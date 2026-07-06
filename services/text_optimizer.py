# -*- coding: utf-8 -*-
"""死算法 — 低级模型裸文本的确定性后处理优化。

低级模型只负责吐内容，格式/结构/去重全由这里的纯算法搞定。
"""

import re
from typing import List


def optimize_chapter_text(raw: str) -> str:
    """优化低级模型输出的章节裸文本。

    处理流程：
    1. 剥离代码块标记、XML 标签
    2. 确保章节标题格式统一
    3. 规范段落间距
    4. 清理无效字符
    5. 去重连续重复段落
    """
    text = raw.strip()

    # 1. 剥离 markdown 代码块
    text = re.sub(r'^```(?:markdown|text|plain)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    # 2. 剥离 XML/思考标签
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    text = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL)
    text = re.sub(r'<result>.*?</result>', '', text, flags=re.DOTALL)
    text = re.sub(r'<answer>.*?</answer>', '', text, flags=re.DOTALL)

    # 3. 确保章节标题格式
    #    将 "第一章"、"第1章"、"Chapter 1" 等统一为 "# 第X章 标题"
    text = _normalize_heading(text)

    # 4. 规范段落间距（段落间最多一个空行）
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 5. 删除重复的连续段落（3行以上完全相同的块）
    text = _dedup_paragraphs(text)

    # 6. 清理控制字符和乱码
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    return text.strip()


def strip_ai_prefix(text: str) -> str:
    """去掉模型常见的开场废话。

    比如 "好的，根据您的要求..."、"以下是第X章的内容："等。
    """
    patterns = [
        r'^(好的|好[的，]|嗯，|明白[了，]|让我|我来|根据).*?(?:内容[：:]|如下[：:]|：)\s*',
        r'^以下是第[一二三四五六七八九十\d]+章[的].*?[：:]\s*',
        r'^第[一二三四五六七八九十\d]+章[：:]\s*',
        r'^#{1,3}\s*第[一二三四五六七八九十\d]+章.*?\n',
    ]
    for p in patterns:
        text = re.sub(p, '', text, count=1)
    return text


def ensure_title(text: str, chapter_num: int, default_title: str = '') -> str:
    """确保章节开头有标题，没有则添加。"""
    first_line = text.split('\n')[0].strip()
    if re.match(r'^#{1,3}\s*第', first_line):
        return text
    title = default_title or f'第{chapter_num}章'
    return f'# {title}\n\n{text}'


def strip_suffix(text: str) -> str:
    """去掉模型结尾的废话。

    比如 "希望这个章节..."、"如果您满意..."等。
    """
    # 删除最后一段如果它看起来像 AI 客套话
    suffix_patterns = [
        r'\n\n希望[这我].*?[。！]?\s*$',
        r'\n\n如果[您你].*?[。！]?\s*$',
        r'\n\n请[告诉让我].*?[。！]?\s*$',
        r'\n\n如[有您].*?[。！]?\s*$',
        r'\n\n您可以.*?[。！]?\s*$',
    ]
    for p in suffix_patterns:
        text = re.sub(p, '', text)
    return text


# ── 内部工具 ──────────────────────────────────────────────

def _normalize_heading(text: str) -> str:
    """统一章节标题格式为 '# 第X章 标题'。"""
    # 各种格式的章节标题
    patterns = [
        (r'^第([一二三四五六七八九十\d零]+)章[：:\s]*(.*?)$', r'# 第\1章 \2'),
        (r'^Chapter\s+(\d+)[：:\s]*(.*?)$', r'# 第\1章 \2'),
    ]
    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pat, repl in patterns:
            match = re.match(pat, stripped)
            if match:
                lines[i] = re.sub(pat, repl, stripped)
                break
    return '\n'.join(lines)


def _dedup_paragraphs(text: str) -> str:
    """删除重复的段落块。"""
    paragraphs = re.split(r'\n\n+', text)
    seen: List[str] = []
    unique: List[str] = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # 只对 >= 3 行的段落做去重（短段落可能是对话/标题）
        lines = p.split('\n')
        if len(lines) >= 3 and p in seen:
            continue
        seen.append(p)
        unique.append(p)
    return '\n\n'.join(unique)
