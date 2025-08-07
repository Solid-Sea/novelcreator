# -*- coding: utf-8 -*-
# File: novel_generator.py
import os
from .utils import (
    logger, create_folder, get_progress, show_progress,
    clean_content, merge_chapters, load_blacklist, load_config
)
from .model_handler import ModelHandler

class NovelGenerator:
    def __init__(self, model_handler: ModelHandler, model_type: str = "ollama"):
        """初始化小说生成器
        
        Args:
            model_handler: 模型处理器实例
            model_type: 模型类型，默认为"ollama"
        """
        self.config = load_config()
        self.ollama_cfg = self.config['ollama']
        self.settings = self.config['settings']
        self.blacklist = load_blacklist()
        self.model_type = model_type
        self.model_handler = model_handler
        self._generation_cache = {}
        self._batch_size = 4

    def generate_novel(self, title: str, output_dir: str = "novels", chapters: int = 10) -> None:
        """生成完整小说
        
        Args:
            title: 小说标题
            output_dir: 输出目录
            chapters: 章节数量
        """
        try:
            novel_dir = os.path.join(output_dir, title)
            chap_dir = os.path.join(novel_dir, "chaps")
            
            # 创建目录
            create_folder(chap_dir)
            
            # 检查已有进度
            completed = get_progress(title)
            if completed > 0:
                logger.info(f"检测到已有进度，从第{completed + 1}章继续生成")
            
            # 生成大纲
            outline = self._generate_outline(title, chapters)
            if not outline:
                raise ValueError("无法生成小说大纲")
            
            # 保存大纲
            outline_path = os.path.join(novel_dir, "outline.txt")
            with open(outline_path, 'w', encoding='utf-8') as f:
                f.write(outline)
            
            # 生成章节
            progress_bar = show_progress(completed, chapters)
            
            for chapter_num in range(completed + 1, chapters + 1):
                try:
                    chapter_content = self._generate_chapter(title, chapter_num, outline)
                    if chapter_content:
                        # 清洗内容
                        cleaned_content = clean_content(chapter_content, self.blacklist)
                        
                        # 保存章节
                        chapter_path = os.path.join(chap_dir, f"chapter_{chapter_num}.txt")
                        with open(chapter_path, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
                        
                        logger.info(f"第{chapter_num}章生成完成")
                    else:
                        logger.warning(f"第{chapter_num}章生成失败，内容为空")
                        
                except Exception as e:
                    logger.error(f"生成第{chapter_num}章失败: {str(e)}")
                    continue
                
                progress_bar.update(1)
            
            progress_bar.close()
            
            # 合并章节
            merge_chapters(novel_dir)
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
        """继续生成小说
        
        Args:
            title: 小说标题
            output_dir: 输出目录
            additional_chapters: 额外章节数量
        """
        try:
            novel_dir = os.path.join(output_dir, title)
            chap_dir = os.path.join(novel_dir, "chaps")
            
            if not os.path.exists(novel_dir):
                raise FileNotFoundError(f"小说目录不存在: {novel_dir}")
            
            # 读取现有内容
            existing_chapters = []
            for file in sorted(os.listdir(chap_dir)):
                if file.startswith("chapter_") and file.endswith(".txt"):
                    with open(os.path.join(chap_dir, file), 'r', encoding='utf-8') as f:
                        existing_chapters.append(f.read())
            
            if not existing_chapters:
                raise ValueError("没有找到现有章节")
            
            # 读取大纲
            outline_path = os.path.join(novel_dir, "outline.txt")
            outline = ""
            if os.path.exists(outline_path):
                with open(outline_path, 'r', encoding='utf-8') as f:
                    outline = f.read()
            
            # 获取当前章节数
            current_chapters = len(existing_chapters)
            total_chapters = current_chapters + additional_chapters
            
            # 生成新章节
            progress_bar = show_progress(current_chapters, total_chapters)
            
            for chapter_num in range(current_chapters + 1, total_chapters + 1):
                try:
                    chapter_content = self._generate_continuation_chapter(
                        title, chapter_num, existing_chapters, outline
                    )
                    if chapter_content:
                        cleaned_content = clean_content(chapter_content, self.blacklist)
                        
                        chapter_path = os.path.join(chap_dir, f"chapter_{chapter_num}.txt")
                        with open(chapter_path, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
                        
                        logger.info(f"第{chapter_num}章生成完成")
                        existing_chapters.append(cleaned_content)
                    
                except Exception as e:
                    logger.error(f"生成第{chapter_num}章失败: {str(e)}")
                    continue
                
                progress_bar.update(1)
            
            progress_bar.close()
            
            # 重新合并章节
            merge_chapters(novel_dir)
            logger.info(f"小说《{title}》续写完成，新增{additional_chapters}章")
            
        except Exception as e:
            logger.error(f"续写小说失败: {str(e)}")
            raise

    def _generate_continuation_chapter(self, title: str, chapter_num: int, 
                                     existing_chapters: list, outline: str) -> str:
        """生成续写章节"""
        try:
            # 获取最近几章的内容作为上下文
            context = "\n\n".join(existing_chapters[-3:]) if len(existing_chapters) >= 3 else "\n\n".join(existing_chapters)
            
            prompt = f"""基于以下已有内容，继续为小说《{title}》生成第{chapter_num}章。

已有内容（最近几章）：
{context}

大纲参考：
{outline}

要求：
1. 内容要与前文保持连贯性
2. 继续发展故事情节
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
