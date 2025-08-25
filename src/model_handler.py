# -*- coding: utf-8 -*-
# File: model_handler.py
import logging
import os
import torch
import gc
from typing import Optional, Dict, Any
import openai
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from .utils import load_config

logger = logging.getLogger('ModelHandler')

class ModelHandler:
    def __init__(self, model_type: str = None, model_cache_dir: Optional[str] = None):
        self.config = load_config()
        # 如果没有指定模型类型，则从配置中获取默认模型类型
        self.model_type = model_type if model_type is not None else self._get_default_model_type()
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

    def _get_default_model_type(self) -> str:
        """从配置中获取默认模型类型"""
        model_selection = self.config.get('model_selection', {})
        default_type = model_selection.get('default_type', 'ollama')
        
        # 验证模型类型
        if default_type not in ['ollama', 'openai']:
            logger.warning(f"无效的模型类型: {default_type}，使用默认值 'ollama'")
            return 'ollama'
        
        logger.info(f"使用默认模型类型: {default_type}")
        return default_type

    def _setup_memory_management(self):
        """优化内存管理设置"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True

    def _get_device(self):
        """统一设备检测与内存管理设置"""
        try:
            if not torch.cuda.is_available():
                return torch.device("cpu")
        
            torch.cuda.init()
            device = torch.device("cuda")
            
            if torch.cuda.mem_get_info(device)[0] < 1024**3:  # 1GB
                logger.warning("可用显存不足，自动回退CPU模式")
                return torch.device("cpu")
            
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
        required_files = ["config.json", "tokenizer_config.json"]
        
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"模型目录不存在: {base_path}")
            
        safetensors_files = []
        if os.path.exists(base_path):
            safetensors_files = [f for f in os.listdir(base_path) if f.startswith('model-') and f.endswith('.safetensors')]
            
        if not safetensors_files and not os.path.exists(os.path.join(base_path, "pytorch_model.bin")):
            raise FileNotFoundError(f"模型目录缺少必要文件: 未找到pytorch_model.bin或safetensors文件")
        
        if all(os.path.exists(os.path.join(base_path, f)) for f in required_files):
            return base_path
            
        model_name = self.config['ollama'].get("hf_model")
        if model_name:
            subdir = os.path.join(base_path, model_name)
            if os.path.isdir(subdir):
                if all(os.path.exists(os.path.join(subdir, f)) for f in required_files):
                    return subdir
                
        common_subdirs = ["model", "models", "checkpoint", "checkpoints"]
        for subdir in common_subdirs:
            candidate = os.path.join(base_path, subdir)
            if os.path.isdir(candidate):
                if all(os.path.exists(os.path.join(candidate, f)) for f in required_files):
                    return candidate
                
        for root, dirs, files in os.walk(base_path):
            if all(f in files for f in required_files):
                return root
                
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
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"模型目录不存在: {model_dir}")
        
        required_files = ["config.json", "tokenizer_config.json"]
        
        safetensors_files = [f for f in os.listdir(model_dir) if f.startswith('model-') and f.endswith('.safetensors')] if os.path.exists(model_dir) else []
        
        if not safetensors_files and not os.path.exists(os.path.join(model_dir, "pytorch_model.bin")):
            raise FileNotFoundError(f"模型目录缺少必要文件: 未找到pytorch_model.bin或safetensors文件")
        
        found_path = self._find_model_subdir(model_dir)
        if not found_path:
            dir_contents = []
            for root, dirs, files in os.walk(model_dir):
                dir_contents.extend(f"{root}/{f}" for f in files)
            
            missing_files = [f for f in required_files if not os.path.exists(os.path.join(model_dir, f))]
            logger.error(f"模型目录结构检查失败，路径: {model_dir}, 缺少文件: {missing_files}")
            logger.debug(f"目录内容: {dir_contents}")
            
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
        
        device_config = {
            "device_map": "cuda" if torch.cuda.is_available() else "cpu",
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True
        }
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=self.config['ollama'].get('trust_remote_code', False))
            model = AutoModelForCausalLM.from_pretrained(model_dir, **device_config, trust_remote_code=self.config['ollama'].get('trust_remote_code', False))
            
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
        
        local_model_name = model_name.replace('/', '_')
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        model_path = os.path.join(models_dir, local_model_name)
        
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
        openai.base_url = self.config['openai'].get('base_url', 'https://api.openai.com/v1')
        self._model_cache["openai"] = {
            "api_key": openai.api_key,
            "base_url": openai.base_url,
            "model": self.config['openai']['model'],
            "models": self.config['openai'].get('models', {})
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

    def generate_text(self, prompt: str, model_type: str = None, temperature: Optional[float] = None, task_type: str = None) -> str:
        if model_type is None:
            model_type = self.model_type
            
        if model_type not in self._model_cache:
            self.initialize_model(model_type)
            
        if model_type == "ollama":
            return self._ollama_generate(prompt, temperature)
        elif model_type == "tf":
            return self._transformer_generate(prompt, temperature)
        elif model_type == "openai":
            return self._openai_generate(prompt, temperature, task_type)
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
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                endpoint = self._model_cache["ollama"]["endpoint"]
                # 确保端点URL格式正确
                if not endpoint.startswith('http'):
                    endpoint = f"http://{endpoint}"
                if not endpoint.endswith('/api/generate'):
                    endpoint = f"{endpoint.rstrip('/')}/api/generate"
                    
                logger.debug(f"Ollama API请求: {endpoint}")
                logger.debug(f"请求载荷: {payload}")
                    
                response = self.session.post(
                    endpoint,
                    json=payload,
                    timeout=self.config['settings']['timeout']
                )
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Ollama API响应: {data}")
                
                if "response" in data:
                    return data["response"]
                elif "text" in data:
                    return data["text"]
                else:
                    raise ValueError("无效的API响应格式")
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"API请求失败，{retry_delay}秒后重试({attempt+1}/{max_retries}): {str(e)}")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"API请求最终失败: {str(e)}")
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

    def _openai_generate(self, prompt: str, temperature: Optional[float], task_type: str = None) -> str:
        try:
            from openai import OpenAI
            
            # 使用新的OpenAI客户端
            client = OpenAI(
                api_key=self._model_cache["openai"]["api_key"],
                base_url=self._model_cache["openai"]["base_url"]
            )
            
            # 根据任务类型选择模型
            model_name = self._model_cache["openai"]["model"]  # 默认模型
            if task_type and "models" in self._model_cache["openai"]:
                task_models = self._model_cache["openai"]["models"]
                if task_type in task_models and task_models[task_type]:
                    model_name = task_models[task_type]
                    logger.info(f"使用任务特定模型: {task_type} -> {model_name}")
            
            # 使用ChatCompletion API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature or self.generation_config['temperature'],
                max_tokens=self.generation_config['max_new_tokens'],
                timeout=self.config['settings']['timeout']
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise

    def generate_text_with_model(self, prompt: str, task_type: str, model_type: str = None, temperature: Optional[float] = None) -> str:
        """使用特定任务模型生成文本"""
        if model_type is None:
            model_type = self.model_type
            
        if model_type not in self._model_cache:
            self.initialize_model(model_type)
            
        if model_type == "ollama":
            return self._ollama_generate(prompt, temperature)
        elif model_type == "tf":
            return self._transformer_generate(prompt, temperature)
        elif model_type == "openai":
            return self._openai_generate(prompt, temperature, task_type)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
