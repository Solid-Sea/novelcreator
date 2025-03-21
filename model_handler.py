import logging
import os
from typing import Optional
import yaml
import openai

logger = logging.getLogger('ModelHandler')

class ModelHandler:
    def __init__(self):
        self.config = self._load_config()
        self._validate_model_config()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        try:
            # 使用绝对路径加载配置文件
            if not os.path.exists(config_path):
                logger.error(f"配置文件 {config_path} 不存在")
                raise FileNotFoundError(f"配置文件 {config_path} 不存在")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not config:
                    logger.error("配置文件内容为空")
                    raise ValueError("配置文件内容为空")
                return config
        except yaml.YAMLError as e:
            logger.error(f"配置文件解析错误: {str(e)}")
            raise ValueError(f"配置文件解析错误: {str(e)}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def _validate_model_config(self):
        # 定义模型配置所需的必要参数
        required_keys = ['model_name', 'base_url', 'temperature', 'max_tokens']
        for key in required_keys:
            if key not in self.config.get('model', {}):
                # 若配置文件中缺少必要参数，抛出异常
                raise ValueError(f"配置文件中缺少必要参数: {key}")

    def initialize_model(self):
        # 获取模型配置信息
        model_config = self.config['model']
        # 记录正在初始化模型的信息
        logger.info(f"正在初始化模型: {model_config['model_name']}")
        # 这里可以添加实际的模型初始化代码
        if model_config.get('provider') == 'openai':
            openai.api_key = self.config['openai']['api_key']
            return {
                'status': 'success',
                'model_name': model_config['model_name'],
                'provider': 'openai'
            }
        return {
            'status': 'success',
            'model_name': model_config['model_name'],
            'base_url': model_config['base_url']
        }

    def generate_text(self, prompt: str, temperature: Optional[float] = None) -> str:
        # 获取模型配置信息
        model_config = self.config['model']
        # 设置文本生成的参数
        params = {
            'temperature': temperature or model_config['temperature'],
            'max_tokens': model_config['max_tokens']
        }
        if not isinstance(prompt, str) or len(prompt.strip()) == 0:
            logger.error("无效的prompt输入: 必须是非空字符串")
            raise ValueError("prompt不能为空")
        logger.debug("正在生成文本，参数: %s", params)
        # 这里可以添加实际的模型调用代码
        if model_config.get('provider') == 'openai':
            response = openai.Completion.create(
                engine=model_config['model'],
                prompt=prompt,
                temperature=params['temperature'],
                max_tokens=params['max_tokens']
            )
            return response.choices[0].text.strip()
        return f"Generated text for: {prompt}"