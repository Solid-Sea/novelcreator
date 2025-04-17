# -*- coding: utf-8 -*-
import os
import json
import time
import requests
from utils import logger, create_folder, get_progress, show_progress, clean_content, load_model_handler
from typing import Optional, Any
from llama_cpp_handler import LlamaCppHandler

class NovelGenerator:
    def __init__(self) -> None:
        self.config: dict[str, Any] = self._load_config()
        self.ollama_cfg: dict[str, Any] = self.config['ollama']
        self.settings: dict[str, Any] = self.config['settings']
        self.model_handler: Optional[LlamaCppHandler] = load_model_handler(self.config)
        
    def _load_config(self) -> dict[str, Any]:
        """加载配置文件"""
        with open('config.yaml', 'r', encoding='utf-8') as f:
            import yaml
            return yaml.safe_load(f)

    def generate_novel(self, title: str) -> bool:
        """主生成流程"""
        base_dir = os.path.join(self.config['paths']['novels_dir'], title)
        total_chaps = 50  # 50万字 / 2000字每章
        
        try:
            create_folder(base_dir)
            create_folder(os.path.join(base_dir, "chaps"))
            create_folder(os.path.join(base_dir, "tl"))

            progress = get_progress(title)
            if progress == 0:
                self._generate_outline(title, base_dir)
                self._generate_chapter_outlines(title, total_chaps, base_dir)

            self._generate_chapters(title, total_chaps, base_dir, progress)
            
            logger.info(f"小说《{title}》生成完成！")
            return True
            
        except Exception as e:
            logger.critical(f"生成失败: {str(e)}")
            return False

    def _generate_outline(self, title: str, base_dir: str) -> None:
        """生成大纲"""
        logger.info("开始生成大纲...")
        prompt = (
            f"生成一本50万字的小说大纲，标题：{title}\n"
            "要求结构包含：\n"
            "1. 世界观设定（时代背景、特殊设定）\n"
            "2. 主要人物（至少3个主角的详细设定）\n"
            "3. 故事主线（起承转合结构）\n"
            "4. 关键情节转折点（至少5个）\n"
            "请用清晰的Markdown格式输出"
        )
        outline = self._safe_api_call(prompt)
        outline_path = os.path.join(base_dir, "outline.txt")
        self._save_text(outline_path, outline)
        logger.info("大纲生成完成")

    def _generate_chapter_outlines(self, title: str, total_chaps: int, base_dir: str) -> None:
        """生成章节大纲"""
        logger.info("开始生成章节大纲...")
        outline_path = os.path.join(base_dir, "outline.txt")
        with open(outline_path, 'r', encoding='utf-8') as f:
            total_outline = f.read()
        
        for i in range(1, total_chaps+1):
            prompt = (
                f"根据总大纲生成第{i}章详细大纲（500字左右）\n"
                "总大纲：\n"
                f"{total_outline}\n"
                "包含以下要素：\n"
                "1. 章节核心冲突\n" 
                "2. 场景转换节点\n"
                "3. 人物情绪变化\n"
                "4. 关键对话要点\n"
                "5. 章节结尾悬念"
            )
            chap_outline = self._safe_api_call(prompt)
            outline_path = os.path.join(base_dir, "tl", f"chap_{i:03d}.txt")
            self._save_text(outline_path, chap_outline)
            if i % 10 == 0:
                logger.info(f"已生成{i}章大纲")
        logger.info("章节大纲全部生成完成")

    def _generate_chapters(self, title: str, total_chaps: int, base_dir: str, progress: int) -> None:
        """生成章节正文"""
        logger.info("开始生成章节内容...")
        with show_progress(progress, total_chaps) as bar:
            for chap_num in range(progress+1, total_chaps+1):
                success = False
                for attempt in range(self.settings['max_retries']):
                    try:
                        outline = self._load_chapter_outline(base_dir, chap_num)
                        content = self._generate_chapter_content(outline)
                        cleaned_content = clean_content(content)
                        self._save_chapter_content(base_dir, chap_num, cleaned_content)
                        bar.update(1)
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"第{chap_num}章生成失败（尝试{attempt+1}次）: {str(e)}")
                        time.sleep(2 ** attempt)
                if not success:
                    logger.error(f"第{chap_num}章生成失败，跳过继续")
                    self._save_chapter_content(base_dir, chap_num, f"第{chap_num}章生成失败，需要手动补写")
                    bar.update(1)

    def _safe_api_call(self, prompt: str) -> str:
        """安全的API调用"""
        # 优先使用本地模型
        if self.model_handler is not None:
            try:
                return self.model_handler.generate(
                    prompt=prompt,
                    temperature=self.config['llama'].get('temperature', 0.7),
                    max_tokens=self.config['llama'].get('max_tokens', 2048)
                )
            except Exception as e:
                logger.error(f"本地模型调用失败，尝试Ollama: {str(e)}")

        # 回退到Ollama API
        payload = {
            "model": self.ollama_cfg["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.ollama_cfg.get("temperature", 0.7),
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(
                self.ollama_cfg["endpoint"],
                json=payload,
                timeout=self.settings['timeout']
            )
            response.raise_for_status()
            data = response.json()
            
            if "response" in data:
                return data["response"]
            elif "text" in data:
                return data["text"]
            else:
                raise ValueError("无效的API响应格式")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            raise

    def _save_text(self, path: str, content: str) -> None:
        """安全保存文本"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise

    def _load_chapter_outline(self, base_dir: str, chap_num: int) -> str:
        """加载章节大纲"""
        outline_path = os.path.join(base_dir, "tl", f"chap_{chap_num:03d}.txt")
        try:
            with open(outline_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取大纲失败: {str(e)}")
            raise

    def _generate_chapter_content(self, outline: str) -> str:
        """生成章节内容"""
        prompt = (
            f"根据以下大纲编写2000-2500字的小说章节：\n{outline}\n"
            "要求：\n"
            "1. 使用简体中文书面语\n"
            "2. 保持段落长度适中（3-5行）\n"
            "3. 包含至少3段对话\n"
            "4. 结尾留有悬念\n"
            "5. 避免使用违禁词汇\n"
            "6生成物直接面向读者，请避免出现多余的文字（例如接下来的剧情走向等）\n"
            "8.严格根据大纲生成，保证每一段文字之间过渡自然，描写细腻生动，人物刻画细致入微，不允许出现突兀的转折，分割线等"
        )
        content = self._safe_api_call(prompt)
        if len(content) < 1800:
            raise ValueError("生成内容过短")
        return content

    def _save_chapter_content(self, base_dir: str, chap_num: int, content: str) -> None:
        """保存章节内容"""
        chap_path = os.path.join(base_dir, "chaps", f"chap_{chap_num:03d}.txt")
        self._save_text(chap_path, content)

if __name__ == "__main__":
    print("小说生成器 v1.0")
    title = input("请输入小说标题：").strip()
    while not title:
        print("标题不能为空！")
        title = input("请输入小说标题：").strip()
    
    generator = NovelGenerator()
    success = generator.generate_novel(title)
    
    if success:
        print("\n生成成功！小说文件保存在 novels/ 目录")
    else:
        completed = get_progress(title)
        print(f"\n生成部分完成，共生成{completed}章，请查看日志文件检查失败章节")
