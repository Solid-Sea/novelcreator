# -*- coding: utf-8 -*-
# File: video_generator.py
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import re
import textwrap
from .utils import load_config, logger

class VideoGenerator:
    def __init__(self):
        self.config = load_config()
        self.settings = self.config.get('settings', {})
        self.video_settings = self.settings.get('video', {})
        
        # 视频参数
        self.width = self.video_settings.get('width', 1920)
        self.height = self.video_settings.get('height', 1080)
        self.fps = self.video_settings.get('fps', 24)
        self.font_size = self.video_settings.get('font_size', 32)
        self.text_color = tuple(self.video_settings.get('text_color', [255, 255, 255]))
        self.bg_color = tuple(self.video_settings.get('bg_color', [0, 0, 0]))
        self.margin = self.video_settings.get('margin', 100)
        self.line_spacing = self.video_settings.get('line_spacing', 10)
        
    def generate_video(self, input_text: str, output_path: str, font_path: str = None) -> None:
        """从文本生成视频"""
        try:
            if not os.path.exists(input_text):
                raise FileNotFoundError(f"输入文件不存在: {input_text}")
                
            with open(input_text, 'r', encoding='utf-8') as f:
                text = f.read()
                
            if not text.strip():
                raise ValueError("输入文件为空")
                
            self.generate_from_text(text, output_path, font_path)
            
        except Exception as e:
            logger.error(f"视频生成失败: {str(e)}")
            raise

    def generate_from_text(self, text: str, output_path: str, font_path: str = None) -> None:
        """从文本内容生成视频"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            # 分割文本为段落
            paragraphs = self._split_text(text)
            if not paragraphs:
                raise ValueError("没有可处理的文本内容")
                
            # 设置字体
            if font_path is None:
                font_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'SimHei.ttf')
                
            if not os.path.exists(font_path):
                logger.warning(f"字体文件不存在，使用默认字体: {font_path}")
                font = ImageFont.load_default()
            else:
                try:
                    font = ImageFont.truetype(font_path, self.font_size)
                except Exception as e:
                    logger.warning(f"加载字体失败，使用默认字体: {str(e)}")
                    font = ImageFont.load_default()
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
            
            if not out.isOpened():
                raise RuntimeError("无法创建视频文件")
                
            logger.info(f"开始生成视频，共{len(paragraphs)}个段落")
            
            # 为每个段落生成帧
            for i, paragraph in enumerate(paragraphs):
                frames = self._create_paragraph_frames(paragraph, font)
                for frame in frames:
                    out.write(frame)
                    
                if i % 10 == 0:
                    logger.info(f"已处理 {i+1}/{len(paragraphs)} 个段落")
            
            out.release()
            logger.info(f"视频生成完成: {output_path}")
            
        except Exception as e:
            logger.error(f"视频生成失败: {str(e)}")
            if 'out' in locals():
                out.release()
            raise

    def _split_text(self, text: str) -> List[str]:
        """将文本分割为适合显示的段落"""
        # 按句子分割
        sentences = re.split(r'[。！？.!?]+', text)
        paragraphs = []
        current_para = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_para + sentence) < 200:  # 每段约200字符
                current_para += sentence + "。"
            else:
                if current_para:
                    paragraphs.append(current_para)
                current_para = sentence + "。"
        
        if current_para:
            paragraphs.append(current_para)
            
        return paragraphs

    def _create_paragraph_frames(self, text: str, font: ImageFont.FreeTypeFont) -> List[np.ndarray]:
        """为段落创建视频帧"""
        frames = []
        
        # 计算文本在图像中的位置
        wrapped_lines = self._wrap_text(text, font)
        
        # 创建背景图像
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # 计算文本起始位置（垂直居中）
        total_height = len(wrapped_lines) * (self.font_size + self.line_spacing)
        start_y = (self.height - total_height) // 2
        
        # 绘制文本
        y = start_y
        for line in wrapped_lines:
            # 计算水平居中位置
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            
            draw.text((x, y), line, font=font, fill=self.text_color)
            y += self.font_size + self.line_spacing
        
        # 将PIL图像转换为OpenCV格式
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # 每段文字显示3秒
        frames_count = int(self.fps * 3)
        for _ in range(frames_count):
            frames.append(frame.copy())
            
        return frames

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont) -> List[str]:
        """文本换行处理"""
        max_width = self.width - 2 * self.margin
        
        # 使用textwrap进行换行
        wrapped_lines = textwrap.wrap(text, width=30)  # 中文字符宽度约为英文字符的2倍
        
        # 进一步处理每行，确保不超出边界
        lines = []
        for line in wrapped_lines:
            if self._get_text_width(line, font) <= max_width:
                lines.append(line)
            else:
                # 如果单行仍然太宽，强制分割
                words = list(line)
                current_line = ""
                for char in words:
                    test_line = current_line + char
                    if self._get_text_width(test_line, font) <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = char
                if current_line:
                    lines.append(current_line)
        
        return lines

    def _get_text_width(self, text: str, font: ImageFont.FreeTypeFont) -> int:
        """获取文本宽度"""
        try:
            # 使用PIL的textbbox方法
            img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]
        except:
            # 备用方法
            return len(text) * self.font_size

    def generate_from_directory(self, directory: str, output_path: str, font_path: str = None) -> None:
        """从目录中的多个文本文件生成视频"""
        try:
            if not os.path.exists(directory):
                raise FileNotFoundError(f"目录不存在: {directory}")
                
            text_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
            if not text_files:
                raise ValueError("目录中没有文本文件")
                
            text_files.sort()
            
            all_text = ""
            for text_file in text_files:
                file_path = os.path.join(directory, text_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            all_text += f"\n\n=== {text_file} ===\n\n{content}"
                except Exception as e:
                    logger.warning(f"读取文件失败: {text_file}, 错误: {str(e)}")
            
            if not all_text.strip():
                raise ValueError("所有文本文件都为空")
                
            self.generate_from_text(all_text, output_path, font_path)
            
        except Exception as e:
            logger.error(f"从目录生成视频失败: {str(e)}")
            raise
