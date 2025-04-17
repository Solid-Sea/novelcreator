# -*- coding: utf-8 -*-
from llama_cpp import Llama
import logging

logger = logging.getLogger('NovelGenerator')

class LlamaCppHandler:
    def __init__(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = -1):
        """
        初始化Llama.cpp模型
        :param model_path: GGUF模型文件路径
        :param n_ctx: 上下文窗口大小
        :param n_gpu_layers: 使用GPU加速的层数（-1表示全部）
        """
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            logits_all=False,
            verbose=False
        )
        logger.info(f"成功加载Llama.cpp模型: {model_path}")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """
        文本生成方法（兼容Ollama接口）
        :param prompt: 输入提示
        :param temperature: 温度参数
        :param max_tokens: 最大生成token数
        :return: 生成的文本内容
        """
        try:
            output = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            if not output or not isinstance(output, dict) or not output.get('choices'):
                raise ValueError("Invalid API response format")
            content: str = str(output['choices'][0]['message']['content'])
            return content
        except Exception as e:
            logger.error(f"Llama.cpp生成失败: {str(e)}")
            raise