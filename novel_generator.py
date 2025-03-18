# -*- coding: utf-8 -*-
# File: novel_generator.py
import os
import json
import time
import requests
import argparse
import shutil
import torch
import gc
from typing import Optional, Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
#from ktransformers import pipeline as ktf_pipeline, AutoConfig  # 添加AutoConfig导入

# 修改vLLM导入
try:
    from vllm import LLM
except ImportError:
    try:
        from vllm.engine.llm_engine import LLM
    except ImportError:
        logger.warning("vLLM导入失败，vllm模式将不可用")
        LLM = None

from utils import (
    logger, create_folder, get_progress, show_progress, 
    clean_content, merge_chapters, load_blacklist
)
from accelerate import init_empty_weights, load_checkpoint_and_dispatch

class NovelGenerator:
    def __init__(self, model_type="ollama", model_cache_dir: Optional[str] = None):
        self.config = self._load_config()
        self.ollama_cfg = self.config['ollama']
        self.settings = self.config['settings']
        self.blacklist = load_blacklist()
        self.model_type = model_type
        self.session = requests.Session()
        self.model_cache_dir = model_cache_dir
        self._model_cache: Dict[str, Any] = {}
        self._generation_cache = {}  # 添加生成结果缓存
        self._batch_size = 4  # 批处理大小
        
        # 优化配置
        self.generation_config = {
            'max_new_tokens': 8192,
            'temperature': 0.7,
            'top_p': 0.9,
            'do_sample': True,
            'repetition_penalty': 1.1,
            'num_return_sequences': 1,
            'early_stopping': True,
            'no_repeat_ngram_size': 3,
            'pad_token_id': 0,
            'eos_token_id': 2,
            'use_cache': True
        }
        
        # 检查CUDA可用性
        self.cuda_available = torch.cuda.is_available()
        if not self.cuda_available:
            logger.warning("CUDA不可用，将使用CPU模式")
            
        # 添加内存管理
        self._setup_memory_management()
        
        try:
            self._initialize_model(model_type)
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise

    def _setup_memory_management(self):
        """优化内存管理设置"""
        if self.cuda_available:
            torch.cuda.empty_cache()
            # 设置固定内存大小以减少内存碎片
            torch.backends.cudnn.benchmark = True
            if hasattr(torch.cuda, 'memory_reserved'):
                torch.cuda.memory_reserved()
            
    def _initialize_model(self, model_type: str):
        """统一的模型初始化接口"""
        if model_type in self._model_cache:
            logger.info("使用缓存模型")
            return self._model_cache[model_type]
            
        model_name = self.ollama_cfg.get("hf_model")
        device_config = self._get_device_config()
        
        try:
            if model_type == "tf":
                self._init_transformer_model(model_name, device_config)
            elif model_type == "ktf":
                self._init_ktransformer_model(model_name, device_config)
            elif model_type == "vllm":
                if LLM is None:
                    raise ImportError("vLLM模块未正确安装")
                self._init_vllm_model(model_name, device_config)
                
            # 缓存模型
            if self.model_cache_dir:
                self._cache_model(model_type)
                
        except Exception as e:
            logger.error(f"模型{model_type}初始化失败: {e}")
            self._cleanup_on_error()
            raise

    def _get_device_config(self) -> Dict[str, Any]:
        """获取设备配置"""
        config = {
            "device_map": "cpu",
            "torch_dtype": torch.float32,
        }
        
        if self.cuda_available:
            free_memory = self._get_gpu_memory()
            if free_memory >= 4 * 1024 * 1024 * 1024:  # 4GB
                config.update({
                    "device_map": "balanced" if torch.cuda.device_count() > 1 else "auto",
                    "torch_dtype": torch.float16,
                    "low_cpu_mem_usage": True,
                })
        return config

    def _get_gpu_memory(self) -> int:
        """获取GPU可用内存"""
        if not self.cuda_available:
            return 0
        return min(torch.cuda.get_device_properties(i).total_memory 
                  for i in range(torch.cuda.device_count()))

    def _cleanup_on_error(self):
        """错误时清理资源"""
        torch.cuda.empty_cache()
        gc.collect()
        if hasattr(self, "tf_pipeline"):
            del self.tf_pipeline
        if hasattr(self, "ktf_pipeline"):
            del self.ktf_pipeline
        if hasattr(self, "vllm_model"):
            del self.vllm_model

    def _cache_model(self, model_type: str):
        """缓存模型到磁盘"""
        if not self.model_cache_dir:
            return
            
        cache_path = os.path.join(self.model_cache_dir, f"{model_type}_model.pt")
        try:
            if model_type == "tf":
                torch.save(self.tf_pipeline.state_dict(), cache_path)
            elif model_type == "ktf":
                torch.save(self.ktf_pipeline.state_dict(), cache_path)
            # VLLM模型不支持缓存
            logger.info(f"模型已缓存: {cache_path}")
        except Exception as e:
            logger.warning(f"模型缓存失败: {e}")

    def _load_config(self):
        """加载配置文件"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                import yaml
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def generate_novel(self, title: str) -> bool:
        """优化的主生成流程"""
        base_dir = os.path.join(self.config['paths']['novels_dir'], title)
        total_chaps = 50  # 50万字 / 2000字每章
        
        try:
            create_folder(base_dir)
            create_folder(os.path.join(base_dir, "chaps"))
            create_folder(os.path.join(base_dir, "tl"))

            progress = get_progress(title)
            if progress == 0:
                self._generate_outline(title, base_dir)
                self._generate_chapter_outlines(title, total_chaps, base_dir)

            # 使用批量生成替代单章生成
            self._generate_chapters_batch(title, total_chaps, base_dir, progress)
            
            # 合并章节并压缩
            merge_chapters(base_dir)
            self._compress_novel(base_dir)
            
            logger.info(f"小说《{title}》生成完成！")
            return True
            
        except Exception as e:
            logger.critical(f"生成失败: {str(e)}")
            return False

    def _generate_outline(self, title, base_dir):
        """生成大纲"""
        logger.info("开始生成大纲...")
        prompt = (
            f"生成一本50万字的小说大纲，标题：{title}\n"
            "要求结构包含：\n"
            "1. 世界观设定（时代背景、特殊设定）\n"
            "2. 主要人物（至少3个主角的详细设定）\n"
            "3. 故事主线（起承转合结构）\n"
            "4. 关键情节转折点（至少5个）\n"
            "请用清晰的Markdown格式输出"
        )
        outline = self._safe_api_call(prompt)
        outline_path = os.path.join(base_dir, "outline.txt")
        self._save_text(outline_path, outline)
        logger.info("大纲生成完成")

    def _generate_chapter_outlines(self, title, total_chaps, base_dir):
        """生成章节大纲"""
        logger.info("开始生成章节大纲...")
        outline_path = os.path.join(base_dir, "outline.txt")
        with open(outline_path, 'r', encoding='utf-8') as f:
            total_outline = f.read()
        
        for i in range(1, total_chaps+1):
            prompt = (
                f"根据总大纲生成第{i}章详细大纲（500字左右）\n"
                "总大纲：\n"
                f"{total_outline}\n"
                "包含以下要素：\n"
                "1. 章节核心冲突\n" 
                "2. 场景转换节点\n"
                "3. 人物情绪变化\n"
                "4. 关键对话要点\n"
                "5. 章节结尾悬念"
            )
            chap_outline = self._safe_api_call(prompt)
            outline_path = os.path.join(base_dir, "tl", f"chap_{i:03d}.txt")
            self._save_text(outline_path, chap_outline)
            if i % 10 == 0:
                logger.info(f"已生成{i}章大纲")
        logger.info("章节大纲全部生成完成")

    def _generate_chapters_batch(self, title: str, total_chaps: int, base_dir: str, progress: int):
        """批量生成章节内容"""
        logger.info("开始批量生成章节内容...")
        with show_progress(progress, total_chaps) as bar:
            batch = []
            batch_outlines = []
            
            for chap_num in range(progress + 1, total_chaps + 1):
                try:
                    # 检查缓存
                    cache_key = f"{title}_{chap_num}"
                    if cache_key in self._generation_cache:
                        content = self._generation_cache[cache_key]
                        self._save_chapter_content(base_dir, chap_num, content)
                        bar.update(1)
                        continue
                    
                    outline = self._load_chapter_outline(base_dir, chap_num)
                    batch.append(chap_num)
                    batch_outlines.append(outline)
                    
                    # 达到批处理大小或最后一章时进行生成
                    if len(batch) == self._batch_size or chap_num == total_chaps:
                        contents = self._batch_generate_content(batch_outlines)
                        
                        for idx, (chap_num, content) in enumerate(zip(batch, contents)):
                            try:
                                cleaned_content = clean_content(content, self.blacklist)
                                if len(cleaned_content) >= 1800:
                                    self._generation_cache[f"{title}_{chap_num}"] = cleaned_content
                                    self._save_chapter_content(base_dir, chap_num, cleaned_content)
                                else:
                                    logger.warning(f"第{chap_num}章内容过短，重新生成")
                                    content = self._generate_chapter_content(batch_outlines[idx])
                                    cleaned_content = clean_content(content, self.blacklist)
                                    self._save_chapter_content(base_dir, chap_num, cleaned_content)
                            except Exception as e:
                                logger.error(f"处理第{chap_num}章失败: {e}")
                            bar.update(1)
                            
                        batch = []
                        batch_outlines = []
                        
                except Exception as e:
                    logger.error(f"生成章节{chap_num}时发生错误: {e}")
                    continue

    def _batch_generate_content(self, outlines: list) -> list:
        """批量生成内容"""
        prompts = [self._create_chapter_prompt(outline) for outline in outlines]
        
        if self.model_type in ["tf", "ktf"]:
            try:
                pipeline = self.tf_pipeline if self.model_type == "tf" else self.ktf_pipeline
                outputs = pipeline(
                    prompts,
                    batch_size=len(prompts),
                    **self.generation_config
                )
                return [output['generated_text'] for output in outputs]
            except Exception as e:
                logger.error(f"批量生成失败: {e}")
                # 回退到单个生成
                return [self._safe_api_call(prompt) for prompt in prompts]
        else:
            return [self._safe_api_call(prompt) for prompt in prompts]

    def _create_chapter_prompt(self, outline: str) -> str:
        """创建章节生成提示"""
        return (
            f"根据以下大纲编写2000-2500字的小说章节：\n{outline}\n"
            "要求：\n"
            "1. 使用简体中文书面语\n"
            "2. 保持段落长度适中（3-5行）\n"
            "3. 包含至少3段对话\n"
            "4. 结尾留有悬念\n"
            "5. 避免使用违禁词汇\n"
            "6. 生成物直接面向读者\n"
            "7. 保证段落过渡自然，描写细腻"
        )

    def _safe_api_call(self, prompt):
        """安全的API调用"""
        if self.model_type == "ollama":
            return self._ollama_api_call(prompt)
        elif self.model_type == "tf":
            return self._transformer_generate(prompt)
        elif self.model_type == "ktf":
            return self._ktf_generate(prompt)
        elif self.model_type == "vllm":
            return self._vllm_generate(prompt)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")

    def _ollama_api_call(self, prompt):
        payload = {
            "model": self.ollama_cfg["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.ollama_cfg.get("temperature", 0.7),
                "top_p": 0.9
            }
        }
        
        try:
            # 修改：使用session发送请求，实现连接复用
            response = self.session.post(
                self.ollama_cfg["endpoint"],
                json=payload,
                timeout=self.settings['timeout']
            )
            response.raise_for_status()
            data = response.json()
            
            if "response" in data:
                return data["response"]
            elif "text" in data:
                return data["text"]
            else:
                raise ValueError("无效的API响应格式")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            raise

    def _transformer_generate(self, prompt):
        """优化Transformer生成方法"""
        try:
            response = self.tf_pipeline(
                prompt,
                max_new_tokens=8192,
                temperature=self.ollama_cfg.get("temperature", 0.7),
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.1,  # 添加重复惩罚
                num_return_sequences=1,
                early_stopping=True,     # 启用早停
                no_repeat_ngram_size=3   # 避免重复短语
            )
            return response[0]['generated_text']
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            raise

    def _ktf_generate(self, prompt):
        """KTransformers生成方法"""
        try:
            response = self.ktf_pipeline(prompt)
            return response[0]['generated_text']
        except Exception as e:
            logger.error(f"KTransformers模型生成失败: {str(e)}")
            raise

    def _vllm_generate(self, prompt):
        """VLLM生成方法"""
        try:
            if not hasattr(self, 'vllm_model'):
                raise RuntimeError("vLLM模型未初始化")
            outputs = self.vllm_model.generate(prompts=[prompt],
                                             temperature=self.ollama_cfg.get("temperature", 0.7),
                                             top_p=0.9,
                                             max_tokens=8192)
            return outputs[0].outputs[0].text
        except Exception as e:
            logger.error(f"VLLM模型生成失败: {str(e)}")
            raise

    def _compress_novel(self, base_dir):
        """压缩小说文件夹"""
        output_path = os.path.join(self.config['paths']['novels_dir'], os.path.basename(base_dir))
        shutil.make_archive(
            base_name=output_path,
            format='zip',
            root_dir=base_dir
        )
        logger.info(f"压缩包已生成：{output_path}.zip")

    def _save_text(self, path, content):
        """安全保存文本"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise

    def _load_chapter_outline(self, base_dir, chap_num):
        """加载章节大纲"""
        outline_path = os.path.join(base_dir, "tl", f"chap_{chap_num:03d}.txt")
        try:
            with open(outline_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取大纲失败: {str(e)}")
            raise

    def _generate_chapter_content(self, outline):
        """生成章节内容"""
        prompt = (
            f"根据以下大纲编写2000-2500字的小说章节：\n{outline}\n"
            "要求：\n"
            "1. 使用简体中文书面语\n"
            "2. 保持段落长度适中（3-5行）\n"
            "3. 包含至少3段对话\n"
            "4. 结尾留有悬念\n"
            "5. 避免使用违禁词汇\n"
            "6生成物直接面向读者，请避免出现多余的文字（例如接下来的剧情走向等）\n"
            "8.严格根据大纲生成，保证每一段文字之间过渡自然，描写细腻生动，人物刻画细致入微，不允许出现突兀的转折，分割线等"
        )
        content = self._safe_api_call(prompt)
        if len(content) < 1800:
            raise ValueError("生成内容过短")
        return content

    def _save_chapter_content(self, base_dir, chap_num, content):
        """保存章节内容"""
        chap_path = os.path.join(base_dir, "chaps", f"chap_{chap_num:03d}.txt")
        self._save_text(chap_path, content)

    def _init_transformer_model(self, model_name: str, device_config: Dict[str, Any]):
        """优化的Transformer模型初始化"""
        try:
            # 确保模型下载到本地
            local_model_dir = os.path.join(self.model_cache_dir or "./models", model_name.replace("/", "_"))
            if not os.path.exists(local_model_dir):
                logger.info(f"模型未找到，正在下载到本地: {local_model_dir}")
                from transformers import snapshot_download
                snapshot_download(repo_id=model_name, cache_dir=local_model_dir)
            
            # 检查下载后的路径是否有效
            if not os.path.exists(local_model_dir):
                raise FileNotFoundError(f"模型下载失败或路径无效: {local_model_dir}")

            # 使用本地路径加载模型
            tokenizer = AutoTokenizer.from_pretrained(
                local_model_dir,
                trust_remote_code=True
            )
            
            # 优化模型加载配置
            model_kwargs = {
                'device_map': device_config.get("device_map", "auto"),
                'torch_dtype': device_config.get("torch_dtype", torch.float16),
                'low_cpu_mem_usage': True,
                'trust_remote_code': True,
                'use_cache': True,
                'max_memory': self._get_max_memory()
            }
            
            with init_empty_weights():
                model = AutoModelForCausalLM.from_pretrained(
                    local_model_dir,
                    **model_kwargs
                )
            
            model = load_checkpoint_and_dispatch(
                model,
                local_model_dir,
                no_split_module_classes=["DeepseekTransformerBlock"],  # 适配DeepSeek模型
                **model_kwargs
            )

            # 初始化优化的生成管道
            self.tf_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                batch_size=self._batch_size,
                **self.generation_config
            )
            
            logger.info(f"Transformer模型加载成功: {local_model_dir}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def _get_max_memory(self) -> Dict[str, str]:
        """获取每个设备的最大内存配置"""
        if not self.cuda_available:
            return {"cpu": "24GB"}
            
        max_memory = {}
        for i in range(torch.cuda.device_count()):
            mem = torch.cuda.get_device_properties(i).total_memory
            max_memory[f"cuda:{i}"] = f"{int(mem * 0.9 / 1024**3)}GB"  # 预留10%
        max_memory["cpu"] = "24GB"  # CPU内存限制
        return max_memory

    def _init_ktransformer_model(self, model_name: str, device_config: Dict[str, Any]):
        """初始化KTransformer模型"""
        try:
            from ktransformers import pipeline as ktf_pipeline
            self.ktf_pipeline = ktf_pipeline(
                "text-generation",
                model_name=model_name,
                trust_remote_code=True,
                device=device_config.get("device_map", "cpu")
            )
            logger.info("KTransformer模型加载成功")
        except Exception as e:
            logger.error(f"KTransformer模型加载失败: {e}")
            raise

    def _init_vllm_model(self, model_name: str, device_config: Dict[str, Any]):
        """初始化vLLM模型"""
        try:
            tensor_parallel_size = torch.cuda.device_count() if self.cuda_available else 1
            self.vllm_model = LLM(
                model=model_name,
                tensor_parallel_size=tensor_parallel_size,
                dtype=device_config.get("torch_dtype", "auto"),
                trust_remote_code=True
            )
            logger.info("vLLM模型加载成功")
        except Exception as e:
            logger.error(f"vLLM模型加载失败: {e}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='小说生成器')
    parser.add_argument('--title', type=str, required=True, help='小说标题')
    parser.add_argument('--model', type=str, choices=['ollama', 'tf', 'ktf', 'vllm'], 
                       default='ollama', help='选择使用的模型类型')
    
    args = parser.parse_args()
    
    print(f"小说生成器 v2.0 | 模型类型: {args.model}")
    generator = NovelGenerator(model_type=args.model)
    success = generator.generate_novel(args.title)
    
    if success:
        print("\n生成成功！小说文件保存在 novels/ 目录")
    else:
        completed = get_progress(args.title)
        print(f"\n生成部分完成，共生成{completed}章，请查看日志文件检查失败章节")
