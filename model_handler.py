import logging
import os
import torch
import gc
from typing import Optional, Dict, Any
import yaml
import openai
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

try:
    from vllm import LLM
except ImportError:
    LLM = None

logger = logging.getLogger('ModelHandler')

class ModelHandler:
    def __init__(self, model_type: str = "ollama", model_cache_dir: Optional[str] = None):
        self.config = self._load_config()
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

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        try:
            if not os.path.exists(config_path):
                logger.error(f"配置文件 {config_path} 不存在")
                raise FileNotFoundError(f"配置文件 {config_path} 不存在")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not config:
                    logger.error("配置文件内容为空")
                    raise ValueError("配置文件内容为空")
                
                required_sections = ['ollama', 'paths', 'settings']
                for section in required_sections:
                    if section not in config:
                        raise ValueError(f"配置文件中缺少必需部分: {section}")
                
                return config
        except yaml.YAMLError as e:
            logger.error(f"配置文件解析错误: {str(e)}")
            raise ValueError(f"配置文件解析错误: {str(e)}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def _get_device(self):
        try:
            if torch.cuda.is_available():
                current_device = torch.cuda.current_device()
                device_name = torch.cuda.get_device_name(current_device)
                logger.info(f"检测到CUDA设备[{current_device}]: {device_name}")
                torch.zeros(1).cuda()  # 测试CUDA是否工作
                return torch.device("cuda")
            else:
                logger.warning("CUDA不可用，将使用CPU模式")
                return torch.device("cpu")
        except Exception as e:
            logger.error(f"CUDA初始化失败: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return torch.device("cpu")

    def _setup_memory_management(self):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            if hasattr(torch.cuda, 'memory_reserved'):
                torch.cuda.memory_reserved()

    def initialize_model(self, model_type: str):
        if model_type in self._model_cache:
            logger.info("使用缓存模型")
            return self._model_cache[model_type]
            
        model_name = self.config['ollama'].get("hf_model")
        
        try:
            if model_type == "tf":
                self._init_transformer_model(model_name)
            elif model_type == "vllm":
                if LLM is None:
                    raise ImportError("vLLM模块未正确安装")
                self._init_vllm_model(model_name)
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
            "device_map": "auto" if torch.cuda.is_available() else "cpu",
            "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
            "low_cpu_mem_usage": True
        }
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, **device_config)
        self._model_cache["tf"] = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=self.device
        )

    def _init_vllm_model(self, model_name: str):
        self._model_cache["vllm"] = LLM(
            model=model_name,
            tensor_parallel_size=torch.cuda.device_count() if torch.cuda.is_available() else 1,
            dtype="float16" if torch.cuda.is_available() else "float32"
        )

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
        elif model_type == "vllm":
            return self._vllm_generate(prompt, temperature)
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

    def _vllm_generate(self, prompt: str, temperature: Optional[float]) -> str:
        try:
            outputs = self._model_cache["vllm"].generate(
                prompts=[prompt],
                temperature=temperature or self.generation_config['temperature'],
                top_p=self.generation_config['top_p'],
                max_tokens=self.generation_config['max_new_tokens']
            )
            return outputs[0].outputs[0].text
        except Exception as e:
            logger.error(f"VLLM模型生成失败: {str(e)}")
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
