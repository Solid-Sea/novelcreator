import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip
from utils import logger

class VideoGenerator:
    def __init__(self):
        self.config = self._load_config()
        self.font = self._load_font()

    def generate_video(self, text_file: str, output_file: str):
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()

            # 分割文本为适合屏幕显示的行
            lines = self._split_text(text)
            
            # 生成滚动文本帧
            frames = self._generate_frames(lines)
            
            # 保存视频
            clip = ImageSequenceClip(frames, fps=24)
            clip.write_videofile(output_file, codec='libx264')
            
            logger.info(f"视频生成成功：{output_file}")
            return True
        except Exception as e:
            logger.error(f"视频生成失败：{str(e)}")
            return False

    def _split_text(self, text: str) -> list:
        max_chars = self.config['settings']['video']['resolution'][0] // (
            self.config['settings']['video']['font_size'] // 2)
        return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

    def _generate_frames(self, lines: list) -> list:
        width, height = map(int, self.config['settings']['video']['resolution'].split('x'))
        speed = self.config['settings']['video']['scroll_speed']
        frames = []
        
        # 计算总帧数
        total_frames = (len(lines) * height) // speed
        
        for frame_num in range(total_frames):
            img = Image.new('RGB', (width, height), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 计算当前显示位置
            y_pos = height - (frame_num * speed)
            
            # 绘制文本
            for i, line in enumerate(lines):
                draw.text(
                    (10, y_pos + i * self.font.size),
                    line,
                    font=self.font,
                    fill=(255, 255, 255))
                
            frames.append(np.array(img))
            
        return frames

    def _load_font(self):
        try:
            return ImageFont.truetype(
                self.config['settings']['video']['font'],
                self.config['settings']['video']['font_size'])
        except Exception as e:
            logger.error(f"加载字体失败：{str(e)}")
            raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入文本文件")
    parser.add_argument("--output", required=True, help="输出视频文件")
    args = parser.parse_args()

    generator = VideoGenerator()
    success = generator.generate_video(args.input, args.output)
    
    if success:
        print("视频生成成功！")
    else:
        print("视频生成失败")