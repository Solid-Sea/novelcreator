# -*- coding: utf-8 -*-
"""Prompt 模板加载与管理"""

import json
import os
from typing import Dict, Any

_PROMPT_CACHE: Dict[str, dict] = {}

_PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')


def load_prompt(name: str) -> dict:
    """加载 prompt 模板。

    Args:
        name: 模板名（不含 .json），如 'outline', 'chapter'

    Returns:
        dict: {system, user, temperature, max_tokens, ...}
    """
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]

    path = os.path.join(_PROMPT_DIR, f'{name}.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'Prompt 模板不存在: {path}')

    with open(path, 'r', encoding='utf-8') as f:
        template = json.load(f)

    _PROMPT_CACHE[name] = template
    return template


def format_prompt(name: str, **kwargs) -> dict:
    """加载模板并填充变量，返回 OpenAI 格式的 messages 列表。

    Args:
        name: 模板名
        **kwargs: 填充模板的变量

    Returns:
        dict: {messages, temperature, max_tokens}
    """
    template = load_prompt(name)
    system_text = template.get('system', '')
    user_text = template.get('user', '')

    messages = []
    if system_text:
        messages.append({'role': 'system', 'content': system_text.format(**kwargs)})
    messages.append({'role': 'user', 'content': user_text.format(**kwargs)})

    return {
        'messages': messages,
        'temperature': template.get('temperature', 0.7),
        'max_tokens': template.get('max_tokens', 4096),
    }
