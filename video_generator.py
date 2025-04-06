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

    def generate_video(self, text_file: str, output_file: str) -> bool:
        """
        生成滚动文本视频
        
        Args:
            text_file: 输入文本文件路径
            output_file: 输出视频文件路径
            
        Returns:
            bool: 生成是否成功
        """
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()

            lines = self._split_text(text)
            frames = self._generate_frames(lines)
            
            clip = ImageSequenceClip(frames, fps=self.fps)
            clip.write_videofile(output_file, codec=self.codec)
            
            logger.info(f"视频生成成功：{output_file}")
            return True
        except IOError as e:
            logger.error(f"文件操作失败：{str(e)}")
        except (ValueError, AttributeError) as e:
            logger.error(f"配置参数错误：{str(e)}")
        except Exception as e:
            logger.error(f"未知错误：{str(e)}")
        return False

    def _split_text(self, text: str) -> list[str]:
        """
        将长文本分割为适合屏幕显示的行
        
        Args:
            text: 输入文本
            
        Returns:
            分割后的文本行列表
        """
        char_per_line = self.width // (self.font_size // 2)
        # 使用生成器表达式减少内存占用
        return list(text[i:i+char_per_line] for i in range(0, len(text), char_per_line))

    def _generate_frames(self, lines: list[str]) -> list[np.ndarray]:
        """
        生成滚动文本的视频帧序列
        
        Args:
            lines: 分割后的文本行列表
            
        Returns:
            包含所有视频帧的numpy数组列表
        """
        # 预分配内存
        total_frames = (len(lines) * self.height) // self.scroll_speed
        frames = [None] * total_frames
        
        # 预创建图像对象
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        for frame_num in range(total_frames):
            # 复用图像对象
            img.paste((0, 0, 0), (0, 0, self.width, self.height))
            y_pos = self.height - (frame_num * self.scroll_speed)
            
            for i, line in enumerate(lines):
                draw.text(
                    (10, y_pos + i * self.font_size),
                    line,
                    font=self.font,
                    fill=(255, 255, 255))
            
            frames[frame_num] = np.array(img)
        
        return frames

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """
        加载字体文件
        
        Returns:
            FreeTypeFont: 加载的字体对象
        
        Raises:
            FontNotFound: 字体加载失败时抛出
        """
        try:
            return ImageFont.truetype(
                self.config['settings']['video']['font'],
                self.font_size)
        except Exception as e:
            logger.error(f"字体加载失败：{str(e)}")
            raise RuntimeError(f"字体加载失败：{str(e)}") from e

    def __init__(self) -> None:
        from model_handler import ModelHandler
        self.model_handler = ModelHandler()
        self.config = self.model_handler.config
        self._parse_video_params()
        self.font = self._load_font()

    def _parse_video_params(self):
        self.video_config = VideoConfig(self.config)

class VideoConfig:
    def __init__(self, config: dict):
        self._load_config(config)

    def _load_config(self, config: dict) -> None:
        """
        加载并验证视频配置参数
        
        Args:
            config: 从config.yaml加载的配置字典
            
        Raises:
            KeyError: 当缺少必需配置项时
            ValueError: 当配置值无效时
        """
        try:
            video_settings = config['settings']['video']
            
            # 解析分辨率
            self.resolution: str = video_settings['resolution']
            try:
                self.width, self.height = map(int, self.resolution.split('x'))
            except ValueError:
                raise ValueError(f"无效的分辨率格式: {self.resolution}, 应为'宽度x高度'格式")
                
            # 视频参数
            self.font_size: int = video_settings.get('font_size', 24)
            self.scroll_speed: int = video_settings.get('scroll_speed', 2)
            self.fps: int = video_settings.get('fps', 24)
            self.codec: str = video_settings.get('codec', 'libx264')
            
            # 必需参数检查
            self.font_file: str = video_settings['font']
            if not os.path.exists(self.font_file):
                raise FileNotFoundError(f"字体文件不存在: {self.font_file}")
                
        except KeyError as e:
            raise KeyError(f"缺少必需的视频配置项: {str(e)}")

def main() -> None:
    """
    命令行入口函数
    
    功能：
    - 解析输入输出路径参数
    - 初始化视频生成器
    - 执行视频生成流程
    - 输出最终状态码
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='文本视频生成器',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", 
                      required=True,
                      type=str,
                      help="输入文本文件路径")
    parser.add_argument("--output",
                      required=True,
                      type=str,
                      help="输出视频文件路径")
    args = parser.parse_args()

    try:
        generator = VideoGenerator()
        success = generator.generate_video(args.input, args.output)
        exit_code = 0 if success else 1
        logger.info(f"程序退出代码: {exit_code}")
    except Exception as e:
        logger.critical(f"程序异常终止: {str(e)}")
        exit_code = 2
    finally:
        exit(exit_code)

if __name__ == "__main__":
    main()