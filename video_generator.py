# File: video_generator.py
import os
import textwrap
from moviepy.editor import *
from moviepy.config import change_settings
import yaml

def generate_video(title):
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    text_path = os.path.join(config['paths']['output_dir'], f"{title}.txt")
    with open(text_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    wrapped_text = textwrap.fill(full_text, width=40)
    
    txt_clip = TextClip(wrapped_text, 
                       font=config['video']['font'],
                       fontsize=config['video']['font_size'],
                       color='white')
    
    txt_clip = txt_clip.set_position(lambda t: ('center', -t*config['video']['scroll_speed']))
    video_duration = txt_clip.h / config['video']['scroll_speed']
    
    video = CompositeVideoClip([txt_clip], 
                              size=config['video']['resolution']).set_duration(video_duration)
    
    if os.path.exists(config['video']['bgm']):
        audio = AudioFileClip(config['video']['bgm']).subclip(0, video_duration)
        video = video.set_audio(audio)
    
    output_path = os.path.join(config['paths']['output_dir'], f"{title}.mp4")
    video.write_videofile(output_path, fps=24)
    
    return output_path
