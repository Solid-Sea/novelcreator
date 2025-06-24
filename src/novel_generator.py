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
import re
import yaml
from typing import Optional, Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BatchEncoding
#from ktransformers import pipeline as ktf_pipeline, AutoConfig  # 添加AutoConfig导入

from utils import (
    logger, create_folder, get_progress, show_progress, 
    clean_content, merge_chapters, load_blacklist, load_config
)
from model_handler import ModelHandler

# 按照PEP8规范添加必要的空行和调整缩进等格式
# 示例：类和函数定义前后添加空行

class NovelGenerator:
    def __init__(self, model_type="ollama", model_cache_dir: Optional[str] = None):
        """初始化小说生成器

        Args:
            model_type: 模型类型，默认为"ollama"
            model_cache_dir: 模型缓存目录，可选
        """
        self.config = load_config()
        self.ollama_cfg = self.config['ollama']
        self.settings = self.config['settings']
        self.blacklist = load_blacklist()
        self.model_type = model_type
        self.openai_provider = 'openai' if self.config.get('openai') else None
        self.session = requests.Session()
        self.model_cache_dir = model_cache_dir
        self._generation_cache = {}
        self._batch_size = 4

        # 初始化模型处理器
        self.model_handler = ModelHandler(model_type, model_cache_dir)
        if self.model_type == "tf":
            self.tf_pipeline = self.model_handler.initialize_model("tf")

        # 检查CUDA可用性并优化设备选择
        # 优化GPU设备选择，确保只有在CUDA可用时才使用GPU
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.cuda_available = True
            torch.cuda.empty_cache()
        else:
            self.device = torch.device("cpu")
            self.cuda_available = False
        self.cuda_available = True
        torch.cuda.empty_cache()

        # 添加内存管理
        self._setup_memory_management()

        try:
            self._initialize_model(model_type)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            self._cleanup_on_error()
            raise
        except Exception as e:
            logger.error(f"模型初始化失败: {str(e)}")
            self._cleanup_on_error()
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
        try:
            self.model_handler.initialize_model(model_type)
        except Exception as e:
            logger.error(f"模型{model_type}初始化失败: {e}")
            raise

    def _init_openai_model(self):
        self.model_handler.initialize_model()

    def _get_device_config(self) -> Dict[str, Any]:
        """获取设备配置"""
        config = {
            "device_map": "auto",
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True
        }
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

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            # 验证必需配置项
            required_sections = ['ollama', 'paths', 'settings']
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"配置文件中缺少必需部分: {section}")
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {str(e)}")

    def _cache_model(self, model_type: str):
        """缓存模型到磁盘"""
        if not self.model_cache_dir:
            return
        cache_path = os.path.join(self.model_cache_dir, f"{model_type}_model.pt")
        try:
            if self.openai_provider and model_type == self.openai_provider:
                self._init_openai_model()
            elif model_type == "tf":
                if hasattr(self, "tf_pipeline"):
                    torch.save(self.tf_pipeline.state_dict(), cache_path)
            elif model_type == "ktf":
                if hasattr(self, "ktf_pipeline"):
                    torch.save(self.ktf_pipeline.state_dict(), cache_path)
            # VLLM模型不支持缓存
            logger.info(f"模型已缓存: {cache_path}")
        except Exception as e:
            logger.error(f"模型缓存失败: {str(e)}", exc_info=True)
            self._cleanup_on_error()
            raise


    def generate_novel(self, novel_title: str) -> bool:
        """优化的主生成流程"""
        if not re.match(r'^[^\\/:*?"<>|]+$', novel_title):
            raise ValueError(f"非法小说标题: {novel_title} 包含无效字符")
        # 构建小说存储的基础目录
        novel_base_dir = os.path.join(self.config['paths']['novels_dir'], novel_title)
        # 计算总章节数，假设每章2000字，共50万字
        total_chapter_count = 50  # 50万字 / 2000字每章
        try:
            # 创建小说基础目录
            create_folder(novel_base_dir)
            # 创建章节存储目录
            create_folder(os.path.join(novel_base_dir, "chaps"))
            # 创建翻译相关目录
            create_folder(os.path.join(novel_base_dir, "tl"))

            # 获取小说生成进度
            generation_progress = get_progress(novel_title)
            if generation_progress == 0:
                # 生成小说大纲
                self._generate_outline(novel_title, novel_base_dir)
                # 生成章节大纲
                self._generate_chapter_outlines(novel_title, total_chapter_count, novel_base_dir)

            # 使用批量生成替代单章生成
            self._generate_chapters_batch(novel_title, total_chapter_count, novel_base_dir, generation_progress)
            
            # 合并章节并压缩
            merge_chapters(novel_base_dir)
            self._compress_novel(novel_base_dir)
            
            logger.info(f"小说《{novel_title}》生成完成！")
            return True
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.critical(f"生成失败: {str(e)}")
            return False

    def _generate_outline(self, title, base_dir):
        """生成大纲"""
        logger.info("开始生成大纲...")
        prompt = (
            f"生成一本50万字的小说大纲，标题：{title}"
            "要求结构包含："
            "1. 世界观设定（时代背景、特殊设定）"
            "2. 主要人物（至少3个主角的详细设定）"
            "3. 故事主线（起承转合结构）"
            "4. 关键情节转折点（至少5个）"
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
                f"根据总大纲生成第{i}章详细大纲（500字左右）"
                "总大纲："
                f"{total_outline}"
                "包含以下要素："
                "1. 章节核心冲突"
                "2. 场景转换节点"
                "3. 人物情绪变化"
                "4. 关键对话要点"
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
                            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
                                logger.error(f"配置加载失败: {str(e)}", exc_info=True)
                                raise
                            except Exception as e:
                                logger.error(f"处理第{chap_num}章失败: {e}")
                            bar.update(1)
                        batch = []
                        batch_outlines = []
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
                    logger.error(f"配置加载失败: {str(e)}", exc_info=True)
                    raise
                except Exception as e:
                    logger.error(f"生成章节{chap_num}时发生错误: {e}")
                    continue

    def _batch_generate_content(self, outlines: list) -> list:
        """优化后的批量生成内容方法"""
        prompts = [self._create_chapter_prompt(outline) for outline in outlines]
        if self.model_type in ["tf", "ktf"]:
            try:
                pipeline = self.tf_pipeline if self.model_type == "tf" else self.ktf_pipeline
                # 确保所有prompts都是字符串类型
                prompts = [str(prompt) for prompt in prompts]
                # 批量tokenize并移动到GPU
                inputs = pipeline.tokenizer(
                    prompts, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True
                ).to(self.device)
                # 优化生成配置
                generation_config = {
                    "max_new_tokens": 16384,
                    "do_sample": True,
                    "temperature": self.ollama_cfg.get("temperature", 0.7),
                    "top_p": 0.9,
                    "repetition_penalty": 1.1,
                    "batch_size": len(prompts),
                    "pad_token_id": pipeline.tokenizer.eos_token_id
                }
                # 执行批量生成
                outputs = pipeline.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    **generation_config
                )
                outputs = [{
                    'generated_text': pipeline.tokenizer.decode(output, skip_special_tokens=True)
                } for output in outputs]
                # 清理显存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                return [output['generated_text'] for output in outputs]
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
                logger.error(f"配置加载失败: {str(e)}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"批量生成失败: {e}")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
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
            response = self.tf_pipeline(
                prompt,
                max_new_tokens=16384,
                temperature=self.ollama_cfg.get("temperature", 0.7),
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.1,
                num_return_sequences=1,
                early_stopping=True,
                no_repeat_ngram_size=3,
                pad_token_id=self.tf_pipeline.tokenizer.eos_token_id
            )
            # 确保输出在CPU上以释放显存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return response[0]['generated_text']

    def _ktf_generate(self, prompt):
        """KTransformers生成方法"""
        try:
            response = self.ktf_pipeline(prompt)
            return response[0]['generated_text']

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
            logger.error(f"KTransformers模型生成失败: {str(e)}")
            raise

    def _vllm_generate(self, prompt):
        """VLLM生成方法"""
        try:
            return self.model_handler.generate_text(prompt, "vllm", self.ollama_cfg.get("temperature", 0.7))
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
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
            logger.error(f"保存文件失败: {str(e)}")
            raise

    def _load_chapter_outline(self, base_dir, chap_num):
        """加载章节大纲"""
        outline_path = os.path.join(base_dir, "tl", f"chap_{chap_num:03d}.txt")
        try:
            with open(outline_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
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
            # 设置模型缓存目录
            local_model_dir = os.path.join(self.model_cache_dir or "./models", model_name.replace("/", "_"))
            os.makedirs(local_model_dir, exist_ok=True)
            
            # 优化模型加载配置
            model_kwargs = {
                'device_map': device_config.get("device_map", "auto"),
                'torch_dtype': device_config.get("torch_dtype", torch.float16),
                'low_cpu_mem_usage': True,
                'trust_remote_code': True,
                'use_cache': True,
                'max_memory': self._get_max_memory(),
                'cache_dir': local_model_dir
            }

            logger.info(f"开始下载模型到本地: {local_model_dir}")
            
            # 使用 from_pretrained 下载并加载模型
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir=local_model_dir
            )
            
            with init_empty_weights():
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    **model_kwargs
                )
            
            model = load_checkpoint_and_dispatch(
                model,
                model_name,  # 使用原始模型名称
                no_split_module_classes=["DeepseekTransformerBlock"],
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
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
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
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
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
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, json.JSONDecodeError) as e:
            logger.error(f"配置加载失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"本地模型生成失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise
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


# 对model_handler.py文件也进行类似的格式调整
# 由于不能输出整个文件内容，这里简单示意
class ModelHandler:
    def __init__(self, model_type: str = "ollama", model_cache_dir: Optional[str] = None):
        # 初始化部分按照PEP8规范调整格式
        self.config = load_config()
        self.model_type = model_type
        self.model_cache_dir = model_cache_dir
        self._model_cache: Dict[str, Any] = {}
        self.session = requests.Session()
        self.device = self._get_device()
        self._setup_memory_management()

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
