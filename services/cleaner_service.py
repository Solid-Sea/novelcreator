# -*- coding: utf-8 -*-
"""LLM 自清洗内容 + 通用算法兜底"""

import logging
import re
from typing import Optional

from .prompt_loader import format_prompt

logger = logging.getLogger('CleanerService')


class CleanerService:
    """清理小说正文中的 AI 分析痕迹。

    策略（按优先级）：
    1. LLM 自清洗 — 让模型自己判断哪些是分析内容
    2. 通用算法兜底 — 去重、空行归一、乱码清理
    3. 黑名单过滤 — 精确匹配 + 范围匹配
    """

    def __init__(self, api_client, blacklist: Optional[dict] = None):
        self.api = api_client
        self.blacklist = blacklist or {'exact': [], 'ranges': []}

    def clean(self, text: str) -> str:
        """全流程清洗。"""
        # 1. LLM 自清洗（主要策略）
        text = self._llm_clean(text)

        # 2. 通用算法兜底
        text = self._algorithm_clean(text)

        # 3. 黑名单过滤
        text = self._blacklist_filter(text)

        return text

    # ── LLM 自清洗 ────────────────────────────────────────

    def _llm_clean(self, text: str) -> str:
        """让 LLM 自己识别并删除分析性内容。"""
        try:
            prompt = format_prompt('clean', text=text)
            response = self.api.chat_completion(
                messages=prompt['messages'],
                temperature=prompt['temperature'],
                max_tokens=prompt['max_tokens'],
            )

            if response and len(response) > 50:
                # 确保 LLM 返回了有效内容，不是敷衍的回复
                placeholder_patterns = [
                    '当然，请您提供需要处理的文本',
                    '请提供需要处理的文本',
                    '我没有收到需要处理的文本',
                ]
                if not any(p in response for p in placeholder_patterns):
                    return response.strip()

            return text

        except Exception as e:
            logger.warning(f"LLM 自清洗失败，使用算法兜底: {e}")
            return text

    # ── 算法兜底 ──────────────────────────────────────────

    def _algorithm_clean(self, text: str) -> str:
        """通用算法清理（去重、空行、乱码）。"""
        # 删除重复段落
        lines = text.split('\n')
        cleaned = []
        seen_paras = set()

        current_para = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_para:
                    para_text = '\n'.join(current_para).strip()
                    if para_text and para_text not in seen_paras:
                        cleaned.extend(current_para)
                        cleaned.append('')
                        seen_paras.add(para_text)
                    current_para = []
                elif not cleaned or cleaned[-1] != '':
                    cleaned.append('')
            else:
                current_para.append(line)

        # 最后一段
        if current_para:
            para_text = '\n'.join(current_para).strip()
            if para_text and para_text not in seen_paras:
                cleaned.extend(current_para)

        # 合并，限制连续空行最多 1 个
        text = '\n'.join(cleaned)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 清理乱码控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

        return text.strip()

    # ── 黑名单 ────────────────────────────────────────────

    def _blacklist_filter(self, text: str) -> str:
        """应用黑名单过滤。"""
        for pattern in self.blacklist.get('ranges', []):
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        for word in self.blacklist.get('exact', []):
            text = re.sub(re.escape(word), '[已屏蔽]', text)
        return text
