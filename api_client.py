# -*- coding: utf-8 -*-
"""
api_client.py — NovelCreator API 客户端

唯一与 LLM API 交互的层。
只做 OpenAI-compatible API 调用，不涉及任何本地模型逻辑。
"""

import json
import logging
import time
from typing import Optional, Dict, Any, List

from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError

logger = logging.getLogger('APIClient')


class APIClient:
    """OpenAI-compatible API 客户端。无状态，不缓存，不预加载。"""

    def __init__(self, config: dict):
        api_cfg = config.get('api', {})
        self.base_url = api_cfg.get('base_url', 'https://api.openai.com/v1')
        self.api_key = api_cfg.get('api_key', '')
        self.timeout = api_cfg.get('timeout', 240)
        self.models = api_cfg.get('models', {})

        self._client: Optional[OpenAI] = None

    # ── 属性 ──────────────────────────────────────────────

    @property
    def client(self) -> OpenAI:
        """延迟初始化 client，不在 __init__ 建立连接。"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=0,  # 我们自己控制重试
            )
        return self._client

    # ── 核心调用 ──────────────────────────────────────────

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8192,
        task_type: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """调用 Chat Completion API，返回回复文本。

        Args:
            messages: OpenAI 格式的消息列表
            temperature: 生成温度
            max_tokens: 最大生成 token 数
            task_type: 任务类型（用于按任务选模型）
            model: 直接指定模型名，优先级高于 task_type

        Returns:
            模型回复文本（strip 后）
        """
        model_name = model or self._resolve_model(task_type)
        last_error = None

        for attempt in range(3):
            try:
                logger.debug(
                    f"API call: model={model_name} "
                    f"temperature={temperature} max_tokens={max_tokens}"
                )
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                return content.strip() if content else ""

            except RateLimitError as e:
                wait = 2 ** attempt * 2  # 2, 4, 8
                logger.warning(
                    f"Rate limited (attempt {attempt+1}/3), "
                    f"retrying in {wait}s: {e}"
                )
                time.sleep(wait)
                last_error = e

            except APITimeoutError as e:
                wait = 2 ** attempt * 3  # 3, 6, 12
                logger.warning(
                    f"Timeout (attempt {attempt+1}/3), "
                    f"retrying in {wait}s: {e}"
                )
                time.sleep(wait)
                last_error = e

            except APIError as e:
                logger.error(f"API error (attempt {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    last_error = e
                else:
                    raise

        raise RuntimeError(
            f"API call failed after 3 retries: {last_error}"
        )

    # ── 工具方法 ──────────────────────────────────────────

    def _resolve_model(self, task_type: Optional[str] = None) -> str:
        """按任务类型解析模型名。"""
        if task_type and task_type in self.models:
            return self.models[task_type]
        return self.models.get('default', 'openrouter/auto')

    def count_tokens(self, text: str) -> int:
        """粗略估算 token 数（中英文混合）。"""
        import re
        # 中文约 1.5 token/字，英文约 1 token/4 字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25) + 4
