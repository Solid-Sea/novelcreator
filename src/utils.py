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
    # 防重复添加handler
    if logger.handlers:
        return logger

    # 默认INFO，允许外部切换到DEBUG（例如--verbose）
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler('novel_gen.log', encoding='utf-8')
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# 内容清洗
def clean_content(text, blacklist=None):
    """内容清洗"""
    if not isinstance(text, str):
        text = str(text)
    
    # 删除AI思考标签（多种格式）
    text = re.sub(r'<tool_call>.*?</tool_call>[\s\r\n]*', '', text, flags=re.DOTALL)
    text = re.sub(r'好的，.*?要求.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，.*?需求。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，.*?预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'然后，.*?一致。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，.*?要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，.*?要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'请补充内容：.*?$', '', text, flags=re.DOTALL)
    text = re.sub(r'让我.*?扩写.*?内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我需要.*?扩写.*?内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节中，.*?然后.*?最后.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望.*?扩展内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩写过程中，.*?最后.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'期待您的指示！', '', text)
    text = re.sub(r'请您提供.*?版本。', '', text, flags=re.DOTALL)
    text = re.sub(r'好，我现在需要帮用户扩写一个小说章节.*?如果需要调整或补充，请随时告诉我。', '', text, flags=re.DOTALL)
    text = re.sub(r'如果您有其他想法，可以随时提出，我会进行调整。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩展内容能满足你的要求。如果需要调整或补充，请随时告诉我。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩展符合您的预期。如果需要更多细节或调整，请随时告诉我。', '', text, flags=re.DOTALL)
    
    # 删除单独的AI标签
    text = re.sub(r'<tool_call>[\s\r\n]*', '', text, flags=re.DOTALL)
    text = re.sub(r'</tool_call>[\s\r\n]*', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我应该考虑如何.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，.*?可以更细致一些。', '', text, flags=re.DOTALL)
    text = re.sub(r'对话部分也可以增加，.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，我需要确保.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，结尾部分可以加入一些.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，我需要通过.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，.*?自然流畅。', '', text, flags=re.DOTALL)
    
    # 删除重复的段落标记
    text = re.sub(r'---+', '---', text)
    text = re.sub(r'===+', '===', text)
    
    # 删除多余的说明文字
    text = re.sub(r'当前章节结尾：.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'要求：.*?使用中文写作', '', text, flags=re.DOTALL)
    text = re.sub(r'请补充内容：', '', text)
    text = re.sub(r'【补充】', '', text)
    text = re.sub(r'mercy', '仁慈', text)
    text = re.sub(r'escape', '逃脱', text)
    text = re.sub(r'whispered', '低声说', text)
    
    # 删除章节开头的分析和说明
    text = re.sub(r'第[一二三四五六七八九十]+章的主题是.*?过程。', '', text, flags=re.DOTALL)
    text = re.sub(r'第[一二三四五六七八九十]+章的主题是.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户明确要求.*?标题。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户明确要求.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这意味着我需要.*?初步冲突。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我会确定.*?推动情节发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩展.*?。', '', text, flags=re.DOTALL)
    
    if blacklist:
        # 范围删除
        for pattern in blacklist.get('ranges', []):
            text = re.sub(pattern + r'\s*', '', text, flags=re.DOTALL)
        
        # 全字匹配删除
        for word in blacklist.get('exact', []):
            text = re.sub(r'(?<!\w)' + re.escape(word) + r'(?!\w)', '[已屏蔽]', text)
    
    # 清理空行和多余空白，但保留段落分隔
    lines = text.splitlines()
    cleaned_lines = []
    seen_lines = set()
    
    for line in lines:
        stripped_line = line.strip()
        # 保留空行（段落分隔）
        if not stripped_line:
            # 只添加一个空行，避免连续多个空行
            if not cleaned_lines or cleaned_lines[-1] != '':
                cleaned_lines.append('')
            continue
            
        # 去除重复行
        if stripped_line not in seen_lines:
            seen_lines.add(stripped_line)
            cleaned_lines.append(stripped_line)
    
    # 移除开头和结尾的空行
    while cleaned_lines and cleaned_lines[0] == '':
        cleaned_lines.pop(0)
    while cleaned_lines and cleaned_lines[-1] == '':
        cleaned_lines.pop()
    
    # 使用统一的换行符
    return '\n'.join(cleaned_lines)

# 加载违禁词列表
def load_blacklist():
    """加载违禁词列表"""
    try:
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
def merge_chapters(novel_dir, blacklist=None):
    """合并所有章节为完整小说"""
    try:
        chap_dir = os.path.join(novel_dir, "chaps")
        if not os.path.exists(chap_dir):
            logger.error(f"章节目录不存在: {chap_dir}")
            return
            
        output_path = os.path.join(novel_dir, "full_novel.txt")
        
        chapters = sorted(
            [f for f in os.listdir(chap_dir) if f.endswith(".txt")],
            key=lambda x: int(x.split('_')[1].split('.')[0]) if len(x.split('_')) > 1 and x.split('_')[1].split('.')[0].isdigit() else 0
        )
        
        if not chapters:
            logger.warning(f"未找到任何章节文件: {chap_dir}")
            return
            
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for filename in chapters:
                file_path = os.path.join(chap_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        chapter_num = filename.split('_')[1].split('.')[0] if len(filename.split('_')) > 1 else '未知'
                        outfile.write(f"=== 第{chapter_num}章 ===\n\n")
                        content = infile.read().strip()
                        # 清理内容
                        cleaned_content = clean_content(content, blacklist)
                        outfile.write(cleaned_content)
                        outfile.write("\n\n")
                except Exception as e:
                    logger.error(f"读取章节文件失败: {file_path}, 错误: {str(e)}")
        
        logger.info(f"小说合并完成：{output_path}")
        
    except Exception as e:
        logger.error(f"合并章节失败: {str(e)}")

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

# 加载配置文件
def load_config() -> dict:
    """加载配置文件
    
    Returns:
        dict: 配置字典
    
    Raises:
        FileNotFoundError: 当配置文件不存在时
        ValueError: 当配置文件格式错误或缺少必要配置项时
        RuntimeError: 当其他错误发生时
    """
    try:
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
