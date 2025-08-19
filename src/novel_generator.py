# -*- coding: utf-8 -*-
# File: novel_generator.py
import os
import re
import json
import time
from typing import Dict, Any, List, Tuple
from .utils import (
    logger, create_folder, get_progress, show_progress,
    clean_content, merge_chapters, load_blacklist, load_config
)
from .model_handler import ModelHandler

class NovelGenerator:
    def __init__(self, model_handler: ModelHandler, model_type: str = "ollama"):
        """初始化小说生成器"""
        self.config = load_config()
        self.ollama_cfg = self.config['ollama']
        self.settings = self.config['settings']
        self.blacklist = load_blacklist()
        self.model_type = model_type
        self.model_handler = model_handler
        self._generation_cache = {}
        self._batch_size = 4
        
        # Reader配置
        reader_cfg = self.settings.get('reader', {})
        self.reader_enabled: bool = bool(reader_cfg.get('enabled', False))
        self.reader_max_rounds: int = int(reader_cfg.get('max_review_rounds', 1))
        self.reader_min_total: int = int(reader_cfg.get('min_total_score', 7))
        self.reader_hard_dims: List[str] = list(reader_cfg.get('hard_fail_dims', ["coherence","character_consistency","safety"]))
        self.reader_sample_review: bool = bool(reader_cfg.get('sample_review', True))
        self.reader_sample_strategy: List[str] = list(reader_cfg.get('sample_strategy', ["head","key","tail"]))
        self.reader_max_summary_len: int = int(reader_cfg.get('max_summary_len', 400))
        
        # M2：长度与抽样配置
        self.min_chapter_chars: int = int(reader_cfg.get('min_chapter_chars', 4000))
        self.sample_threshold_chars: int = int(reader_cfg.get('sample_threshold_chars', 5000))
        
        # M3：硬性字数达标策略
        self.max_expand_rounds: int = int(reader_cfg.get('max_expand_rounds', 4))
        self.per_round_target_gain: int = int(reader_cfg.get('per_round_target_gain', 1200))
        self.retry_backoff_secs: int = int(reader_cfg.get('retry_backoff', 2))

    def _is_content_repetitive(self, existing_text: str, new_text: str, threshold: float = 0.3) -> bool:
        """检查新内容是否与现有内容重复"""
        # 简单的重复检查：检查新文本中的句子是否在现有文本中出现
        new_sentences = re.split(r'[。！？]', new_text)
        existing_sentences = re.split(r'[。！？]', existing_text)
        
        # 创建现有句子的集合用于快速查找
        existing_set = set(s.strip() for s in existing_sentences if s.strip())
        
        # 计算重复句子的比例
        if not new_sentences:
            return False
            
        duplicate_count = 0
        for sentence in new_sentences:
            if sentence.strip() in existing_set:
                duplicate_count += 1
                
        duplicate_ratio = duplicate_count / len(new_sentences)
        return duplicate_ratio > threshold

    def generate_novel(self, title: str, output_dir: str = "novels", chapters: int = 10) -> None:
        """生成完整小说"""
        try:
            novel_dir = os.path.join(output_dir, title)
            chap_dir = os.path.join(novel_dir, "chaps")
            
            create_folder(chap_dir)
            
            completed = get_progress(title)
            if completed > 0:
                logger.info(f"检测到已有进度，从第{completed + 1}章继续生成")
            
            outline = self._generate_outline(title, chapters)
            if not outline:
                raise ValueError("无法生成小说大纲")
            
            outline_path = os.path.join(novel_dir, "outline.txt")
            with open(outline_path, 'w', encoding='utf-8') as f:
                f.write(outline)
            
            progress_bar = show_progress(completed, chapters)

            reviews_dir = os.path.join(novel_dir, "reviews")
            summaries_dir = os.path.join(novel_dir, "summaries")
            create_folder(reviews_dir)
            create_folder(summaries_dir)

            recent_summaries: List[str] = []
            
            for chapter_num in range(completed + 1, chapters + 1):
                try:
                    chapter_content = self._generate_chapter(title, chapter_num, outline)
                    if not chapter_content:
                        logger.warning(f"第{chapter_num}章生成失败，内容为空")
                        progress_bar.update(1)
                        continue

                    expanded_text = self._ensure_min_length(
                        title=title,
                        chapter_num=chapter_num,
                        chapter_text=chapter_content,
                        outline=outline,
                        target_chars=self.min_chapter_chars
                    )
                    
                    ensured_text = self._ensure_hard_min_length_by_append(
                        title=title,
                        chapter_num=chapter_num,
                        chapter_text=expanded_text,
                        outline=outline,
                        target_chars=self.min_chapter_chars
                    )

                    final_text, review_obj = self._reader_review_and_revise(
                        title=title,
                        chapter_num=chapter_num,
                        chapter_text=ensured_text,
                        outline=outline,
                        recent_summaries=recent_summaries,
                        story_bible_path=os.path.join(novel_dir, "story_bible.json")
                    )

                    if review_obj is not None:
                        review_path = os.path.join(reviews_dir, f"chapter_{chapter_num}.json")
                        with open(review_path, 'w', encoding='utf-8') as rf:
                            json.dump(review_obj, rf, ensure_ascii=False, indent=2)

                    summary_text = self._summarize_chapter(final_text)
                    if summary_text:
                        with open(os.path.join(summaries_dir, f"chapter_{chapter_num}.txt"), 'w', encoding='utf-8') as sf:
                            sf.write(summary_text)
                        recent_summaries.append(summary_text)
                        if len(recent_summaries) > 3:
                            recent_summaries.pop(0)

                    # 立即清理AI分析内容
                    logger.debug(f"第{chapter_num}章清理前长度: {len(final_text)}")
                    # 提取清洗表达式（llm驱动的）
                    cleaned_content = self._extract_and_clean_llm_analysis(final_text)
                    logger.debug(f"第{chapter_num}章清理后长度: {len(cleaned_content)}")
                    chapter_path = os.path.join(chap_dir, f"chapter_{chapter_num}.txt")
                    with open(chapter_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    logger.info(f"第{chapter_num}章生成完成")

                except Exception as e:
                    logger.error(f"生成第{chapter_num}章失败: {str(e)}")
                    pass
                
                progress_bar.update(1)
            
            progress_bar.close()
            merge_chapters(novel_dir, self.blacklist)
            logger.info(f"小说《{title}》生成完成")
            
        except Exception as e:
            logger.error(f"小说生成失败: {str(e)}")
            raise

    def _generate_outline(self, title: str, chapters: int) -> str:
        """生成小说大纲"""
        try:
            prompt = f"""请为小说《{title}》生成一个详细的大纲，包含{chapters}个章节。
要求：
1. 每个章节有明确的主题和情节发展
2. 章节之间要有连贯性
3. 包含主要人物介绍和故事背景
4. 使用中文回答

请按以下格式输出：
小说标题：{title}
总章节数：{chapters}

大纲内容：
"""
            
            response = self.model_handler.generate_text(prompt, self.model_type, temperature=0.8)
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成大纲失败: {str(e)}")
            return ""

    def _generate_chapter(self, title: str, chapter_num: int, outline: str) -> str:
        """生成单个章节"""
        try:
            prompt = f"""根据以下大纲，为小说《{title}》生成第{chapter_num}章的内容。

大纲：
{outline}

要求：
1. 这是第{chapter_num}章，要符合大纲中的对应部分
2. 内容要详细生动，有对话和场景描写
3. 字数在2000-3000字之间
4. 使用中文写作
5. 章节开头要有标题

请直接开始写作第{chapter_num}章的内容：
"""
            
            response = self.model_handler.generate_text(prompt, self.model_type, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成章节失败: {str(e)}")
            return ""

    def continue_novel(self, title: str, output_dir: str = "novels", additional_chapters: int = 5) -> None:
        """继续生成小说"""
        try:
            novel_dir = os.path.join(output_dir, title)
            chap_dir = os.path.join(novel_dir, "chaps")
            
            if not os.path.exists(novel_dir):
                raise FileNotFoundError(f"小说目录不存在: {novel_dir}")
            
            existing_chapters = []
            for file in sorted(os.listdir(chap_dir)):
                if file.startswith("chapter_") and file.endswith(".txt"):
                    with open(os.path.join(chap_dir, file), 'r', encoding='utf-8') as f:
                        existing_chapters.append(f.read())
            
            if not existing_chapters:
                raise ValueError("没有找到现有章节")
            
            outline_path = os.path.join(novel_dir, "outline.txt")
            outline = ""
            if os.path.exists(outline_path):
                with open(outline_path, 'r', encoding='utf-8') as f:
                    outline = f.read()
            
            current_chapters = len(existing_chapters)
            total_chapters = current_chapters + additional_chapters
            
            progress_bar = show_progress(current_chapters, total_chapters)

            reviews_dir = os.path.join(novel_dir, "reviews")
            summaries_dir = os.path.join(novel_dir, "summaries")
            create_folder(reviews_dir)
            create_folder(summaries_dir)

            recent_summaries: List[str] = []
            try:
                summary_files = [f for f in os.listdir(summaries_dir) if f.startswith("chapter_") and f.endswith(".txt")]
                summary_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
                for fn in summary_files[-3:]:
                    with open(os.path.join(summaries_dir, fn), 'r', encoding='utf-8') as sf:
                        recent_summaries.append(sf.read().strip())
            except Exception:
                pass
            
            for chapter_num in range(current_chapters + 1, total_chapters + 1):
                try:
                    chapter_content = self._generate_continuation_chapter(
                        title, chapter_num, existing_chapters, outline
                    )
                    if not chapter_content:
                        logger.error(f"生成第{chapter_num}章失败：无内容")
                        progress_bar.update(1)
                        continue

                    expanded_text = self._ensure_min_length(
                        title=title,
                        chapter_num=chapter_num,
                        chapter_text=chapter_content,
                        outline=outline,
                        target_chars=self.min_chapter_chars
                    )
                    
                    ensured_text = self._ensure_hard_min_length_by_append(
                        title=title,
                        chapter_num=chapter_num,
                        chapter_text=expanded_text,
                        outline=outline,
                        target_chars=self.min_chapter_chars
                    )

                    final_text, review_obj = self._reader_review_and_revise(
                        title=title,
                        chapter_num=chapter_num,
                        chapter_text=ensured_text,
                        outline=outline,
                        recent_summaries=recent_summaries,
                        story_bible_path=os.path.join(novel_dir, "story_bible.json")
                    )

                    if review_obj is not None:
                        review_path = os.path.join(reviews_dir, f"chapter_{chapter_num}.json")
                        with open(review_path, 'w', encoding='utf-8') as rf:
                            json.dump(review_obj, rf, ensure_ascii=False, indent=2)

                    summary_text = self._summarize_chapter(final_text)
                    if summary_text:
                        with open(os.path.join(summaries_dir, f"chapter_{chapter_num}.txt"), 'w', encoding='utf-8') as sf:
                            sf.write(summary_text)
                        recent_summaries.append(summary_text)
                        if len(recent_summaries) > 3:
                            recent_summaries.pop(0)

                    # 立即清理AI分析内容
                    logger.debug(f"第{chapter_num}章清理前长度: {len(final_text)}")
                    # 提取清洗表达式（llm驱动的）
                    cleaned_content = self._extract_and_clean_llm_analysis(final_text)
                    logger.debug(f"第{chapter_num}章清理后长度: {len(cleaned_content)}")
                    chapter_path = os.path.join(chap_dir, f"chapter_{chapter_num}.txt")
                    with open(chapter_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    logger.info(f"第{chapter_num}章生成完成")

                except Exception as e:
                    logger.error(f"生成第{chapter_num}章失败: {str(e)}")
                    pass
                
                progress_bar.update(1)
            
            progress_bar.close()
            merge_chapters(novel_dir, self.blacklist)
            logger.info(f"小说《{title}》续写完成")
            
        except Exception as e:
            logger.error(f"续写小说失败: {str(e)}")
            raise

    def _generate_continuation_chapter(self, title: str, chapter_num: int, existing_chapters: List[str], outline: str) -> str:
        """生成续写章节"""
        try:
            last_chapter = existing_chapters[-1] if existing_chapters else ""
            prompt = f"""继续为小说《{title}》生成第{chapter_num}章的内容。

之前章节的结尾：
{last_chapter[-500:] if len(last_chapter) > 500 else last_chapter}

大纲：
{outline}

要求：
1. 这是第{chapter_num}章，要延续之前的情节
2. 内容要详细生动，有对话和场景描写
3. 字数在2000-3000字之间
4. 使用中文写作
5. 章节开头要有标题

请直接开始写作第{chapter_num}章的内容：
"""
            
            response = self.model_handler.generate_text(prompt, self.model_type, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成续写章节失败: {str(e)}")
            return ""

    def _ensure_min_length(self, title: str, chapter_num: int, chapter_text: str, outline: str, target_chars: int) -> str:
        """确保章节达到最小长度（M2策略）"""
        current_len = len(re.sub(r'\s', '', chapter_text))
        if current_len >= target_chars:
            logger.info(f"第{chapter_num}章已达标：{current_len}字符")
            return chapter_text

        rounds = 0
        expanded_text = chapter_text
        
        while current_len < target_chars and rounds < self.max_expand_rounds:
            rounds += 1
            needed = min(self.per_round_target_gain, target_chars - current_len)
            logger.info(f"第{chapter_num}章第{rounds}轮扩展，需增加{needed}字符")
            
            try:
                prompt = f"""扩写以下小说章节内容，增加{needed}字符左右。

当前章节内容：
{expanded_text[-1500:] if len(expanded_text) > 1500 else expanded_text}

要求：
1. 保持原有情节连贯性
2. 增加细节描写、对话或内心独白
3. 自然融入扩展内容
4. 使用中文写作
5. 不要重复已有的内容

请扩写内容：
"""
                
                expansion = self.model_handler.generate_text(prompt, self.model_type, temperature=0.6)
                if expansion.strip():
                    # 检查扩写内容是否与原文重复
                    if not self._is_content_repetitive(expanded_text, expansion.strip()):
                        expanded_text += "\n\n" + expansion.strip()
                        current_len = len(re.sub(r'\s', '', expanded_text))
                        logger.info(f"扩展后长度：{current_len}字符")
                    else:
                        logger.warning(f"第{rounds}轮扩展内容重复，跳过")
                
                time.sleep(self.retry_backoff_secs)
                
            except Exception as e:
                logger.warning(f"第{rounds}轮扩展失败: {str(e)}")
                break
        
        return expanded_text

    def _ensure_hard_min_length_by_append(self, title: str, chapter_num: int, chapter_text: str, outline: str, target_chars: int) -> str:
        """通过追加段落确保硬性最小长度（M3策略B）"""
        current_len = len(re.sub(r'\s', '', chapter_text))
        if current_len >= target_chars:
            return chapter_text

        logger.info(f"第{chapter_num}章需追加内容以达到{target_chars}字符")
        
        final_text = chapter_text
        attempts = 0
        
        while current_len < target_chars and attempts < 3:
            attempts += 1
            missing = target_chars - current_len
            
            try:
                prompt = f"""为小说《{title}》第{chapter_num}章补充内容，增加{missing}字符。

当前章节结尾：
{final_text[-800:] if len(final_text) > 800 else final_text}

要求：
1. 补充与主线相关的额外情节或细节
2. 可以是角色的回忆、背景故事或后续发展
3. 保持风格一致
4. 使用中文写作

请补充内容：
"""
                
                supplement = self.model_handler.generate_text(prompt, self.model_type, temperature=0.5)
                if supplement.strip():
                    final_text += "\n\n【补充】\n" + supplement.strip()
                    current_len = len(re.sub(r'\s', '', final_text))
                    logger.info(f"追加后长度：{current_len}字符")
                
                if current_len >= target_chars:
                    break
                    
            except Exception as e:
                logger.error(f"追加内容失败: {str(e)}")
                break
        
        return final_text

    def _reader_review_and_revise(self, title: str, chapter_num: int, chapter_text: str, outline: str, recent_summaries: List[str], story_bible_path: str) -> Tuple[str, Dict[str, Any]]:
        """Reader审查与修订"""
        if not self.reader_enabled:
            return chapter_text, None

        try:
            # 抽样审查
            review_text = chapter_text
            if self.reader_sample_review and len(chapter_text) > self.sample_threshold_chars:
                review_text = self._sample_text_for_review(chapter_text)
            
            # 构建审查提示
            summaries_str = "\n".join(recent_summaries) if recent_summaries else "无"
            prompt = f"""请审查以下小说章节，从多个维度评分并提供改进建议。

小说标题：《{title}》
第{chapter_num}章

大纲：
{outline}

最近章节摘要：
{summaries_str}

审查内容：
{review_text}

请按以下JSON格式回复：
{{
    "scores": {{
        "coherence": 1-5,
        "character_consistency": 1-5,
        "plot_progression": 1-5,
        "writing_style": 1-5,
        "safety": 1-5
    }},
    "total_score": 5-25,
    "issues": ["问题列表"],
    "suggestions": ["改进建议"],
    "needs_revision": true/false
}}
"""
            
            review_response = self.model_handler.generate_text(prompt, self.model_type, temperature=0.3)
            review_obj = json.loads(review_response)
            
            # 检查是否需要修订
            if review_obj.get("needs_revision", False) and review_obj.get("total_score", 0) < self.reader_min_total:
                revised_text = self._revise_chapter(title, chapter_num, chapter_text, review_obj.get("suggestions", []))
                return revised_text, review_obj
            
            return chapter_text, review_obj
            
        except Exception as e:
            logger.warning(f"Reader审查失败: {str(e)}")
            return chapter_text, None

    def _sample_text_for_review(self, text: str) -> str:
        """抽样文本用于审查"""
        samples = []
        
        for strategy in self.reader_sample_strategy:
            if strategy == "head":
                samples.append(text[:500])
            elif strategy == "tail":
                samples.append(text[-500:])
            elif strategy == "key":
                # 寻找关键段落（包含对话或重要事件）
                key_parts = re.findall(r'[^\n。！？]*[：:"“][^\n。！？]*[。！？]', text)
                if key_parts:
                    samples.extend(key_parts[:3])
        
        return "\n...\n".join(samples)

    def _revise_chapter(self, title: str, chapter_num: int, chapter_text: str, suggestions: List[str]) -> str:
        """根据建议修订章节"""
        try:
            suggestions_str = "\n".join(f"- {s}" for s in suggestions)
            prompt = f"""根据以下建议修订小说章节。

小说：《{title}》第{chapter_num}章

原始内容：
{chapter_text}

改进建议：
{suggestions_str}

要求：
1. 解决所有指出的问题
2. 保持原有情节和风格
3. 使用中文写作

请提供修订后的完整章节：
"""
            
            revised = self.model_handler.generate_text(prompt, self.model_type, temperature=0.4)
            return revised if revised.strip() else chapter_text
            
        except Exception as e:
            logger.error(f"修订章节失败: {str(e)}")
            return chapter_text

    def _summarize_chapter(self, chapter_text: str) -> str:
        """生成章节摘要"""
        try:
            prompt = f"""请为以下小说章节生成简洁的摘要。

章节内容：
{chapter_text[:2000] if len(chapter_text) > 2000 else chapter_text}

要求：
1. 用中文总结主要情节
2. 控制在200-400字之间
3. 突出关键事件和人物发展

摘要：
"""
            
            summary = self.model_handler.generate_text(prompt, self.model_type, temperature=0.3)
            return summary.strip()[:self.reader_max_summary_len]
            
        except Exception as e:
            logger.error(f"生成摘要失败: {str(e)}")
            return ""

    def _extract_and_clean_llm_analysis(self, chapter_text: str) -> str:
        """使用LLM驱动的方式提取和清洗AI分析内容"""
        try:
            # 首先使用现有的清理函数进行基础清理
            cleaned_text = clean_content(chapter_text, self.blacklist)
            
            # 检查清理后的文本是否包含明显的AI分析内容
            ai_indicators = [
                "作为专业的小说编辑",
                "你的任务是",
                "请提供需要处理的文本",
                "我的任务是",
                "接下来，我需要",
                "首先，我需要",
                "最后，我需要",
                "总结一下",
                "步骤是",
                "这样就能",
                "满足用户的需求"
            ]
            
            # 如果基础清理后的文本仍然包含明显的AI分析内容，则使用LLM清理
            if any(indicator in cleaned_text for indicator in ai_indicators):
                prompt = f"""你是一个专业的小说编辑，你的任务是从以下文本中删除所有AI生成的分析内容，只保留小说正文。

需要处理的文本：
{cleaned_text}

你的任务要求：
1. 仔细识别并删除所有AI分析、思考过程、扩写说明等内容
2. 完整保留小说正文的所有内容，不要有任何删减
3. 保持原有的段落结构和格式不变
4. 只输出清理后的小说正文，不要添加任何其他内容或说明

清理后的小说正文：
"""
                
                response = self.model_handler.generate_text(prompt, self.model_type, temperature=0.2)
                if response.strip() and not response.strip().startswith("当然，请您提供需要处理的文本") and len(response.strip()) > 50:
                    return response.strip()
            
            # 如果LLM没有返回有效内容或不需要LLM清理，返回基础清理后的文本
            return cleaned_text
                
        except Exception as e:
            logger.warning(f"LLM驱动的清理失败，使用基础清理: {str(e)}")
            # 如果LLM清理失败，返回基础清理后的文本
            return clean_content(chapter_text, self.blacklist)
