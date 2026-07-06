# -*- coding: utf-8 -*-
"""M2 有机扩写 + M3 硬性补足策略"""

import logging
import re
import time
from typing import Optional

from .prompt_loader import format_prompt

logger = logging.getLogger('ExpansionService')


class ExpansionService:
    """确保章节达到目标字数。

    - M2: 多轮有机扩写，每轮增加细节
    - M3: 硬性追加段落，直到字数达标
    """

    def __init__(
        self,
        api_client,
        target_chars: int = 4000,
        max_expand_rounds: int = 4,
        per_round_gain: int = 1200,
        retry_backoff: int = 2,
        max_append_attempts: int = 3,
    ):
        self.api = api_client
        self.target_chars = target_chars
        self.max_expand_rounds = max_expand_rounds
        self.per_round_gain = per_round_gain
        self.retry_backoff = retry_backoff
        self.max_append_attempts = max_append_attempts

    def ensure_length(self, title: str, chapter_num: int, chapter_text: str) -> str:
        """综合 M2 + M3 策略确保字数达标。"""
        text = self._expand_m2(title, chapter_num, chapter_text)
        text = self._append_m3(title, chapter_num, text)
        return text

    # ── M2: 有机扩写 ──────────────────────────────────────

    def _expand_m2(self, title: str, chapter_num: int, chapter_text: str) -> str:
        """多轮有机扩写。"""
        current_len = self._non_space_len(chapter_text)
        if current_len >= self.target_chars:
            return chapter_text

        text = chapter_text
        for round_num in range(1, self.max_expand_rounds + 1):
            current_len = self._non_space_len(text)
            if current_len >= self.target_chars:
                break

            needed = min(self.per_round_gain, self.target_chars - current_len)
            logger.info(
                f"第{chapter_num}章 M2 第{round_num}轮：需增 {needed} 字符"
            )

            try:
                prompt = format_prompt('expand',
                    needed=needed,
                    chapter_excerpt=text[-1500:] if len(text) > 1500 else text,
                )
                expansion = self.api.chat_completion(
                    messages=prompt['messages'],
                    temperature=prompt['temperature'],
                    max_tokens=prompt['max_tokens'],
                    task_type='content',
                    tier='basic',
                )

                if expansion.strip() and not self._is_repetitive(text, expansion):
                    text += '\n\n' + expansion.strip()
                    logger.info(
                        f"M2 第{round_num}轮后长度：{self._non_space_len(text)}"
                    )

                time.sleep(self.retry_backoff)

            except Exception as e:
                logger.warning(f"M2 第{round_num}轮失败: {e}")
                break

        return text

    # ── M3: 硬性追加 ──────────────────────────────────────

    def _append_m3(self, title: str, chapter_num: int, chapter_text: str) -> str:
        """通过追加段落确保硬性最小长度。"""
        current_len = self._non_space_len(chapter_text)
        if current_len >= self.target_chars:
            return chapter_text

        text = chapter_text
        for attempt in range(1, self.max_append_attempts + 1):
            current_len = self._non_space_len(text)
            if current_len >= self.target_chars:
                break

            missing = self.target_chars - current_len
            logger.info(
                f"第{chapter_num}章 M3 第{attempt}次：缺 {missing} 字符"
            )

            try:
                messages = [
                    {'role': 'system', 'content': (
                        '你是一位才华横溢的科幻小说作家。'
                    )},
                    {'role': 'user', 'content': (
                        f'为《{title}》第 {chapter_num} 章补充约 {missing} 个字符的内容。\n\n'
                        f'当前章节结尾：\n{text[-800:]}\n\n'
                        f'要求：\n1. 与主线紧密相关\n'
                        f'2. 可以是回忆、背景故事或内心独白\n'
                        f'3. 使用中文写作\n'
                        f'4. 保持风格一致\n\n请直接输出补充内容：'
                    )},
                ]
                supplement = self.api.chat_completion(
                    messages=messages,
                    temperature=0.5,
                    max_tokens=4096,
                    task_type='content',
                    tier='basic',
                )

                if supplement.strip():
                    text += '\n\n' + supplement.strip()
                    logger.info(
                        f"M3 第{attempt}次后长度：{self._non_space_len(text)}"
                    )

            except Exception as e:
                logger.error(f"M3 第{attempt}次失败: {e}")
                break

        return text

    # ── 工具 ──────────────────────────────────────────────

    @staticmethod
    def _non_space_len(text: str) -> int:
        return len(re.sub(r'\s', '', text))

    @staticmethod
    def _is_repetitive(existing: str, new_text: str, threshold: float = 0.3) -> bool:
        """检查新内容是否与现有内容重复。"""
        new_sentences = re.split(r'[。！？]', new_text)
        existing_set = set(s.strip() for s in re.split(r'[。！？]', existing) if s.strip())

        if not new_sentences:
            return False

        dup_count = sum(1 for s in new_sentences if s.strip() in existing_set)
        return (dup_count / len(new_sentences)) > threshold
