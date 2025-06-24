# -*- coding: utf-8 -*-
# File: utils.py
import os
import logging
import re
import yaml
from pathlib import Path
from tqdm import tqdm

# 日志设置
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

# 内容清洗
def clean_content(text, blacklist=None):
    """内容清洗"""
    # 删除AI思考标签
    text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)
    
    if blacklist:
        # 范围删除
        for pattern in blacklist.get('ranges', []):
            text = re.sub(pattern + '\s*', '', text, flags=re.DOTALL)
        
        # 全字匹配删除
        for word in blacklist.get('exact', []):
            text = re.sub(r'(?<!\w)' + re.escape(word) + r'(?!\w)', '[已屏蔽]', text)
    
    # 清理空行
    return os.linesep.join([line for line in text.splitlines() if line.strip()])

# 加载违禁词列表
def load_blacklist():
    """加载违禁词列表"""
    try:
        # 构建黑名单文件路径
        blacklist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'blacklist.yaml')
        if not os.path.exists(blacklist_path):
            logging.warning(f"黑名单文件未找到: {blacklist_path}")
            return {'exact': [], 'ranges': []}
            
        with open(blacklist_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {'exact': [], 'ranges': []}
    except Exception as e:
        logging.warning(f"加载违禁词列表失败: {str(e)}")
        return {'exact': [], 'ranges': []}

# 合并章节
def merge_chapters(novel_dir):
    """合并所有章节为完整小说"""
    chap_dir = os.path.join(novel_dir, "chaps")
    output_path = os.path.join(novel_dir, "full_novel.txt")
    
    chapters = sorted(
        [f for f in os.listdir(chap_dir) if f.endswith(".txt")],
        key=lambda x: int(x.split('_')[1].split('.')[0])
    )
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for filename in chapters:
            with open(os.path.join(chap_dir, filename), 'r', encoding='utf-8') as infile:
                outfile.write(f"=== 第{filename.split('_')[1].split('.')[0]}章 ===\n\n")
                outfile.write(infile.read())
                outfile.write("\n\n")
    
    logger.info(f"小说合并完成：{output_path}")

# 目录操作
def create_folder(path):
    """安全创建目录"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        raise

# 进度管理
def get_progress(book_title):
    """获取生成进度"""
    try:
        chap_dir = os.path.join("novels", book_title, "chaps")
        if not os.path.exists(chap_dir):
            return 0
        return len([f for f in os.listdir(chap_dir) if f.endswith(".txt")])
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        return 0

# 进度条显示
def show_progress(current: int, total: int) -> tqdm:
    """
    生成并返回进度条对象

    Args:
        current (int): 当前已完成的章节数
        total (int): 总章节数

    Returns:
        tqdm: 配置好的进度条对象
    """
    return tqdm(
        total=total, 
        initial=current,
        unit="章",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [已用:{elapsed}, 剩余:{remaining}]"
    )



import os
import yaml
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """加载配置文件
    
    Returns:
        Dict[str, Any]: 配置字典
    
    Raises:
        FileNotFoundError: 当配置文件不存在时
        ValueError: 当配置文件格式错误或缺少必要配置项时
        RuntimeError: 当其他错误发生时
    """
    try:
        # 更新配置文件路径
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            
        required_sections = {'ollama', 'paths', 'settings'}
        missing = required_sections - config.keys()
        if missing:
            raise ValueError(f"缺失必要配置项: {', '.join(missing)}")
            
        return config
        
    except yaml.YAMLError as e:
        raise ValueError(f"配置文件解析错误: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"配置加载失败: {str(e)}")
