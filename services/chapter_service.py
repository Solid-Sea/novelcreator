# -*- coding: utf-8 -*-
"""章节生成 + 续写"""

import json
import logging
from typing import Optional, List

from .prompt_loader import format_prompt
from .text_optimizer import optimize_chapter_text, strip_ai_prefix, strip_suffix

logger = logging.getLogger('ChapterService')


class ChapterService:
    """生成和续写小说章节。"""

    def __init__(self, api_client):
        self.api = api_client

    def generate_chapter(
        self,
        title: str,
        chapter_num: int,
        outline_data: dict,
    ) -> str:
        """根据结构化大纲生成章节。"""
        chapter_info = None
        for ch in outline_data.get('chapters', []):
            if ch.get('chapter_num') == chapter_num:
                chapter_info = ch
                break

        if chapter_info is None:
            return self._generate_from_outline_text(
                title, chapter_num, json.dumps(outline_data, ensure_ascii=False)
            )

        characters = '\n'.join(
            f"- {c.get('name', '')}: {c.get('role', '')} - {c.get('characteristics', '')}"
            for c in outline_data.get('main_characters', [])
        )

        prompt = format_prompt('chapter',
            title=title,
            chapter_num=chapter_num,
            story_background=outline_data.get('story_background', ''),
            characters=characters,
            chapter_summary=chapter_info.get('summary', ''),
            key_events=', '.join(chapter_info.get('key_events', [])),
        )
        response = self.api.chat_completion(
            messages=prompt['messages'],
            temperature=prompt['temperature'],
            max_tokens=prompt['max_tokens'],
            task_type='content',
            tier='basic',
        )
        raw = response.strip()
        raw = strip_ai_prefix(raw)
        raw = strip_suffix(raw)
        return optimize_chapter_text(raw)

    def _generate_from_outline_text(self, title: str, chapter_num: int, outline: str) -> str:
        """回退：用纯文本大纲生成章节。"""
        prompt = format_prompt('chapter',
            title=title,
            chapter_num=chapter_num,
            story_background='',
            characters='',
            chapter_summary=outline[:500],
            key_events='',
        )
        response = self.api.chat_completion(
            messages=prompt['messages'],
            temperature=prompt['temperature'],
            max_tokens=prompt['max_tokens'],
            task_type='content',
            tier='basic',
        )
        raw = response.strip()
        raw = strip_ai_prefix(raw)
        raw = strip_suffix(raw)
        return optimize_chapter_text(raw)

    def generate_continuation(
        self,
        title: str,
        chapter_num: int,
        last_chapter_text: str,
        outline: str,
    ) -> str:
        """生成续写章节。"""
        messages = [
            {'role': 'system', 'content': '你是一位才华横溢的科幻小说作家。'},
            {'role': 'user', 'content': (
                f'继续为小说《{title}》生成第 {chapter_num} 章的内容。\n\n'
                f'之前章节的结尾：\n{last_chapter_text[-500:]}\n\n'
                f'大纲：\n{outline[:1000]}\n\n'
                f'要求：\n1. 延续之前的情节\n'
                f'2. 内容详细生动，有对话和场景描写\n'
                f'3. 字数 2000-3000 字\n'
                f'4. 使用中文写作\n'
                f'5. 章节开头有标题\n\n'
                f'请直接开始写第 {chapter_num} 章的内容：'
            )},
        ]
        response = self.api.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=8192,
            task_type='content',
            tier='basic',
        )
        raw = response.strip()
        raw = strip_ai_prefix(raw)
        raw = strip_suffix(raw)
        return optimize_chapter_text(raw)
