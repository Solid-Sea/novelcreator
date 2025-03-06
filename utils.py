# -*- coding: utf-8 -*-
import os
import logging
from pathlib import Path
from tqdm import tqdm
import re
import yaml  # 添加缺失的导入

def clean_content(text):
    """去除AI思考标签"""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return os.linesep.join([line for line in text.splitlines() if line.strip()])

def setup_logger():
    logger = logging.getLogger('NovelGenerator')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('novel_gen.log', encoding='utf-8')
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

def create_folder(path):
    """安全创建目录"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"创建目录失败: {str(e).encode('utf-8')}")
        raise

def get_progress(book_title):
    """获取生成进度"""
    try:
        chap_dir = os.path.join("novels", book_title, "chaps")
        if not os.path.exists(chap_dir):
            return 0
        return len([f for f in os.listdir(chap_dir) if f.endswith(".txt")])
    except Exception as e:
        logger.error(f"获取进度失败: {str(e).encode('utf-8')}")
        return 0

def show_progress(current, total):
    """进度条显示"""
    return tqdm(
        total=total, 
        initial=current, 
        unit="章",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [已用:{elapsed}, 剩余:{remaining}]"
    )