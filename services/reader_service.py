# -*- coding: utf-8 -*-
"""Reader 质量审查 + 修订"""

import json
import logging
from typing import Optional, Dict, Any, List

from .prompt_loader import format_prompt

logger = logging.getLogger('ReaderService')


class ReaderService:
    """多维度质量审查与修订。"""

    # 硬性失败维度
    HARD_FAIL_DIMS = ['coherence', 'character_consistency', 'safety']
    # 评分维度列表
    DIMS = [
        'coherence', 'character_consistency', 'plot_progression',
        'writing_style', 'emotional_impact', 'engagement',
        'creativity', 'safety',
    ]

    def __init__(
        self,
        api_client,
        enabled: bool = True,
        min_total_score: int = 32,
        max_review_rounds: int = 2,
        sample_review: bool = True,
        sample_strategy: list = None,
        sample_threshold: int = 5000,
        max_summary_len: int = 400,
    ):
        self.api = api_client
        self.enabled = enabled
        self.min_total_score = min_total_score
        self.max_review_rounds = max_review_rounds
        self.sample_review = sample_review
        self.sample_strategy = sample_strategy or ['head', 'key', 'tail']
        self.sample_threshold = sample_threshold
        self.max_summary_len = max_summary_len

    # ── 审查 ──────────────────────────────────────────────

    def review(
        self,
        title: str,
        chapter_num: int,
        chapter_text: str,
        outline: str,
        recent_summaries: List[str] = None,
    ) -> tuple:
        """执行 Reader 审查，返回 (是否需要修订, review_dict)。"""
        if not self.enabled:
            return False, None

        try:
            review_text = chapter_text
            if self.sample_review and len(chapter_text) > self.sample_threshold:
                review_text = self._sample_text(chapter_text)

            summaries_str = '\n'.join(recent_summaries) if recent_summaries else '无'

            prompt = format_prompt('review',
                title=title,
                chapter_num=chapter_num,
                review_text=review_text,
                summaries=summaries_str,
            )
            response = self.api.chat_completion(
                messages=prompt['messages'],
                temperature=prompt['temperature'],
                max_tokens=prompt['max_tokens'],
                task_type='review',
            )

            review_obj = json.loads(self._clean_json(response))
            total_score = review_obj.get('total_score', 0)
            needs_revision = review_obj.get('needs_revision', False)
            priority = review_obj.get('revision_priority', 'low')

            should_revise = needs_revision and (
                total_score < self.min_total_score or priority == 'high'
            )
            return should_revise, review_obj

        except Exception as e:
            logger.warning(f"Reader 审查失败: {e}")
            return False, None

    # ── 修订 ──────────────────────────────────────────────

    def revise(
        self,
        title: str,
        chapter_num: int,
        chapter_text: str,
        suggestions: List[str],
    ) -> str:
        """根据建议修订章节。"""
        try:
            prompt = format_prompt('revise',
                title=title,
                chapter_num=chapter_num,
                suggestions='\n'.join(f'- {s}' for s in suggestions),
                chapter_text=chapter_text,
            )
            response = self.api.chat_completion(
                messages=prompt['messages'],
                temperature=prompt['temperature'],
                max_tokens=prompt['max_tokens'],
                task_type='review',
            )
            return response.strip() if response.strip() else chapter_text

        except Exception as e:
            logger.error(f"修订失败: {e}")
            return chapter_text

    # ── 摘要 ──────────────────────────────────────────────

    def summarize(self, chapter_text: str) -> str:
        """生成章节摘要。"""
        try:
            prompt = format_prompt('summary',
                chapter_text=chapter_text[:2000],
            )
            response = self.api.chat_completion(
                messages=prompt['messages'],
                temperature=prompt['temperature'],
                max_tokens=prompt['max_tokens'],
            )
            return response.strip()[:self.max_summary_len]

        except Exception as e:
            logger.warning(f"摘要生成失败: {e}")
            return ''

    # ── 内部工具 ──────────────────────────────────────────

    def _sample_text(self, text: str) -> str:
        """抽样文本用于审查（节省 token）。"""
        samples = []
        for strategy in self.sample_strategy:
            if strategy == 'head':
                samples.append(text[:500])
            elif strategy == 'tail':
                samples.append(text[-500:])
            elif strategy == 'key':
                import re
                key_parts = re.findall(r'[^\n。！？]*[：:"“][^\n。！？]*[。！？]', text)
                if key_parts:
                    samples.extend(key_parts[:3])
        return '\n...\n'.join(samples) if samples else text[:1000]

    @staticmethod
    def _clean_json(text: str) -> str:
        """清理模型返回的 JSON 字符串。"""
        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith('```'):
                lines = lines[:-1]
            text = '\n'.join(lines).strip()
        return text
