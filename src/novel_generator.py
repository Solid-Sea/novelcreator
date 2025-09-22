# -*- coding: utf-8 -*-
# File: novel_generator.py
import os
import re
import json
import time
import concurrent.futures
from typing import Dict, Any, List, Tuple
from .utils import (
    logger, create_folder, get_progress, show_progress,
    clean_content, merge_chapters, load_blacklist, load_config
)
from .model_handler import ModelHandler

class NovelGenerator:
    def __init__(self, model_handler: ModelHandler, model_type: str = None):
        """初始化小说生成器"""
        self.config = load_config()
        self.ollama_cfg = self.config['ollama']
        self.settings = self.config['settings']
        self.blacklist = load_blacklist()
        # 如果没有指定模型类型，则使用model_handler中的模型类型
        self.model_type = model_type if model_type is not None else model_handler.model_type
        self.model_handler = model_handler
        self._generation_cache = {}
        self._batch_size = 4
        self._max_workers = min(32, os.cpu_count() + 4)  # 限制最大并发数
        
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
            
            # 生成结构化大纲
            outline_json_str = self._generate_outline(title, chapters)
            if not outline_json_str:
                raise ValueError("无法生成小说大纲")
            
            # 解析结构化大纲
            try:
                outline_data = json.loads(outline_json_str)
                logger.info(f"成功解析结构化大纲，共{outline_data.get('total_chapters', 0)}章")
                
                # 保存结构化大纲
                structured_outline_path = os.path.join(novel_dir, "outline_structured.json")
                with open(structured_outline_path, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, ensure_ascii=False, indent=2)
                
                # 创建故事圣经（Story Bible）
                story_bible = self._create_story_bible(outline_data)
                story_bible_path = os.path.join(novel_dir, "story_bible.json")
                with open(story_bible_path, 'w', encoding='utf-8') as f:
                    json.dump(story_bible, f, ensure_ascii=False, indent=2)
                
                # 保存原始大纲文本
                outline_path = os.path.join(novel_dir, "outline.txt")
                with open(outline_path, 'w', encoding='utf-8') as f:
                    f.write(outline_json_str)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"大纲JSON解析失败，使用原始文本: {str(e)}")
                outline_data = None
                # 保存原始大纲文本
                outline_path = os.path.join(novel_dir, "outline.txt")
                with open(outline_path, 'w', encoding='utf-8') as f:
                    f.write(outline_json_str)
            
            progress_bar = show_progress(completed, chapters)

            reviews_dir = os.path.join(novel_dir, "reviews")
            summaries_dir = os.path.join(novel_dir, "summaries")
            create_folder(reviews_dir)
            create_folder(summaries_dir)

            recent_summaries: List[str] = []
            
            # 获取章节数量
            total_chapters = chapters
            if outline_data and 'chapters' in outline_data:
                total_chapters = len(outline_data['chapters'])
                logger.info(f"从结构化大纲获取章节数: {total_chapters}")
            
            # 使用线程池并发生成章节
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                # 提交章节生成任务
                future_to_chapter = {}
                for chapter_num in range(completed + 1, total_chapters + 1):
                    future = executor.submit(
                        self._generate_single_chapter,
                        title, chapter_num, outline_data or outline_json_str, 
                        novel_dir, reviews_dir, summaries_dir, recent_summaries
                    )
                    future_to_chapter[future] = chapter_num
                
                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_chapter):
                    chapter_num = future_to_chapter[future]
                    try:
                        result = future.result()
                        if result:
                            logger.info(f"第{chapter_num}章生成完成")
                        else:
                            logger.warning(f"第{chapter_num}章生成失败")
                    except Exception as e:
                        logger.error(f"生成第{chapter_num}章时发生异常: {str(e)}")
                    finally:
                        progress_bar.update(1)
            
            progress_bar.close()
            merge_chapters(novel_dir, self.blacklist)
            logger.info(f"小说《{title}》生成完成")
            
        except Exception as e:
            logger.error(f"小说生成失败: {str(e)}")
            raise

    def _generate_single_chapter(self, title: str, chapter_num: int, outline_data, novel_dir: str, 
                                reviews_dir: str, summaries_dir: str, recent_summaries: List[str]) -> bool:
        """生成单个章节"""
        try:
            chapter_content = self._generate_chapter_structured(title, chapter_num, outline_data)
            if not chapter_content:
                logger.warning(f"第{chapter_num}章生成失败，内容为空")
                return False

            expanded_text = self._ensure_min_length(
                title=title,
                chapter_num=chapter_num,
                chapter_text=chapter_content,
                outline=outline_data if isinstance(outline_data, str) else json.dumps(outline_data),
                target_chars=self.min_chapter_chars
            )
            
            ensured_text = self._ensure_hard_min_length_by_append(
                title=title,
                chapter_num=chapter_num,
                chapter_text=expanded_text,
                outline=outline_data if isinstance(outline_data, str) else json.dumps(outline_data),
                target_chars=self.min_chapter_chars
            )

            final_text, review_obj = self._reader_review_and_revise(
                title=title,
                chapter_num=chapter_num,
                chapter_text=ensured_text,
                outline=outline_data if isinstance(outline_data, str) else json.dumps(outline_data),
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
                # 注意：这里不更新recent_summaries，因为在并发环境下会有竞争条件

            # 立即清理AI分析内容
            logger.debug(f"第{chapter_num}章清理前长度: {len(final_text)}")
            # 提取清洗表达式（llm驱动的）
            cleaned_content = self._extract_and_clean_llm_analysis(final_text)
            logger.debug(f"第{chapter_num}章清理后长度: {len(cleaned_content)}")
            chapter_path = os.path.join(novel_dir, "chaps", f"chapter_{chapter_num}.txt")
            # 使用UTF-8-BOM编码写入文件，避免乱码
            with open(chapter_path, 'w', encoding='utf-8-sig') as f:
                f.write(cleaned_content)
            
            return True
        except Exception as e:
            logger.error(f"生成第{chapter_num}章失败: {str(e)}")
            return False

    def _generate_outline(self, title: str, chapters: int) -> str:
        """生成小说大纲"""
        try:
            prompt = f"""你是一位专业的小说创作顾问，你的任务是为《{title}》这部科幻小说创作一个引人入胜的大纲，包含{chapters}个章节。

你的目标是创造一个既有深刻主题又能吸引读者的故事。请考虑以下要素：
1. 强烈的情感线索：故事应该能引起读者的情感共鸣
2. 复杂而有深度的角色：角色应该有成长和变化
3. 意想不到的情节转折：保持读者的兴趣
4. 深刻的主题：探讨有意义的思想和概念

请严格按照以下JSON格式输出，只输出JSON内容，不要添加任何其他说明或格式标记：
{{
    "title": "{title}",
    "total_chapters": {chapters},
    "story_background": "详细的故事背景设定，包括世界观、时代背景等",
    "main_themes": ["主要主题1", "主要主题2"],  // 添加主题元素
    "emotional_arc": "整体情感弧线描述",  // 添加情感线索
    "main_characters": [
        {{
            "name": "角色姓名",
            "role": "角色身份",
            "characteristics": "角色特征，包括性格、动机、恐惧等",
            "arc": "角色在整个故事中的成长弧线",  // 添加角色发展
            "relationship": "与其他角色的关系及变化",
            "conflict": "角色面临的主要内外部冲突"  // 添加角色冲突
        }}
    ],
    "chapters": [
        {{
            "chapter_num": 1,
            "title": "章节标题",
            "summary": "章节概要，包括关键事件和转折点",
            "key_events": ["重要事件1", "重要事件2"],
            "character_development": "本章中角色的重要发展",
            "emotional_beat": "本章的情感节拍",  // 添加情感节拍
            "plot_points": "关键情节点",
            "conflict": "本章的主要冲突",  // 添加章节冲突
            "themes_explored": ["本章探讨的主题"]  // 添加主题探讨
        }}
    ]
}}

请直接输出纯净的JSON格式大纲，不要使用代码块标记（如```json），不要添加任何解释说明，确保JSON语法正确。确保内容具有情感深度和吸引力：
"""
            
            response = self.model_handler.generate_text_with_model(prompt, "outline", self.model_type, temperature=0.8)
            # 清理可能的Markdown标记
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # 移除代码块标记
                lines = cleaned_response.split('\n')
                if lines[0].strip().startswith("```"):
                    lines.pop(0)
                if lines and lines[-1].strip().startswith("```"):
                    lines.pop()
                cleaned_response = '\n'.join(lines).strip()
            
            # 尝试修复常见的JSON格式错误
            cleaned_response = self._fix_json_format(cleaned_response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"生成大纲失败: {str(e)}")
            return ""

    def _fix_json_format(self, json_str: str) -> str:
        """修复常见的JSON格式错误"""
        try:
            # 尝试直接解析
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
        
        # 修复双逗号问题
        import re
        fixed_str = re.sub(r',\s*,', ',', json_str)
        
        # 修复末尾逗号问题
        fixed_str = re.sub(r',\s*([}\]])', r'\1', fixed_str)
        
        # 移除可能的额外文本
        lines = fixed_str.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            if line.strip().startswith('{'):
                in_json = True
            
            if in_json:
                json_lines.append(line)
                # 计算大括号数量
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    break
        
        if json_lines:
            fixed_str = '\n'.join(json_lines)
        
        return fixed_str.strip()

    def _generate_chapter_structured(self, title: str, chapter_num: int, outline_data) -> str:
        """生成结构化章节"""
        try:
            # 如果outline_data是字符串，说明是原始大纲
            if isinstance(outline_data, str):
                return self._generate_chapter(title, chapter_num, outline_data)
            
            # 获取章节信息
            chapter_info = None
            if 'chapters' in outline_data:
                for chap in outline_data['chapters']:
                    if chap.get('chapter_num') == chapter_num:
                        chapter_info = chap
                        break
            
            if chapter_info:
                # 使用结构化信息生成章节
                prompt = f"""你是一位才华横溢的科幻小说作家，你的任务是为《{title}》第{chapter_num}章创作一段引人入胜的内容。
    
    你的写作风格应该是：
    1. 情感丰富：深入描绘角色的内心世界和情感变化
    2. 感官生动：使用丰富的感官描写让读者身临其境
    3. 节奏紧凑：平衡动作、对话和描述，保持读者兴趣
    4. 主题深刻：自然地融入故事主题和思想
    
    小说背景：
    {outline_data.get('story_background', '')}
    
    主要主题：
    {', '.join(outline_data.get('main_themes', []))}
    
    整体情感弧线：
    {outline_data.get('emotional_arc', '')}
    
    主要角色：
    {chr(10).join([f"- {char.get('name', '')}: {char.get('role', '')} - {char.get('characteristics', '')} - 角色弧线: {char.get('arc', '')} - 冲突: {char.get('conflict', '')}" for char in outline_data.get('main_characters', [])])}
    
    当前章节信息：
    章节标题：{chapter_info.get('title', '')}
    章节概要：{chapter_info.get('summary', '')}
    关键事件：{', '.join(chapter_info.get('key_events', []))}
    角色发展：{chapter_info.get('character_development', '')}
    情感节拍：{chapter_info.get('emotional_beat', '')}
    情节点：{chapter_info.get('plot_points', '')}
    冲突：{chapter_info.get('conflict', '')}
    探讨主题：{', '.join(chapter_info.get('themes_explored', []))}
    
    写作要求：
    1. 这是第{chapter_num}章，要符合大纲中的对应部分
    2. 内容要详细生动，有丰富的对话和场景描写
    3. 字数在2500-3500字之间
    4. 使用中文写作
    5. 章节开头要有引人入胜的标题
    6. 严格按照章节信息展开情节
    7. 重点刻画角色的情感变化和内心冲突
    8. 创造强烈的画面感和氛围感
    9. 在章节结尾设置悬念或转折，吸引读者继续阅读
    
    请直接开始写作第{chapter_num}章的内容，确保文字具有吸引力、连贯性和情感共鸣：
    """
            else:
                # 如果没有找到章节信息，使用原始方式
                prompt = f"""根据以下大纲，为小说《{title}》生成第{chapter_num}章的内容。

大纲：
{json.dumps(outline_data, ensure_ascii=False, indent=2) if isinstance(outline_data, dict) else outline_data}

要求：
1. 这是第{chapter_num}章，要符合大纲中的对应部分
2. 内容要详细生动，有对话和场景描写
3. 字数在2000-3000字之间
4. 使用中文写作
5. 章节开头要有标题

请直接开始写作第{chapter_num}章的内容：
"""
            
            response = self.model_handler.generate_text_with_model(prompt, "content", self.model_type, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成结构化章节失败: {str(e)}")
            # 回退到原始章节生成
            return self._generate_chapter(title, chapter_num, json.dumps(outline_data, ensure_ascii=False) if isinstance(outline_data, dict) else str(outline_data))

    def _generate_chapter(self, title: str, chapter_num: int, outline: str) -> str:
        """生成单个章节"""
        try:
            prompt = f"""你是一位才华横溢的科幻小说作家，你的任务是为《{title}》第{chapter_num}章创作一段引人入胜的内容。

你的写作风格应该是：
1. 情感丰富：深入描绘角色的内心世界和情感变化
2. 感官生动：使用丰富的感官描写让读者身临其境
3. 节奏紧凑：平衡动作、对话和描述，保持读者兴趣
4. 主题深刻：自然地融入故事主题和思想

大纲：
{outline}

写作要求：
1. 这是第{chapter_num}章，要符合大纲中的对应部分
2. 内容要详细生动，有丰富的对话和场景描写
3. 字数在2500-3500字之间
4. 使用中文写作
5. 章节开头要有引人入胜的标题
6. 重点刻画角色的情感变化和内心冲突
7. 创造强烈的画面感和氛围感
8. 在章节结尾设置悬念或转折，吸引读者继续阅读

请直接开始写作第{chapter_num}章的内容，确保文字具有吸引力、连贯性和情感共鸣：
"""
            
            response = self.model_handler.generate_text(prompt, self.model_type, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成章节失败: {str(e)}")
            return ""

    def _create_story_bible(self, outline_data: dict) -> dict:
        """创建故事圣经（Story Bible）- 存储小说的核心信息"""
        try:
            story_bible = {
                "title": outline_data.get("title", ""),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "story_background": outline_data.get("story_background", ""),
                "main_characters": outline_data.get("main_characters", []),
                "total_chapters": outline_data.get("total_chapters", 0),
                "chapters": [],
                "consistency_tracker": {
                    "character_traits": {},
                    "plot_points": [],
                    "timeline": [],
                    "locations": [],
                    "relationships": {}
                }
            }
            
            # 处理章节信息
            for chapter in outline_data.get("chapters", []):
                story_bible["chapters"].append({
                    "chapter_num": chapter.get("chapter_num"),
                    "title": chapter.get("title", ""),
                    "summary": chapter.get("summary", ""),
                    "key_events": chapter.get("key_events", []),
                    "character_development": chapter.get("character_development", ""),
                    "plot_points": chapter.get("plot_points", "")
                })
                
                # 跟踪关键情节点
                if "plot_points" in chapter:
                    story_bible["consistency_tracker"]["plot_points"].append({
                        "chapter": chapter.get("chapter_num"),
                        "points": chapter.get("plot_points", "")
                    })
            
            # 初始化角色特征跟踪
            for character in outline_data.get("main_characters", []):
                char_name = character.get("name", "")
                if char_name:
                    story_bible["consistency_tracker"]["character_traits"][char_name] = {
                        "role": character.get("role", ""),
                        "characteristics": character.get("characteristics", ""),
                        "relationship": character.get("relationship", "")
                    }
            
            logger.info("故事圣经创建完成")
            return story_bible
            
        except Exception as e:
            logger.error(f"创建故事圣经失败: {str(e)}")
            return {
                "title": outline_data.get("title", ""),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "story_background": "",
                "main_characters": [],
                "chapters": [],
                "consistency_tracker": {}
            }

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
            
            # 使用线程池并发生成章节
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                # 提交章节生成任务
                future_to_chapter = {}
                for chapter_num in range(current_chapters + 1, total_chapters + 1):
                    future = executor.submit(
                        self._generate_single_chapter,
                        title, chapter_num, outline,
                        novel_dir, reviews_dir, summaries_dir, recent_summaries
                    )
                    future_to_chapter[future] = chapter_num
                
                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_chapter):
                    chapter_num = future_to_chapter[future]
                    try:
                        result = future.result()
                        if result:
                            logger.info(f"第{chapter_num}章续写完成")
                        else:
                            logger.warning(f"第{chapter_num}章续写失败")
                    except Exception as e:
                        logger.error(f"续写第{chapter_num}章时发生异常: {str(e)}")
                    finally:
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
                prompt = f"""你是一位专业的小说编辑，你的任务是为以下科幻小说章节内容进行高质量的扩写，增加约{needed}个字符。
    
    你的扩写应该：
    1. 增强情感深度：深入描绘角色的内心世界和情感变化
    2. 丰富感官体验：添加更多视觉、听觉、触觉等感官描写
    3. 强化角色动机：更清楚地展现角色的行为原因和心理活动
    4. 营造氛围：通过细节描写增强场景的氛围感
    5. 保持连贯性：确保新内容与原有情节无缝衔接
    
    当前章节内容：
    {expanded_text[-1500:] if len(expanded_text) > 1500 else expanded_text}
    
    扩写要求：
    1. 保持原有情节连贯性
    2. 重点增加情感描写、内心独白和感官细节
    3. 自然融入扩展内容，不要显得突兀
    4. 使用中文写作
    5. 不要重复已有的内容
    6. 增强读者的情感共鸣和沉浸感
    
    请进行高质量的扩写：
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
                prompt = f"""你是一位才华横溢的科幻小说作家，你的任务是为《{title}》第{chapter_num}章补充高质量的内容，增加约{missing}个字符。
    
    你的补充内容应该：
    1. 增强故事的吸引力：添加引人入胜的情节元素
    2. 深化角色塑造：展现角色更深层的动机和情感
    3. 丰富世界观：提供更多关于故事背景的细节
    4. 强化主题表达：更清晰地传达故事的核心思想
    
    当前章节结尾：
    {final_text[-800:] if len(final_text) > 800 else final_text}
    
    补充要求：
    1. 补充与主线紧密相关的情节或细节
    2. 可以是角色的回忆、背景故事、内心独白或后续发展
    3. 保持风格一致，确保文字质量
    4. 使用中文写作
    5. 增强情感深度和读者的沉浸感
    
    请补充高质量的内容：
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
            prompt = f"""你是一位经验丰富的科幻小说编辑和评论家，你的任务是从多个维度对以下小说章节进行专业评估，以帮助提升作品质量。你的评估将直接影响作品的最终质量，请务必认真对待。

你的评估应该：
1. 客观公正：基于文本本身进行评价，避免主观偏见
2. 具体详细：提供具体的例子和改进建议，避免空泛的评价
3. 关注情感共鸣：特别注意作品是否能引起读者的情感共鸣，这是优秀小说的核心
4. 注重吸引力：评估作品是否能吸引和保持读者的兴趣，是否有足够的悬念和冲突
5. 重视创新性：评估作品是否有独特的创意和新颖的表达方式
6. 关注技术细节：检查语言表达、情节逻辑、角色塑造等方面的技术问题

小说标题：《{title}》第{chapter_num}章

大纲：
{outline}

最近章节摘要：
{summaries_str}

审查内容：
{review_text}

评估标准（满分5分）：
- 情节连贯性（coherence）：情节发展是否合理，逻辑是否清晰
- 角色一致性（character_consistency）：角色行为是否符合其设定，是否有明显矛盾
- 情节推进（plot_progression）：情节是否有足够的推进力，是否吸引人
- 写作风格（writing_style）：语言表达是否流畅，风格是否统一
- 情感冲击力（emotional_impact）：是否能引起读者的情感共鸣，是否有感染力
- 吸引力（engagement）：是否能吸引读者继续阅读，是否有足够的悬念
- 创新性（creativity）：是否有独特的创意和新颖的表达
- 安全性（safety）：内容是否符合法律法规和社会道德

请按以下JSON格式回复，评分要严格按标准执行：
{{
    "scores": {{
        "coherence": 1-5, // 情节连贯性
        "character_consistency": 1-5,  // 角色一致性
        "plot_progression": 1-5,  // 情节推进
        "writing_style": 1-5,  // 写作风格
        "emotional_impact": 1-5,  // 情感冲击力
        "engagement": 1-5,  // 吸引力
        "creativity": 1-5,  // 创新性（新增）
        "safety": 1-5  // 安全性
    }},
    "total_score": 8-40,  // 总分范围更新（8项评分）
    "strengths": ["具体优点列表，每项都要有具体例子"],  // 详细优点评估
    "issues": ["具体问题列表，每项都要有具体例子"],
    "suggestions": ["具体改进建议，每项都要有针对性"],
    "emotional_analysis": "详细的情感共鸣分析，包括哪些段落引起了情感共鸣，哪些没有",  // 详细情感分析
    "engagement_analysis": "详细的吸引力分析，包括哪些地方吸引人，哪些地方显得平淡",  // 详细吸引力分析
    "creativity_analysis": "详细的创新性分析，包括哪些地方有创意，哪些地方显得平庸",  // 新增创新性分析
    "needs_revision": true/false,  // 是否需要修订（总分低于30分且有具体问题时为true）
    "revision_priority": "high/medium/low"  // 修订优先级
}}
"""
            
            review_response = self.model_handler.generate_text_with_model(prompt, "review", self.model_type, temperature=0.3)
            review_obj = json.loads(review_response)
            
            # 检查是否需要修订
            # 改进修订条件：总分低于32分或修订优先级为high时才进行修订
            total_score = review_obj.get("total_score", 0)
            needs_revision = review_obj.get("needs_revision", False)
            revision_priority = review_obj.get("revision_priority", "low")
            
            if needs_revision and (total_score < self.reader_min_total or revision_priority == "high"):
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
            prompt = f"""你是一位专业的小说编辑，你的任务是根据以下建议对小说章节进行高质量的修订，以显著提升作品质量。请认真对待每一项建议，确保修订后的内容有明显改善。

你的修订应该：
1. 全面解决指出的问题：仔细分析每一条建议，确保问题得到彻底解决
2. 增强情感深度和角色塑造：深入刻画角色内心世界，增强情感表达的感染力
3. 提高文字的吸引力和流畅性：优化语言表达，使文字更具吸引力和阅读流畅性
4. 保持原有情节和风格的一致性：在改进的同时确保不破坏原有故事线和写作风格
5. 增强创新性：在修订中加入新颖的元素和创意表达
6. 提升悬念和冲突：增强故事的吸引力，增加读者的阅读兴趣

小说：《{title}》第{chapter_num}章

原始内容：
{chapter_text}

改进建议：
{suggestions_str}

修订要求：
1. 解决所有指出的问题：每一条建议都必须得到回应和解决
2. 重点增强情感描写和角色内心世界：增加能够引起读者情感共鸣的描写
3. 提高文字的吸引力和沉浸感：使用更生动、更具吸引力的语言
4. 保持原有情节和风格：确保修订后的内容与原作风格一致
5. 增强创新性表达：在保持原意的基础上，尝试新颖的表达方式
6. 使用中文写作：确保语言符合中文表达习惯
7. 确保修订后的内容更加引人入胜：修订后的内容应该在各个方面都有明显提升

请提供修订后的完整章节，确保文字具有更强的吸引力、连贯性、情感共鸣和创新性。修订后的内容应该比原文有显著提升：
"""
            
            revised = self.model_handler.generate_text(prompt, self.model_type, temperature=0.4)
            return revised if revised.strip() else chapter_text
            
        except Exception as e:
            logger.error(f"修订章节失败: {str(e)}")
            return chapter_text

    def _summarize_chapter(self, chapter_text: str) -> str:
        """生成章节摘要"""
        try:
            prompt = f"""你是一位专业的文学编辑，你的任务是为以下科幻小说章节生成高质量的摘要。

你的摘要应该：
1. 突出情节核心：准确概括主要事件
2. 强调情感线索：体现角色的情感变化
3. 保持吸引力：让读者对后续内容产生兴趣

章节内容：
{chapter_text[:2000] if len(chapter_text) > 2000 else chapter_text}

摘要要求：
1. 用中文总结主要情节
2. 控制在250-350字之间
3. 突出关键事件、角色发展和情感变化
4. 避免剧透重要情节转折
5. 语言简洁有力，具有吸引力

请生成高质量的摘要：
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
