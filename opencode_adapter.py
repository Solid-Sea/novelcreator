# -*- coding: utf-8 -*-
"""OpenCode (Go) Runner Adapter — 用 opencode CLI 替代直接 API 调用。

实现与 api_client.APIClient 相同的接口，
但底层走 opencode run，利用它已配置的 provider/credential。
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Optional, Dict, Any, List

logger = logging.getLogger('OpenCodeAPIClient')


class OpenCodeAPIClient:
    """通过 opencode CLI 执行 LLM 调用。

    用法与 APIClient 一致，方便替换。
    """

    def __init__(self, config: dict):
        self.config = config
        api_cfg = config.get('api', {})
        self.timeout = api_cfg.get('timeout', 240)
        self.models = api_cfg.get('models', {})

        # 模型名映射
        self._model_map = {
            ('advanced', 'outline'): 'opencode-go/deepseek-v4-flash',
            ('advanced', 'review'): 'opencode-go/deepseek-v4-flash',
            ('advanced', 'clean'): 'opencode-go/deepseek-v4-flash',
            ('advanced', 'summary'): 'opencode-go/deepseek-v4-flash',
            ('advanced', 'revise'): 'opencode-go/deepseek-v4-flash',
            ('advanced', None): 'opencode-go/deepseek-v4-flash',
            ('basic', 'content'): 'opencode-go/deepseek-v4-flash',
            ('basic', 'expand'): 'opencode-go/deepseek-v4-flash',
            ('basic', None): 'opencode-go/deepseek-v4-flash',
        }

    # ── 公开接口 ──────────────────────────────────────────

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8192,
        task_type: Optional[str] = None,
        model: Optional[str] = None,
        tier: str = 'basic',
    ) -> str:
        """调用 opencode run 执行 LLM 生成。"""
        prompt = self._build_prompt(messages)
        model_name = model or self._resolve_model(task_type, tier)

        # 写 prompt 到临时文件，通过 stdin 重定向传给 opencode
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(prompt)
            prompt_path = f.name

        try:
            # opencode run 必须传 message 作为位置参数
            # 长 prompt 直接传字符串（Python subprocess 无 shell 转义问题）
            cmd = [
                'opencode', 'run',
                '--model', model_name,
                '--format', 'json',
                prompt,
            ]

            logger.info(
                f'OpenCode call: model={model_name} '
                f'prompt_len={len(prompt)}'
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ},
            )

            if result.returncode != 0:
                error_msg = (result.stderr or result.stdout or 'unknown error')[:300]
                raise RuntimeError(f'opencode run failed: {error_msg}')

            return self._parse_response(result.stdout)

        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f'opencode run timed out after {self.timeout}s'
            )
        except Exception as e:
            logger.error(f'OpenCode call failed: {e}')
            raise
        finally:
            try:
                os.unlink(prompt_path)
            except OSError:
                pass

    # ── 内部 ──────────────────────────────────────────────

    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """将 OpenAI 格式 messages 转为 plain text prompt。"""
        parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                parts.append(f'【系统指令】\n{content}')
            elif role == 'user':
                parts.append(f'{content}')
            else:
                parts.append(f'{content}')
        return '\n\n'.join(parts)

    def _parse_response(self, raw: str) -> str:
        """从 opencode --format json 输出中提取文本。"""
        texts = []
        for line in raw.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get('type') == 'text':
                    # 格式: {"type":"text","part":{"type":"text","text":"..."}}
                    part = data.get('part', {})
                    if 'text' in part:
                        texts.append(part['text'])
                    elif 'data' in part:
                        texts.append(part['data'])
                elif data.get('type') == 'error':
                    raise RuntimeError(
                        f'opencode error: {data.get("data", "unknown")}'
                    )
            except json.JSONDecodeError:
                continue

        result = ''.join(texts).strip()
        if result:
            return result
        return raw.strip()

    def _resolve_model(self, task_type: Optional[str] = None, tier: str = 'basic') -> str:
        key = (tier, task_type)
        if key in self._model_map:
            return self._model_map[key]
        return 'opencode-go/deepseek-v4-flash'
