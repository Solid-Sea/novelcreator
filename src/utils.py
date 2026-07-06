# -*- coding: utf-8 -*-
"""工具函数：配置加载、文件操作、日志、进度条。"""

import logging
import os
import re
import yaml
from pathlib import Path
from tqdm import tqdm


# ── 日志 ──────────────────────────────────────────────────

def setup_logger():
    logger = logging.getLogger('NovelGenerator')
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler('novel_gen.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    ))
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logger()


# ── 配置 ──────────────────────────────────────────────────

def load_config() -> dict:
    """加载配置文件。"""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'config', 'config.yaml',
    )
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'配置文件不存在: {config_path}')

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def load_blacklist() -> dict:
    """加载黑名单。"""
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'config', 'blacklist.yaml',
    )
    if not os.path.exists(path):
        return {'exact': [], 'ranges': []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {'exact': [], 'ranges': []}
    except Exception:
        return {'exact': [], 'ranges': []}


# ── 文件操作 ──────────────────────────────────────────────

def create_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def merge_chapters(novel_dir, blacklist=None):
    """合并章节为完整小说。"""
    chap_dir = os.path.join(novel_dir, 'chaps')
    if not os.path.exists(chap_dir):
        logger.error(f'章节目录不存在: {chap_dir}')
        return

    output_path = os.path.join(novel_dir, 'full_novel.txt')
    chapters = sorted(
        [f for f in os.listdir(chap_dir) if f.endswith('.txt')],
        key=lambda x: int(x.split('_')[1].split('.')[0])
        if len(x.split('_')) > 1 and x.split('_')[1].split('.')[0].isdigit()
        else 0,
    )

    if not chapters:
        logger.warning(f'未找到章节文件: {chap_dir}')
        return

    # 简单黑名单过滤（不依赖 services/）

    with open(output_path, 'w', encoding='utf-8') as out:
        for filename in chapters:
            file_path = os.path.join(chap_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as inf:
                    num = filename.split('_')[1].split('.')[0]
                    out.write(f'=== 第{num}章 ===\n\n')
                    content = inf.read()
                    # 黑名单过滤（不要 LLM 清洗，太慢）
                    if blacklist:
                        for pattern in blacklist.get('ranges', []):
                            content = re.sub(pattern, '', content, flags=re.DOTALL)
                        for word in blacklist.get('exact', []):
                            content = re.sub(re.escape(word), '[已屏蔽]', content)
                    out.write(content)
                    out.write('\n\n')
            except Exception as e:
                logger.error(f'读取章节文件失败: {file_path}, {e}')

    logger.info(f'小说合并完成: {output_path}')


# ── 进度 ──────────────────────────────────────────────────

def get_progress(book_title):
    chap_dir = os.path.join('novels', book_title, 'chaps')
    if not os.path.exists(chap_dir):
        return 0
    return len([f for f in os.listdir(chap_dir) if f.endswith('.txt')])


def show_progress(current: int, total: int) -> tqdm:
    return tqdm(
        total=total,
        initial=current,
        unit='章',
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
    )
