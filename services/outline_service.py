# -*- coding: utf-8 -*-
"""大纲生成 + Story Bible"""

import json
import logging
import time
import re
from typing import Optional

from .prompt_loader import format_prompt

logger = logging.getLogger('OutlineService')


class OutlineService:
    """生成小说大纲和故事圣经。"""

    def __init__(self, api_client):
        self.api = api_client

    def generate_outline(self, title: str, chapters: int) -> Optional[dict]:
        """生成结构化大纲，返回 dict。"""
        try:
            prompt = format_prompt('outline', title=title, chapters=chapters)
            response = self.api.chat_completion(
                messages=prompt['messages'],
                temperature=prompt['temperature'],
                max_tokens=prompt['max_tokens'],
                task_type='outline',
            )

            # 清理可能的 Markdown 标记
            cleaned = response.strip()
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

            data = json.loads(cleaned)
            logger.info(
                f"大纲生成成功: {data.get('title', title)} "
                f"共 {data.get('total_chapters', 0)} 章"
            )
            return data

        except json.JSONDecodeError as e:
            logger.warning(f"大纲 JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"大纲生成失败: {e}")
            return None

    def create_story_bible(self, outline: dict) -> dict:
        """从大纲创建故事圣经。"""
        bible = {
            'title': outline.get('title', ''),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'story_background': outline.get('story_background', ''),
            'main_themes': outline.get('main_themes', []),
            'main_characters': outline.get('main_characters', []),
            'total_chapters': outline.get('total_chapters', 0),
            'chapters': [],
            'consistency_tracker': {
                'character_traits': {},
                'plot_points': [],
                'timeline': [],
                'locations': [],
                'relationships': {},
            },
        }

        for ch in outline.get('chapters', []):
            bible['chapters'].append({
                'chapter_num': ch.get('chapter_num'),
                'title': ch.get('title', ''),
                'summary': ch.get('summary', ''),
                'key_events': ch.get('key_events', []),
                'plot_points': ch.get('plot_points', ''),
            })

        for char in outline.get('main_characters', []):
            name = char.get('name', '')
            if name:
                bible['consistency_tracker']['character_traits'][name] = {
                    'role': char.get('role', ''),
                    'characteristics': char.get('characteristics', ''),
                    'arc': char.get('arc', ''),
                }

        return bible
