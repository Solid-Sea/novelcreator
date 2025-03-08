# File: novel_generator.py
import os
import json
import time
import shutil
import zipfile
import argparse
import requests
import torch
from transformers import pipeline
from utils import ContentCleaner, logger, create_folder, get_progress
from video_generator import generate_video

class NovelGenerator:
    def __init__(self, args):
        self.args = args
        self.config = self._load_config()
        self.cleaner = ContentCleaner()
        
        if self.config['settings']['model_type'] == 'transformers':
            self.model = pipeline('text-generation', 
                                model=self.config['transformers']['model_name'],
                                device=self.config['transformers']['device'])
        else:
            self.model = None

    def _load_config(self):
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_novel(self, title):
        base_dir = os.path.join(self.config['paths']['novels_dir'], title)
        total_chaps = self._calculate_total_chapters()
        
        try:
            create_folder(base_dir)
            create_folder(os.path.join(base_dir, "chaps"))
            create_folder(os.path.join(base_dir, "tl"))

            progress = get_progress(title)
            if progress == 0:
                self._generate_outline(title, base_dir)
                self._generate_chapter_outlines(title, total_chaps, base_dir)

            self._generate_chapters(title, total_chaps, base_dir, progress)
            self._merge_chapters(title, base_dir)
            self._compress_output(title)
            
            if self.args.generate_video:
                generate_video(title)
            
            logger.info(f"小说《{title}》生成完成！")
            return True
            
        except Exception as e:
            logger.critical(f"生成失败: {str(e)}")
            return False

    def _merge_chapters(self, title, base_dir):
        output_path = os.path.join(self.config['paths']['output_dir'], f"{title}.txt")
        chap_dir = os.path.join(base_dir, "chaps")
        
        chapters = sorted(os.listdir(chap_dir), 
                        key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for chap in chapters:
                with open(os.path.join(chap_dir, chap), 'r') as infile:
                    outfile.write(f"第{chap.split('_')[1].split('.')[0]}章\n\n")
                    outfile.write(infile.read() + "\n\n")

    def _compress_output(self, title):
        source_dir = os.path.join(self.config['paths']['novels_dir'], title)
        output_path = os.path.join(self.config['paths']['output_dir'], f"{title}.zip")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), 
                              os.path.relpath(os.path.join(root, file), 
                                            os.path.join(source_dir, '..')))

    def _generate_content(self, prompt):
        if self.config['settings']['model_type'] == 'transformers':
            return self._generate_with_transformers(prompt)
        else:
            return self._generate_with_ollama(prompt)

    def _generate_with_transformers(self, prompt):
        response = self.model(
            prompt,
            max_length=4000,
            num_return_sequences=1,
            temperature=0.7,
            pad_token_id=self.model.tokenizer.eos_token_id
        )
        return response[0]['generated_text']

    def _generate_with_ollama(self, prompt):
        payload = {
            "model": self.config['ollama']['model'],
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        response = requests.post(
            self.config['ollama']['endpoint'],
            json=payload,
            timeout=self.config['settings']['timeout']
        )
        return response.json().get("response", "")

    def _generate_chapter_content(self, outline):
        content = self._generate_content(outline)
        cleaned = self.cleaner.clean(content)
        if len(cleaned) < 1800:
            raise ValueError("生成内容过短")
        return cleaned

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--model-type", choices=['ollama', 'transformers'])
    parser.add_argument("--generate-video", action='store_true')
    args = parser.parse_args()
    
    generator = NovelGenerator(args)
    generator.generate_novel(args.title)
