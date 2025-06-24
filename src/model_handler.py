import logging
import os
import torch
import gc
import json
from typing import Optional, Dict, Any
import yaml
import openai
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import accelerate
import bitsandbytes as bnb
from utils import load_config



logger = logging.getLogger('ModelHandler')

class ModelHandler:
    def __init__(self, model_type: str = "ollama", model_cache_dir: Optional[str] = None):
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

    def _setup_memory_management(self):
        """优化内存管理设置"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            # 设置固定内存大小以减少内存碎片
            torch.backends.cudnn.benchmark = True
            if hasattr(torch.cuda, 'memory_reserved'):
                torch.cuda.memory_reserved()

    def _get_device(self):
        """统一设备检测与内存管理设置"""
        try:
            if not torch.cuda.is_available():
                return torch.device("cpu")
        
            # 统一检测流程
            torch.cuda.init()
            device = torch.device("cuda")
            
            # 显存检查与内存管理
            if torch.cuda.mem_get_info(device)[0] < 1024**3:  # 1GB
                logger.warning("可用显存不足，自动回退CPU模式")
                return torch.device("cpu")
            
            # 测试设备可用性并设置内存优化
            torch.zeros(1).to(device)
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            
            logger.info(f"使用CUDA设备: {torch.cuda.get_device_name(device)}")
            return device
        
        except Exception as e:
            logger.error(f"CUDA初始化异常: {str(e)}")
            torch.cuda.empty_cache()
            return torch.device("cpu")

    def _find_model_subdir(self, base_path: str) -> Optional[str]:
        """智能查找模型子目录"""
        # 定义必要文件列表
        required_files = ["config.json", "tokenizer_config.json"]
        
        # 检查模型目录是否存在
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"模型目录不存在: {base_path}")
            
        # 检查safetensors或pytorch_model.bin文件
        safetensors_files = []
        if os.path.exists(base_path):
            safetensors_files = [f for f in os.listdir(base_path) if f.startswith('model-') and f.endswith('.safetensors')]
            
        # 修复未定义model_dir问题
        if not safetensors_files and not os.path.exists(os.path.join(base_path, "pytorch_model.bin")):
            raise FileNotFoundError(f"模型目录缺少必要文件: 未找到pytorch_model.bin或safetensors文件")
        
        # 1. 检查当前目录是否包含所有必要文件
        if all(os.path.exists(os.path.join(base_path, f)) for f in required_files):
            return base_path
            
        # 2. 检查配置中指定的模型子目录
        model_name = self.config['ollama'].get("hf_model")
        if model_name:
            subdir = os.path.join(base_path, model_name)
            if os.path.isdir(subdir):
                if all(os.path.exists(os.path.join(subdir, f)) for f in required_files):
                    return subdir
                logger.debug(f"模型子目录存在但缺少必要文件: {subdir}")
                
        # 3. 检查常见模型子目录结构
        common_subdirs = ["model", "models", "checkpoint", "checkpoints"]
        for subdir in common_subdirs:
            candidate = os.path.join(base_path, subdir)
            if os.path.isdir(candidate):
                if all(os.path.exists(os.path.join(candidate, f)) for f in required_files):
                    return candidate
                logger.debug(f"常见子目录存在但缺少必要文件: {candidate}")
                
        # 4. 遍历所有子目录查找
        for root, dirs, files in os.walk(base_path):
            if all(f in files for f in required_files):
                return root
                
        # 5. 尝试查找部分文件匹配的情况
        for root, dirs, files in os.walk(base_path):
            if "config.json" in files and "pytorch_model.bin" in files:
                logger.warning(f"找到部分匹配的模型目录: {root}, 缺少tokenizer_config.json")
                return root
                
        logger.debug(f"未找到有效的模型目录结构，检查路径: {base_path}")
        return None

    def _load_model_from_path(self, model_path: str):
        """智能加载模型文件或目录"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}")

        if os.path.isdir(model_path):
            found_path = self._find_model_subdir(model_path)
            if found_path:
                return self._load_model_from_dir(found_path)
            raise ValueError(f"模型目录缺少必要文件: {model_path}")

        if model_path.endswith('.pth'):
            return self._handle_pth_file(model_path)
                
        raise ValueError(f"不支持的模型文件格式: {model_path}")
            
    def _load_model_from_dir(self, model_dir: str):
        """从目录加载模型"""
        # 按照PEP8规范，避免重复检查目录是否存在
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"模型目录不存在: {model_dir}")
        
        # 定义必要文件列表
        required_files = ["config.json", "tokenizer_config.json"]
        
        # 检查safetensors或pytorch_model.bin文件
        safetensors_files = [f for f in os.listdir(model_dir) if f.startswith('model-') and f.endswith('.safetensors')] if os.path.exists(model_dir) else []
        
        if not safetensors_files and not os.path.exists(os.path.join(model_dir, "pytorch_model.bin")):
            raise FileNotFoundError(f"模型目录缺少必要文件: 未找到pytorch_model.bin或safetensors文件")
        
        # 查找有效的模型目录
        found_path = self._find_model_subdir(model_dir)
        if not found_path:
            # 获取更详细的错误信息
            dir_contents = []
            for root, dirs, files in os.walk(model_dir):
                dir_contents.extend(f"{root}/{f}" for f in files)
            
            missing_files = [f for f in required_files if not os.path.exists(os.path.join(model_dir, f))]
            logger.error(f"模型目录结构检查失败，路径: {model_dir}, 缺少文件: {missing_files}")
            logger.debug(f"目录内容: {dir_contents}")
            
            # 检查是否有部分匹配的文件
            partial_matches = []
            for root, dirs, files in os.walk(model_dir):
                found_files = [f for f in required_files if f in files]
                if found_files:
                    partial_matches.append({
                        "path": root,
                        "files": found_files,
                        "missing": [f for f in required_files if f not in files]
                    })
            
            if partial_matches:
                logger.warning(f"找到部分匹配的模型目录: {[m['path'] for m in partial_matches]}")
            
            raise FileNotFoundError(
                f"模型目录缺少必要文件: {missing_files}\n"
                f"请确保模型目录包含以下文件: {required_files}\n"
                f"部分匹配的目录: {[m['path'] for m in partial_matches] if partial_matches else '无'}"
            )
        
        logger.info(f"加载模型目录: {model_dir}")
        
        # 设备配置
        device_config = {
            "device_map": "cuda" if torch.cuda.is_available() else "cpu",
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True
        }
        
        try:
            # 加载tokenizer，优先尝试从目录加载
            tokenizer_path = os.path.join(model_dir, "tokenizer_config.json")
            if os.path.exists(tokenizer_path):
                tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=self.config['ollama'].get('trust_remote_code', False))
            else:
                logger.warning(f"tokenizer_config.json不存在，尝试使用默认tokenizer")
                tokenizer = AutoTokenizer.from_pretrained(
                    self.config['ollama'].get("hf_model"), 
                    trust_remote_code=self.config['ollama'].get('trust_remote_code', False)
                )
            
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                model_dir,
                **device_config,
                trust_remote_code=self.config['ollama'].get('trust_remote_code', False)
            )
            
            return pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer
            )
        except Exception as e:
            logger.error(f"从目录加载模型失败: {str(e)}")
            logger.debug(f"模型目录内容: {os.listdir(model_dir)}")
            if torch.cuda.is_available():
                logger.debug(f"当前显存占用: {torch.cuda.memory_allocated()/1024**2:.2f}MB")
            raise
        
    def initialize_model(self, model_type: str):
        if model_type in self._model_cache:
            logger.info("使用缓存模型")
            return self._model_cache[model_type]
            
        model_name = self.config['ollama'].get("hf_model")
        
        # 优先检查本地模型路径
        local_model_name = model_name.replace('/', '_')
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        model_path = os.path.join(models_dir, local_model_name)
        
        # 设置models为默认缓存目录
        if not self.model_cache_dir:
            self.model_cache_dir = models_dir
            
        if os.path.exists(model_path):
            try:
                logger.info(f"尝试从本地路径加载模型: {model_path}")
                self._model_cache["tf"] = self._load_model_from_path(model_path)
                logger.info(f"成功从本地路径加载模型: {model_path}")
                return self._model_cache[model_type]
            except Exception as e:
                logger.error(f"从本地路径加载模型失败: {str(e)}")
                logger.debug(f"模型路径内容: {os.listdir(model_path)}")
                if hasattr(e, 'args') and len(e.args) > 0:
                    logger.debug(f"详细错误信息: {e.args[0]}")
        
        try:
            if model_type == "tf":
                self._init_transformer_model(model_name)
            
            elif model_type == "ollama":
                self._init_ollama_model()
            elif model_type == "openai" and "openai" in self.config:
                self._init_openai_model()
                
            if self.model_cache_dir:
                self._cache_model(model_type)
                
        except Exception as e:
            logger.error(f"模型{model_type}初始化失败: {e}")
            if torch.cuda.is_available():
                logger.debug(f"CUDA设备信息: {torch.cuda.get_device_properties(0)}")
                logger.debug(f"当前显存占用: {torch.cuda.memory_allocated()/1024**2:.2f}MB")
                logger.debug(f"PyTorch编译版本: {torch.version.cuda}")
            self._cleanup_on_error()
            raise

    def _init_transformer_model(self, model_name: str):
        device_config = {
            "device_map": "auto",
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True
        }
        
        try:
            # 简化模型加载逻辑
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name, **device_config)
            
            self._model_cache["tf"] = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer
            )
        except Exception as e:
            logger.error(f"加载模型{model_name}失败: {str(e)}")
            if "safetensors" in str(e):
                logger.warning("尝试从本地缓存加载模型")
                local_model_name = model_name.replace('/', '_')
                models_dir = os.path.join(os.path.dirname(__file__), "models")
                model_path = os.path.join(models_dir, local_model_name)
                if os.path.exists(model_path):
                    return self._load_model_from_path(model_path)
            raise

    

    def _init_ollama_model(self):
        self._model_cache["ollama"] = {
            "endpoint": self.config['ollama']['endpoint'],
            "model": self.config['ollama']['model']
        }

    def _init_openai_model(self):
        openai.api_key = self.config['openai']['api_key']
        self._model_cache["openai"] = {
            "api_key": openai.api_key,
            "model": self.config['openai']['model']
        }

    def _cache_model(self, model_type: str):
        if not self.model_cache_dir:
            return
            
        cache_path = os.path.join(self.model_cache_dir, f"{model_type}_model.pt")
        try:
            if model_type == "tf":
                torch.save(self._model_cache["tf"].state_dict(), cache_path)
            elif model_type == "vllm":
                logger.warning("VLLM模型不支持缓存")
            logger.info(f"模型已缓存: {cache_path}")
        except Exception as e:
            logger.warning(f"模型缓存失败: {e}")

    def _cleanup_on_error(self):
        torch.cuda.empty_cache()
        gc.collect()
        for model in self._model_cache.values():
            if hasattr(model, "state_dict"):
                del model

    def generate_text(self, prompt: str, model_type: str, temperature: Optional[float] = None) -> str:
        if model_type not in self._model_cache:
            self.initialize_model(model_type)
            
        if model_type == "ollama":
            return self._ollama_generate(prompt, temperature)
        elif model_type == "tf":
            return self._transformer_generate(prompt, temperature)
        
        elif model_type == "openai":
            return self._openai_generate(prompt, temperature)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")

    def _ollama_generate(self, prompt: str, temperature: Optional[float]) -> str:
        payload = {
            "model": self._model_cache["ollama"]["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.generation_config['temperature'],
                "top_p": self.generation_config['top_p']
            }
        }
        
        try:
            response = self.session.post(
                self._model_cache["ollama"]["endpoint"],
                json=payload,
                timeout=self.config['settings']['timeout']
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

    def _transformer_generate(self, prompt: str, temperature: Optional[float]) -> str:
        try:
            response = self._model_cache["tf"](prompt,
                max_new_tokens=self.generation_config['max_new_tokens'],
                temperature=temperature or self.generation_config['temperature'],
                top_p=self.generation_config['top_p'],
                do_sample=self.generation_config['do_sample'],
                repetition_penalty=self.generation_config['repetition_penalty'],
                num_return_sequences=self.generation_config['num_return_sequences'],
                early_stopping=self.generation_config['early_stopping'],
                no_repeat_ngram_size=self.generation_config['no_repeat_ngram_size']
            )
            return response[0]['generated_text']
        except Exception as e:
            logger.error(f"Transformer模型生成失败: {str(e)}")
            raise

    

    def _openai_generate(self, prompt: str, temperature: Optional[float]) -> str:
        try:
            response = openai.Completion.create(
                engine=self._model_cache["openai"]["model"],
                prompt=prompt,
                temperature=temperature or self.generation_config['temperature'],
                max_tokens=self.generation_config['max_new_tokens']
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise

        # 在novel_generator.py中修复字符串拼接错误
        if isinstance(prompt, BatchEncoding):
            prompt = self._model_cache[model_type].tokenizer.decode(prompt['input_ids'][0], skip_special_tokens=True)
        prompt = str(prompt)
