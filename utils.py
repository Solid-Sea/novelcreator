# -*- coding: utf-8 -*-
import os
import logging
from pathlib import Path
from tqdm import tqdm
import re
from typing import Any, Optional
from llama_cpp_handler import LlamaCppHandler

def load_model_handler(config: dict[str, Any]) -> Optional[LlamaCppHandler]:
    """加载模型处理器"""
    if not config.get('llama'):
        return None
    return LlamaCppHandler(**{
        'model_path': config['llama']['model_path'],
        'n_ctx': config['llama'].get('n_ctx', 2048),
        'n_gpu_layers': config['llama'].get('n_gpu_layers', -1)
    })


def clean_content(text: str) -> str:
    """清理生成内容
    
    Args:
        text: 原始文本
    
    Returns:
        清理后的文本
    """
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return os.linesep.join([line for line in text.splitlines() if line.strip()])

logger = logging.getLogger('NovelGenerator')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.FileHandler('novel_gen.log', encoding='utf-8'))
logger.addHandler(logging.StreamHandler())

def create_folder(path: str) -> None:
    """安全创建目录
    
    Args:
        path: 要创建的目录路径
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        raise

def get_progress(book_title: str) -> int:
    """获取生成进度
    
    Args:
        book_title: 小说标题
    
    Returns:
        已生成的章节数量
    """
    try:
        chap_dir = os.path.join("novels", book_title, "chaps")
        if not os.path.exists(chap_dir):
            return 0
        return len([f for f in os.listdir(chap_dir) if f.endswith(".txt")])
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        return 0

def show_progress(current: int, total: int) -> tqdm:
    """显示进度条
    
    Args:
        current: 当前进度
        total: 总进度
    
    Returns:
        进度条对象
    """
    return tqdm(
        total=total, 
        initial=current, 
        unit="章",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [已用:{elapsed}, 剩余:{remaining}]"
    )