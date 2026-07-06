# -*- coding: utf-8 -*-
"""小说生成编排器 — 统筹所有 Service 完成一个完整的小说生成流程。"""

import json
import logging
import os
import concurrent.futures
from typing import List, Optional

from .outline_service import OutlineService
from .chapter_service import ChapterService
from .reader_service import ReaderService
from .expansion_service import ExpansionService
from .cleaner_service import CleanerService

logger = logging.getLogger('GeneratorOrchestrator')


class GeneratorOrchestrator:
    """编排大纲 → 章节生成 → 扩写 → 审查 → 清洗 → 合并的全流程。"""

    def __init__(
        self,
        api_client,
        outline_service: Optional[OutlineService] = None,
        chapter_service: Optional[ChapterService] = None,
        reader_service: Optional[ReaderService] = None,
        expansion_service: Optional[ExpansionService] = None,
        cleaner_service: Optional[CleanerService] = None,
        max_workers: int = 8,
        novels_dir: str = 'novels',
    ):
        self.api = api_client
        self.outline_svc = outline_service or OutlineService(api_client)
        self.chapter_svc = chapter_service or ChapterService(api_client)
        self.reader_svc = reader_service or ReaderService(api_client)
        self.expansion_svc = expansion_service or ExpansionService(api_client)
        self.cleaner_svc = cleaner_service or CleanerService(api_client)
        self.max_workers = max_workers
        self.novels_dir = novels_dir

    # ── 新建小说 ──────────────────────────────────────────

    def generate_novel(self, title: str, chapters: int = 10):
        """生成完整小说。"""
        novel_dir = os.path.join(self.novels_dir, title)
        chap_dir = os.path.join(novel_dir, 'chaps')
        reviews_dir = os.path.join(novel_dir, 'reviews')
        summaries_dir = os.path.join(novel_dir, 'summaries')

        os.makedirs(chap_dir, exist_ok=True)
        os.makedirs(reviews_dir, exist_ok=True)
        os.makedirs(summaries_dir, exist_ok=True)

        # 1. 生成大纲
        logger.info('正在生成大纲...')
        outline = self.outline_svc.generate_outline(title, chapters)
        if not outline:
            raise RuntimeError('大纲生成失败')

        # 保存大纲
        outline_path = os.path.join(novel_dir, 'outline_structured.json')
        with open(outline_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)

        # 2. 创建 Story Bible
        bible = self.outline_svc.create_story_bible(outline)
        bible_path = os.path.join(novel_dir, 'story_bible.json')
        with open(bible_path, 'w', encoding='utf-8') as f:
            json.dump(bible, f, ensure_ascii=False, indent=2)

        # 3. 并发生成章节
        total = len(outline.get('chapters', [])) or chapters
        logger.info(f'开始生成 {total} 个章节...')
        recent_summaries: List[str] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            futures = {}
            for ch_num in range(1, total + 1):
                future = executor.submit(
                    self._process_single_chapter,
                    title, ch_num, outline,
                    recent_summaries.copy(),
                )
                futures[future] = ch_num

            for future in concurrent.futures.as_completed(futures):
                ch_num = futures[future]
                try:
                    result = future.result()
                    if result:
                        text, review_obj, summary = result

                        # 写章节文件
                        chap_path = os.path.join(chap_dir, f'chapter_{ch_num}.txt')
                        with open(chap_path, 'w', encoding='utf-8-sig') as f:
                            f.write(text)

                        # 写审查记录
                        if review_obj:
                            review_path = os.path.join(
                                reviews_dir, f'chapter_{ch_num}.json'
                            )
                            with open(review_path, 'w', encoding='utf-8') as f:
                                json.dump(review_obj, f, ensure_ascii=False, indent=2)

                        # 写摘要
                        if summary:
                            summary_path = os.path.join(
                                summaries_dir, f'chapter_{ch_num}.txt'
                            )
                            with open(summary_path, 'w', encoding='utf-8') as f:
                                f.write(summary)
                            recent_summaries.append(summary)

                        logger.info(f'第 {ch_num} 章生成完成')
                    else:
                        logger.warning(f'第 {ch_num} 章生成失败')

                except Exception as e:
                    logger.error(f'第 {ch_num} 章异常: {e}')

        # 4. 合并章节
        self._merge_chapters(novel_dir)

        logger.info(f'小说《{title}》生成完成')

    # ── 续写 ──────────────────────────────────────────────

    def continue_novel(self, title: str, additional_chapters: int = 5):
        """续写小说。"""
        novel_dir = os.path.join(self.novels_dir, title)
        chap_dir = os.path.join(novel_dir, 'chaps')

        if not os.path.exists(novel_dir):
            raise FileNotFoundError(f'小说目录不存在: {novel_dir}')

        # 读取现有章节
        existing = sorted(
            [f for f in os.listdir(chap_dir) if f.startswith('chapter_') and f.endswith('.txt')],
            key=lambda x: int(x.split('_')[1].split('.')[0]),
        )

        if not existing:
            raise ValueError('没有找到现有章节')

        # 读取大纲
        outline_path = os.path.join(novel_dir, 'outline_structured.json')
        outline = {}
        if os.path.exists(outline_path):
            with open(outline_path, 'r', encoding='utf-8') as f:
                outline = json.load(f)

        current = len(existing)
        outline_text = json.dumps(outline, ensure_ascii=False) if outline else ''

        # 读取最近摘要
        summaries_dir = os.path.join(novel_dir, 'summaries')
        recent_summaries = []
        if os.path.exists(summaries_dir):
            files = sorted(
                [f for f in os.listdir(summaries_dir) if f.endswith('.txt')],
                key=lambda x: int(x.split('_')[1].split('.')[0]),
            )
            for fn in files[-3:]:
                with open(os.path.join(summaries_dir, fn), 'r', encoding='utf-8') as f:
                    recent_summaries.append(f.read().strip())

        # 读最后一章
        with open(os.path.join(chap_dir, existing[-1]), 'r', encoding='utf-8') as f:
            last_chapter = f.read()

        reviews_dir = os.path.join(novel_dir, 'reviews')
        os.makedirs(reviews_dir, exist_ok=True)

        # 并发生成新章节
        total = current + additional_chapters
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            for ch_num in range(current + 1, total + 1):
                ch_text = self.chapter_svc.generate_continuation(
                    title, ch_num, last_chapter, outline_text,
                )
                if not ch_text:
                    logger.warning(f'第 {ch_num} 章续写失败')
                    continue

                # 扩写 + 审查
                ch_text = self.expansion_svc.ensure_length(title, ch_num, ch_text)
                _, review_obj = self.reader_svc.review(
                    title, ch_num, ch_text, outline_text, recent_summaries
                )

                ch_text = self.cleaner_svc.clean(ch_text)

                # 写文件
                chap_path = os.path.join(chap_dir, f'chapter_{ch_num}.txt')
                with open(chap_path, 'w', encoding='utf-8-sig') as f:
                    f.write(ch_text)

                if review_obj:
                    review_path = os.path.join(reviews_dir, f'chapter_{ch_num}.json')
                    with open(review_path, 'w', encoding='utf-8') as f:
                        json.dump(review_obj, f, ensure_ascii=False, indent=2)

                # 摘要
                summary = self.reader_svc.summarize(ch_text)
                if summary:
                    summary_path = os.path.join(
                        summaries_dir or os.path.join(novel_dir, 'summaries'),
                        f'chapter_{ch_num}.txt',
                    )
                    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        f.write(summary)

                last_chapter = ch_text
                logger.info(f'第 {ch_num} 章续写完成')

        self._merge_chapters(novel_dir)
        logger.info(f'小说《{title}》续写完成')

    # ── 内部：单章处理 ────────────────────────────────────

    def _process_single_chapter(self, title, ch_num, outline, recent_summaries):
        """生成 → 扩写 → 审查 → 清洗 单个章节。"""
        # 生成
        ch_text = self.chapter_svc.generate_chapter(title, ch_num, outline)
        if not ch_text:
            return None

        # 扩写
        ch_text = self.expansion_svc.ensure_length(title, ch_num, ch_text)

        # 审查 + 修订
        outline_str = json.dumps(outline, ensure_ascii=False)
        needs_revise, review_obj = self.reader_svc.review(
            title, ch_num, ch_text, outline_str, recent_summaries,
        )
        if needs_revise and review_obj and review_obj.get('suggestions'):
            ch_text = self.reader_svc.revise(
                title, ch_num, ch_text, review_obj['suggestions'],
            )

        # 摘要
        summary = self.reader_svc.summarize(ch_text)

        # 清洗
        ch_text = self.cleaner_svc.clean(ch_text)

        return ch_text, review_obj, summary

    # ── 合并章节 ──────────────────────────────────────────

    def _merge_chapters(self, novel_dir: str):
        """合并所有章节为完整小说。"""
        chap_dir = os.path.join(novel_dir, 'chaps')
        if not os.path.exists(chap_dir):
            return

        chapters = sorted(
            [f for f in os.listdir(chap_dir) if f.endswith('.txt')],
            key=lambda x: int(x.split('_')[1].split('.')[0])
            if len(x.split('_')) > 1 and x.split('_')[1].split('.')[0].isdigit()
            else 0,
        )
        if not chapters:
            return

        output_path = os.path.join(novel_dir, 'full_novel.txt')
        with open(output_path, 'w', encoding='utf-8') as out:
            for filename in chapters:
                file_path = os.path.join(chap_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as inf:
                    num = filename.split('_')[1].split('.')[0]
                    out.write(f'=== 第{num}章 ===\n\n')
                    content = self.cleaner_svc.clean(inf.read())
                    out.write(content)
                    out.write('\n\n')

        logger.info(f'小说合并完成: {output_path}')
