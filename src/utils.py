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
    text = re.sub(r'思考过程开始.*?思考过程结束[\s\r\n]*', '', text, flags=re.DOTALL)
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
    text = re.sub(r'首先，我需要考虑如何.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，.*?可以更细致一些。', '', text, flags=re.DOTALL)
    text = re.sub(r'对话部分也可以增加，.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，我需要确保.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，结尾部分可以加入一些.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，我需要通过.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，.*?自然流畅。', '', text, flags=re.DOTALL)
    
    # 删除以"首先，我需要"、"接下来，我需要"、"最后，我需要"开头的分析内容
    text = re.sub(r'首先，我需要.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我需要.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'让我.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容模式
    text = re.sub(r'首先，这.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'然后，我需要.*?。', '', text, flags=re.DOTALL)
    
    # 删除用户交互相关的AI分析内容
    text = re.sub(r'好的，请您提供需要处理的文本，我会为您清理掉所有AI生成的分析内容，只保留小说正文。', '', text, flags=re.DOTALL)
    text = re.sub(r'请提供需要处理的文本。', '', text, flags=re.DOTALL)
    text = re.sub(r'作为专业的小说编辑，你的任务是从以下文本中删除所有AI生成的分析内容，只保留小说正文。', '', text, flags=re.DOTALL)
    text = re.sub(r'我的任务是识别并删除这些分析内容，只保留小说正文。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要明确什么是AI生成的分析内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'通常，这包括对需求的分析、结构的理解、扩展重点等。', '', text, flags=re.DOTALL)
    text = re.sub(r'而正文则是故事本身，包含情节、对话和人物描写等内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'我会逐段检查文本，判断每一部分是否属于分析内容还是正文。', '', text, flags=re.DOTALL)
    text = re.sub(r'在确认哪些是需要保留的内容时，我会寻找明显的故事情节或人物互动部分。', '', text, flags=re.DOTALL)
    text = re.sub(r'完成识别后，我将删除所有分析性内容，只保留小说正文，并确保格式不变，不添加任何额外信息。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我会输出清理后的正文，确保符合用户的要求，没有遗漏或错误。', '', text, flags=re.DOTALL)
    text = re.sub(r'总结一下，我的步骤是：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样就能满足用户的需求，提供一个干净的小说正文。', '', text, flags=re.DOTALL)
    
    # 删除重复的提示和说明
    text = re.sub(r'用户明确要求.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这意味着我需要.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我会确定.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我要围绕主角.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'关键是要有生动的场景和对话，让读者感受到紧张和悬念。', '', text, flags=re.DOTALL)
    
    # 删除更多的分析内容
    text = re.sub(r'好，我现在需要帮用户生成小说.*?。根据用户的请求，我得先仔细分析他的需求。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，用户提供了一个详细的大纲，分为三个章节。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，检查字数是否达到要求，并确保整体流畅，没有重复的内容。这样，扩写后的内容不仅丰富了故事，还深化了人物形象和主题。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让内容更加自然连贯，我会先分析', '', text, flags=re.DOTALL)
    
    # 删除写作指导和扩展说明
    text = re.sub(r'在写作时，我需要详细描写场景和对话，使情节生动有趣。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作时，我需要详细描写场景和对话，使情节生动有趣。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我会.*?。然后.*?。接着.*?。最后.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作过程中，我要注意.*?。同时，加入一些.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过这些思考，我可以.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，不要重复已有的内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让内容更加丰富，我会先列出一些具体的扩展点：', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更完整，我会先列出一些基本的情节安排。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 章节概要', '', text, flags=re.DOTALL)
    text = re.sub(r'### 故事梗概', '', text, flags=re.DOTALL)
    text = re.sub(r'### 世界观设定', '', text, flags=re.DOTALL)
    text = re.sub(r'### 详细情节安排', '', text, flags=re.DOTALL)
    text = re.sub(r'### 详细情节设计', '', text, flags=re.DOTALL)
    text = re.sub(r'### 扩展问题框架', '', text, flags=re.DOTALL)
    text = re.sub(r'### 补充内容概要', '', text, flags=re.DOTALL)
    text = re.sub(r'### 详细扩展内容', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*.*?\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*.*?\*\*：', '', text, flags=re.DOTALL)
    text = re.sub(r'重点展现.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我们将重点描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段将重点描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段主要描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'请您看看以下内容是否符合您的预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个故事.*?能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩展内容能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写内容能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个故事片段能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个故事开头能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩展.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望以上内容符合您的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'---+', '', text, flags=re.DOTALL)
    
    # 删除扩展说明和写作提示
    text = re.sub(r'\*\*写作提示\*\*：', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*扩展内容：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*新增细节描写：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*增加对话内容：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*丰富内心独白：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*自然融入扩展：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*标题：.*?\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*正文：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*尾声：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*扩展说明：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'【补充】', '', text, flags=re.DOTALL)
    text = re.sub(r'【补充内容】', '', text, flags=re.DOTALL)
    
    # 删除章节开头的分析内容
    text = re.sub(r'为了让故事更加生动，我会先列出一些基本的问题来理清思路。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让内容更加丰富完整，我会先列出一些补充的情节脉络。', '', text, flags=re.DOTALL)
    text = re.sub(r'测试学院是挑选未来领导者的场所。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作时，我需要详细描写场景和对话，使情节生动有趣。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我会.*?。然后.*?。接着.*?。最后.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作过程中，我要注意.*?。同时，加入一些.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过这些思考，我可以.*?。', '', text, flags=re.DOTALL)
    
    # 删除章节结尾的分析内容
    text = re.sub(r'\*\*接下来故事可能会沿着这些方向发展\*\*：', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*结尾\*\*：', '', text, flags=re.DOTALL)
    text = re.sub(r'当艾琳离开测试场时，天空依旧阴沉。她没有回头，也没有思考未来的方向。她知道，自己已经站在了一个新的起点上，而这场"最终测试"，才刚刚拉开序幕。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望以上内容符合您的要求。', '', text, flags=re.DOTALL)
    
    # 删除章节中的分析标记和说明
    text = re.sub(r'\*\*标题：.*?\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*正文：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*尾声：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*扩展内容：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*扩展说明：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*新增细节描写：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*增加对话内容：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*丰富内心独白：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*自然融入扩展：\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的分析内容标记
    text = re.sub(r'### 章节内容概要', '', text, flags=re.DOTALL)
    text = re.sub(r'### 补充内容概要', '', text, flags=re.DOTALL)
    text = re.sub(r'### 详细扩展内容', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来通过这些情节展现她的内心世界，并为后续发展埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，要确保扩展的内容与原故事主题一致，即艾琳在压力下的成长和选择。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我会逐步分析每个部分，寻找可以扩展的点，并添加必要的细节和对话，使章节更加丰满。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更丰富，我会先列出一些基本的情节发展脉络。', '', text, flags=re.DOTALL)
    text = re.sub(r'艾琳是其中一个具有特殊天赋的学生，而伊恩教授掌握着重要的秘密实验。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来', '', text, flags=re.DOTALL)
    
    # 删除重复的段落（完全相同的段落）
    lines = text.split('\n')
    cleaned_lines = []
    seen_lines = set()
    seen_paragraphs = set()
    
    current_paragraph = []
    for line in lines:
        stripped_line = line.strip()
        # 如果是空行，表示段落结束
        if not stripped_line:
            if current_paragraph:
                # 检查整个段落是否重复
                paragraph_text = '\n'.join(current_paragraph).strip()
                if paragraph_text and paragraph_text not in seen_paragraphs:
                    # 如果段落不重复，添加到结果中
                    cleaned_lines.extend(current_paragraph)
                    cleaned_lines.append('')  # 添加空行分隔
                    seen_paragraphs.add(paragraph_text)
                current_paragraph = []
            elif not cleaned_lines or cleaned_lines[-1] != '':
                # 只添加一个空行，避免连续多个空行
                cleaned_lines.append('')
        else:
            # 收集段落行
            current_paragraph.append(line)
    
    # 处理最后一个段落
    if current_paragraph:
        paragraph_text = '\n'.join(current_paragraph).strip()
        if paragraph_text and paragraph_text not in seen_paragraphs:
            cleaned_lines.extend(current_paragraph)
            seen_paragraphs.add(paragraph_text)
    
    # 移除开头和结尾的空行
    while cleaned_lines and cleaned_lines[0] == '':
        cleaned_lines.pop(0)
    while cleaned_lines and cleaned_lines[-1] == '':
        cleaned_lines.pop()
    
    # 清理多余的空行（最多保留两个连续空行）
    text = re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned_lines))
    
    # 删除更多的AI分析内容
    text = re.sub(r'这意味着我要在现有基础上.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我需要分析当前章节.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'主要人物有.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'他们之间似乎有些紧张的关系.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'比如，.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'或许可以增加一些回忆片段.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，加入更多的环境描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'内心独白能很好地展示角色的情感变化.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，考虑到.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展时，我需要确保.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'可以通过逐步揭示的方式来增加细节.*?。', '', text, flags=re.DOTALL)
    
    
    # 删除更多的AI分析内容
    text = re.sub(r'为了让故事更吸引人，我会先列出一些基本的情节安排。请您看看以下内容是否符合您的预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 世界观设定.*?### 章节概要', '', text, flags=re.DOTALL)
    text = re.sub(r'### 章节概要.*?现在让我们聚焦于', '', text, flags=re.DOTALL)
    text = re.sub(r'现在让我们聚焦于.*?过程。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来的故事可能会沿着这些方向发展：.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'嗯，用户希望我扩写小说章节的内容，增加大约.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我需要保持原有情节的连贯性，不能偏离主线。', '', text, flags=re.DOTALL)
    text = re.sub(r'然后，用户要求增加细节描写、对话或内心独白，以及自然融入扩展内容，使用中文写作，且不重复已有内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节已经涵盖了.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了增加内容，我可以从以下几个方面入手：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，在数据中心的部分，可以加入更多关于代码重组的画面.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'此外，还可以增加一些回忆片段.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，在扩展过程中要注意语言的流畅性和自然性.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'请看扩写后的内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'好的，我现在需要帮助用户扩写小说章节，增加大约.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我要仔细阅读当前的内容，理解主要情节和人物关系。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要考虑如何扩展这些方面。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，用户提到可以增加回忆片段.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，我需要注意语言的流畅性和自然性.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'总结一下，我需要从环境描写、角色心理活动、对话扩展、动作描写和回忆片段几个方面入手.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'好，我需要为小说.*?增加.*?个字符。', '', text, flags=re.DOTALL)
    text = re.sub(r'他们想要增加与主线相关的情节或细节，可以是角色的回忆、背景故事或后续发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'在风格上，需要保持紧张和神秘的感觉，符合小说的整体氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'因此，补充的内容应该包含一些悬念和暗示，让读者感到好奇。', '', text, flags=re.DOTALL)
    text = re.sub(r'可能需要分成几个段落，分别添加回忆、实验室细节以及后续发展，以丰富故事层次。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'好吧，用户希望我扩写小说章节，增加大约.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更加丰满，我会先列出一些基本的问题框架。请您看看以下内容是否符合您的预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 扩展问题框架.*?###', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'为了让故事更加丰富生动，我会先列出一些基本的设定。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来我们将重点描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我要确保扩展后的内容保持原有情节的连贯性，不能偏离主线。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，用户要求增加细节描写和内心独白。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，用户提到不要重复已有的内容，所以我要避免重复描述已经出现的元素。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，我还要注意自然融入新内容，不让新增的部分显得突兀。', '', text, flags=re.DOTALL)
    text = re.sub(r'如果需要更多细节或调整，请随时告诉我。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我要分析当前章节的结构和内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要找出可以扩展的地方。', '', text, flags=re.DOTALL)
    text = re.sub(r'然后，我要考虑如何自然地融入扩展内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'我还需要确保语言流畅，避免重复已有的内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我会检查整个扩写部分是否与原有情节连贯，并且符合用户的要求，确保没有遗漏任何关键点。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，用户的章节内容是.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户的要求有几个关键点：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 章节扩展大纲.*?###', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来是具体扩写内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写内容能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更加完整和引人入胜，我会先列出一些基本的情节安排。请您看看以下内容是否符合您的预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 故事梗概.*?###', '', text, flags=re.DOTALL)
    text = re.sub(r'这段内容将展现这个神秘组织的真实目的，为后续剧情埋下伏笔。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'用户已经提供了详细的大纲，并且希望我按照大纲中的第一章节进行创作。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我会回顾一下大纲的第一章节内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要根据这些内容，创作第一章的具体情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 第一章：命运的转折.*?###', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我将根据上述大纲，展开具体的故事情节，加入更多的细节描写和对话，使这一章更加生动和吸引人。', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*写作提示\*\*：', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*场景描写\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*人物互动\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*悬念设置\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我可以开始撰写第一章的具体内容了。', '', text, flags=re.DOTALL)
    text = re.sub(r'好，我现在需要帮用户扩写小说章节，增加大约.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户已经提供了当前的章节内容和一些要求，我得仔细分析一下。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我要理解现有的情节结构。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户的要求包括保持连贯性、增加细节描写、对话或内心独白，自然融入扩展内容，并且使用中文。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我会考虑如何扩展每个部分。', '', text, flags=re.DOTALL)
    text = re.sub(r'然后，当程野出现时，我可以详细描写他的外貌和动作，比如他黑色夹克的细节，脸部表情的变化，以及他冲过来的动作，增加紧张感。', '', text, flags=re.DOTALL)
    text = re.sub(r'此外，两人的对话可以更丰富，加入更多内心独白，展示叶小夏的好奇和不安，以及程野的复杂情绪。', '', text, flags=re.DOTALL)
    text = re.sub(r'在回家的路上，我可以描绘周围的环境，增强场景的真实感，比如路灯、街道的声音，以及纸条上的符号细节，让读者更有代入感。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，当程野再次出现时，可以详细描写他的举止变化，比如敲门的方式、眼神的变化，增加悬疑氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'在对话展开的部分，可以加入更多关于纸条的背景信息，或者两人之间的紧张关系，进一步推动情节发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'悬念设置部分，我需要增强那种无形的压力感，比如通过环境描写或心理活动来表现叶小夏和程野的恐惧。', '', text, flags=re.DOTALL)
    text = re.sub(r'在高潮与结尾部分，可以详细描写那个戴面具男人的外貌和氛围，让读者感受到威胁的迫近。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我要确保整个扩写过程流畅自然，不重复已有内容，并且保持原有的悬疑和恐怖基调。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'### 故事梗概.*?###', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段主要描写.*?过程。', '', text, flags=re.DOTALL)
    text = re.sub(r'他们希望增加.*?个字符，也就是大约.*?字左右的内容，以保持章节的连贯性和紧张氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'补充的内容应该与主线相关，可能是角色回忆、背景故事或后续发展的铺垫。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前结尾已经很紧张，王小明发现台钟停在1985年，并且房间出现了一张诡异照片。这里的关键点是时间错乱和神秘照片。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户提到的三个发展方向中，时间错乱可能与张奶奶有关，暗示她有不寻常的往事；神秘照片预示更多超自然事件。', '', text, flags=re.DOTALL)
    text = re.sub(r'我需要思考如何在这部分添加细节，既符合当前紧张氛围，又为后续情节埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，王小明在调整台钟时的手感异常，或者照片上的女人名字与张奶奶有关联，增加悬念。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到用户希望保持风格一致，补充的内容应该简短而有力，避免冗长。', '', text, flags=re.DOTALL)
    text = re.sub(r'可能添加一个细节，比如王小明调整台钟时感觉指节咔咔作响，暗示时间的凝固；或者照片上的女人名字与张奶奶相关，引发读者的好奇心。', '', text, flags=re.DOTALL)
    text = re.sub(r'最终，我决定在台钟细节上增加一些描述，让读者感受到时间的诡异，并且为后续发展埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样既补充了内容，又保持了紧张和神秘感。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'通过回忆，揭示林小曼与命运之书的关联，增加角色深度和故事层次。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来故事可能会沿着这些方向发展：', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘香料\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*青铜戒指\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*命运之网\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个故事片段能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'我需要考虑如何扩展这个章节。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，可以考虑加入林小曼的回忆，解释她为何会进入库房，以及她对这本书的感受。', '', text, flags=re.DOTALL)
    text = re.sub(r'其次，可以详细描述她触摸青铜戒指时发生的异变，比如镜子出现的过程，以及她看到自己苍白的脸色和身后人们的疑惑表情。', '', text, flags=re.DOTALL)
    text = re.sub(r'此外，可以加入更多关于书的细节，比如书页上的符文、香气来源，以及青铜戒指的历史背景。', '', text, flags=re.DOTALL)
    text = re.sub(r'这些细节能为故事增添深度，并暗示未来的剧情发展。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'由于您没有提供具体的故事情节和当前章节内容，我将基于一个悬疑小说的框架，创作一段新的情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在让我们聚焦于.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'嗯，用户希望为小说.*?增加.*?个字符。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我需要理解当前的情节发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，用户提到可能会沿着几个方向发展：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'所以补充的内容应该围绕这些方面展开。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，可以加入主角回忆过去的片段，展示他与养母的关系变化，或者警方调查的进展，揭示更多关于养母的秘密。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到保持风格一致，语言应该是紧张、悬疑的，符合犯罪心理学和家庭秘密的主题。', '', text, flags=re.DOTALL)
    text = re.sub(r'需要增加一些细节，比如主角在审讯室里的感受，警方如何审问养母，以及主角内心的变化。', '', text, flags=re.DOTALL)
    text = re.sub(r'可能的情节发展包括：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过这样的补充，不仅增加了字数，还深化了角色背景和故事主线，为后续揭示真相埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我需要构思一个场景，可能是在审讯室里，警方询问养母，而主角在旁边观察，同时回忆起一些关键的记忆片段。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，在审讯室中，警官拿出一张旧报纸，提到养母过去的案件，引发主角的回忆。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过这样的补充，不仅增加了字数，还深化了悬疑感。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，检查字数是否达到要求，并确保语言风格与原章节一致。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样，补充的内容就能有效丰富故事，推动主线发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'好吧，我现在需要帮用户为小说.*?补充内容，增加.*?个字。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户已经提供了当前章节的结尾部分，并希望补充与主线相关的情节或细节，可以是角色的回忆、背景故事或后续发展，同时保持风格一致，使用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我得仔细阅读用户提供的现有内容，理解情节的发展和氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我要考虑如何补充.*?个字。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望增加与主线相关的内容，所以可能需要添加一些回忆、背景或后续发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到当前结尾部分，主角已经看到了婴儿照片，并且联想到雨夜的画面。', '', text, flags=re.DOTALL)
    text = re.sub(r'补充内容可以描述主角在看到照片时的心理活动，比如她突然想起养母曾经提到过某个地方，或者她记得养母在某个特定时间的行为异常。', '', text, flags=re.DOTALL)
    text = re.sub(r'我需要保持风格一致，紧张而悬疑的氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'可能添加一个回忆片段，让主角回想起养母过去的一些行为或对话，这可能会揭示更多线索，推动剧情发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，可以补充主角突然想起养母曾经带她去过某个地方，那里有旧房子，或者养母在某个雨夜表现出异常紧张。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样的细节不仅增加字数，还为后续情节埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我需要确保补充的内容流畅自然，并且符合现有情节的发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'可能的句子结构是：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样既增加了细节，又深化了悬疑感。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，用户希望增加三个段落，每段约500字左右，总共约1500字，以满足1558个字符的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'但看起来用户可能误解了，因为306个字符大约是两句话，而不是三个段落。', '', text, flags=re.DOTALL)
    text = re.sub(r'所以，我需要确认是否是补充到整个章节中，还是仅在结尾部分添加。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，用户提供了当前的章节结尾，包括林小夏回家后发现电脑异常的情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在需要补充与主线相关的内容，可以是角色回忆、背景故事或后续发展，并保持风格一致。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到小说可能涉及超自然元素，我应该扩展林小夏的能力展示，或者引入新的线索。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，增加一个场景，让她在使用能力时遇到更多问题，或者揭示她的过去。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，用户提到神秘老人和国家安全局的新闻，这暗示了更大的阴谋或背景故事。', '', text, flags=re.DOTALL)
    text = re.sub(r'我可以补充一些回忆，说明林小夏之前接触过类似的事情，或者她为何会获得这种能力。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，要保持风格一致，紧张而诡异，让读者感受到不安和悬念。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'用户希望保持原有情节连贯性，并且增加细节描写、对话或内心独白，同时自然融入扩展内容，使用中文写作，不要重复已有的内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'看起来用户的小说第一章主要讲述了一个神秘的信件和主角许晴与路远的相遇，以及他们参观画廊的情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来的情节可能会围绕以下线索展开：', '', text, flags=re.DOTALL)
    text = re.sub(r'- 神秘的艺术展和"命运"主题', '', text, flags=re.DOTALL)
    text = re.sub(r'- 画作中模糊的面容与许晴的关联', '', text, flags=re.DOTALL)
    text = re.sub(r'- 路远的特殊身份和他创作这幅画的原因', '', text, flags=re.DOTALL)
    text = re.sub(r'- 许晴对自身身世的好奇心', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这些扩展内容能让故事更加丰满，同时为后续发展埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更完整，我会先列出一些基本设定。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*初识路远\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*艺术区之行\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘画廊\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*画中秘密\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*命运关联\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在让我们开始故事的第一章：', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'嗯，用户给了一个小说章节的请求，需要我帮忙扩写大约1200字左右。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我要仔细阅读现有的章节内容，了解故事的发展和主要情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节描述了林夏在废弃大楼里经历的一系列事件，包括她进入电梯故障、遇到神秘男子周扬，以及开始解开密码箱的过程。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望保持连贯性，并增加细节描写、对话或内心独白，同时自然融入扩展内容，使用中文写作，避免重复。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我需要分析每个部分可以扩展的地方。', '', text, flags=re.DOTALL)
    text = re.sub(r'在进入废弃大楼的部分，可以详细描写环境，增加紧张氛围，比如风吹动落叶的声音，或者大楼外的警示标志。', '', text, flags=re.DOTALL)
    text = re.sub(r'电梯故障是一个关键点，可以在这里增加一些悬念，比如林夏听到的脚步声是否来自她自己或其他人，或者电梯里的消毒水味是否有特殊含义。', '', text, flags=re.DOTALL)
    text = re.sub(r'遇到周扬时，他们的对话可以更深入，探讨命运测试的目的和意义，以及周扬的真实动机。', '', text, flags=re.DOTALL)
    text = re.sub(r'在揭示真相的部分，可以加入更多关于"命运测试者"组织的背景信息，比如他们的历史、过去的参与者，以及为什么选择林夏。', '', text, flags=re.DOTALL)
    text = re.sub(r'这不仅丰富了故事，也为后续的发展埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，在关键抉择部分，可以详细描写密码箱的外观和符号，增加一些紧张感和时间压力，让读者感受到林夏的压力和决心。', '', text, flags=re.DOTALL)
    text = re.sub(r'结尾悬念处，可以留有更多的疑问，比如光芒中的预示或未完成的任务，为下一章做铺垫。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，我需要确保每个扩展部分自然融入原有情节，不破坏故事的连贯性，并通过细腻的描写和深入的对话，提升整体的吸引力。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'好，用户希望我帮他扩写一个小说章节的内容，大约增加1200字左右。', '', text, flags=re.DOTALL)
    text = re.sub(r'他给了具体的，并且不要重复已有的内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望添加与主线相关的情节或细节，可以是角色的回忆、背景故事或后续发展，并且要保持风格一致，使用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'这意味着我需要深入挖掘角色的过去，或者引入一些伏笔，为后续的发展做铺垫。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节结尾处，主角注意到本地人的手温暖干燥，这在雨天显得异常，可能暗示着什么秘密。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，主角对本地人知道很多感到疑惑，并联想到旅店听到的故事，这些都提示我需要扩展这些线索。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我应该考虑如何自然地插入回忆或背景故事。', '', text, flags=re.DOTALL)
    text = re.sub(r'或许可以展示本地人在成为向导之前的经历，比如他如何来到这座城市，或者之前发生在他身上的奇怪事件。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样既能丰富角色背景，又能增加悬疑氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，我可以加入一个场景，显示本地人过去在工厂附近失踪的经历，或者他的家人与工厂有关的悲剧。', '', text, flags=re.DOTALL)
    text = re.sub(r'这不仅解释了他对工厂的态度，也为后续情节埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，通过对话揭示角色的内心活动和动机，让读者更深入地理解他们的行为。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我开始构思具体的情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'或许在主角和本地人奔跑的过程中，本地人突然停下，回忆起过去的一次经历，描述工厂附近的诡异现象，或者讲述他如何失去了家人，从而对工厂产生深深的恐惧或恨意。', '', text, flags=re.DOTALL)
    text = re.sub(r'这些内容不仅能增加字数，还能深化角色的动机，推动剧情发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，确保补充的内容与主线紧密相关，并且自然地融入现有情节中，不显得突兀。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，检查语言风格是否一致，保持悬疑和紧张的氛围，让读者欲罢不能。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'用户提供了一个当前章节的内容，但似乎没有给出具体内容，所以我可能需要假设一些情境来展开。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到小说章节通常有起承转合，我可以选择一个关键点进行扩展，比如主角遇到神秘人物的情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 世界观设定', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*时间设定\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*地点设定\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*基本背景\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 故事梗概', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*意外重逢\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*身份之谜\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*跟踪事件\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*诡异场景\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'---', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个故事开头能满足你的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'好，我现在要帮用户为小说《测试小说22》第一章补充1789个字符。', '', text, flags=re.DOTALL)
    text = re.sub(r'当前章节结尾已经写得不错，但需要增加更多情节和细节，同时保持故事连贯性和风格一致。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我需要理解现有内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'林深和顾明城重逢，顾提到自己创立了私募基金公司，并且在纽约上市。这让林深感到意外，因为她记得五年前顾还很穷。接着，他们上了车，顾开车，座位下有泛黄的照片，引发后续发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望补充与主线相关的情节或细节，可以是回忆、背景故事或后续发展。我需要考虑如何扩展这些部分，增加深度和悬念。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，可以深入林深的内心活动，展示她对顾明城变化的感受，以及她为何突然离开。这可能涉及她的过去和现在的情感状态。例如，她可能在犹豫是否要揭露顾的秘密，或者她有自己的秘密。', '', text, flags=re.DOTALL)
    text = re.sub(r'其次，照片中的女孩小雨，可以增加一些背景故事。可以考虑这个人的背景和动机，以及他如何影响林深和顾的关系。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，可以加入一些环境描写，比如地铁站的氛围，或者餐厅的装饰，增强场景的真实感。同时，通过对话展示角色的性格变化，比如林深变得更加谨慎，而顾明城则显得有些疏离或隐藏。', '', text, flags=re.DOTALL)
    text = re.sub(r'我还需要确保补充的内容与主线紧密相关，不偏离主要情节。例如，可以增加林深回忆起过去帮助顾的情景，或者她如何发现顾的秘密，从而推动故事发展。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'为了让故事更完整，我会先列出一些基本的情节安排。请您看看以下内容是否符合您的预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 章节概要', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘古籍\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*黑衣人夜枭\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*意外邂逅\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘力量\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'重点展现人物性格和初步建立敌对关系。', '', text, flags=re.DOTALL)
    text = re.sub(r'请您看看以下内容是否符合您的预期。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*第一章：命运交织\*\*：', '', text, flags=re.DOTALL)
    text = re.sub(r'- 苏晴发现自己体内觉醒特殊力量，并意外获得神秘古籍。', '', text, flags=re.DOTALL)
    text = re.sub(r'- 在古董店遇到白影，得知自己是守望者组织的一员。', '', text, flags=re.DOTALL)
    text = re.sub(r'- 夜枭的出现揭示了血统觉醒者的身份和背后的阴谋。', '', text, flags=re.DOTALL)
    text = re.sub(r'我们将重点描写苏晴在古董店遇到白影时的情节，以及她逐渐发现自己身世的过程。这段内容将展示主角与神秘组织的关系，同时埋下血脉相连的重要伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*血脉相连\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*觉醒者使命\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘古籍\*\*：.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我得仔细阅读当前章节的内容，理解故事的发展和主要线索。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，用户希望补充514个字符，这意味着需要添加大约两段左右的内容。考虑到故事的发展，我应该选择一个能够推进主线的情节点。例如，主角回忆过去，或者与张教授的对话揭示更多实验细节。', '', text, flags=re.DOTALL)
    text = re.sub(r'在当前结尾中，小夏被救下后，张教授显得慌乱，这可能是一个好的切入点。或许可以加入一段小夏和张教授之间的对话，进一步解释实验的目的，以及为什么选择她作为实验对象。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样不仅增加了背景故事，还能推动主线发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，保持风格一致很重要。原文充满了紧张和悬念，补充的内容也应该延续这种氛围。例如，通过对话揭示更多的信息，同时让读者感受到主角的困惑和恐惧。', '', text, flags=re.DOTALL)
    text = re.sub(r'我还需要注意字数限制，确保补充内容大约514个字符，不要过多或过少。因此，可能需要精简语言，突出关键情节，避免冗长。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，检查是否符合所有要求：补充与主线相关的情节，保持风格一致，使用中文，并且控制在指定字数内。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'这个故事将围绕一具在雪山中发现的尸体展开，涉及神秘事件和未解之谜。为了让故事更加引人入胜，我会先列出一些基本的情节安排。', '', text, flags=re.DOTALL)
    text = re.sub(r'故事梗概', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*诡异发现\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*高原反应\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*当地传说\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘现象\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段将重点描写林楚在雪山中发现诡异现象的过程，以及她与其他登山者的互动。通过引入当地向导提到的"雪女"传说，为后续剧情埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个故事开篇能满足你的要求。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我会确定章节的标题，按照示例使用.*?。接下来，我要围绕主角.*?。关键是要有生动的场景和对话，让读者感受到紧张和悬念。', '', text, flags=re.DOTALL)
    text = re.sub(r'我需要先描述.*?。然后，她发现.*?。下班回家后，突如其来的破坏和神秘男子的出现是本章的关键转折点，需要详细描写，突出紧张感。', '', text, flags=re.DOTALL)
    text = re.sub(r'对话部分要真实，反映角色的情感状态。例如，.*?。这些都能增强故事的真实性和吸引力。', '', text, flags=re.DOTALL)
    text = re.sub(r'场景描写方面，我会注重环境细节，比如.*?。同时，动作描写要细腻，展示主角如何利用周围环境逃脱，突出她的机智。', '', text, flags=re.DOTALL)
    text = re.sub(r'结尾部分要留下悬念，让读者对后续情节充满期待。.*?。这为第二章的发展埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作过程中，我要确保语言流畅自然，避免过于复杂的句子结构，同时保持叙述的节奏感。通过详细描写每个关键事件和角色互动，使第一章内容充实，引人入胜。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，检查整体结构是否合理，情节是否有逻辑漏洞，并确保符合用户的所有要求，包括字数、中文写作等。这样，就能生成一份高质量的小说第一章内容了。', '', text, flags=re.DOTALL)
    text = re.sub(r'所以，我需要在现有基础上添加更多的环境描写、人物心理活动以及可能的背景故事，使情节更加丰富和紧张。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我可以考虑在李小曼发现文件夹时，增加她的内心感受，比如她的好奇心和对项目的疑问。然后，在接到王强电话后，可以详细描述她收拾东西的过程，以及她拿到文件夹时的心理变化，比如她为什么会对这个项目感兴趣，是否有之前的线索或背景。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，当李小曼走出公司大楼时，环境描写可以更细致，比如周围的街道、天气的变化，或者她看到的其他人的反应。这能增强紧张感，让读者感受到她的不安和恐惧。', '', text, flags=re.DOTALL)
    text = re.sub(r'在遇到陈浩的情节中，可以增加更多的对话，揭示更多关于项目的信息。例如，陈浩为什么会知道李小曼的名字？他是否有其他的背景故事？同时，加入一些动作描写，比如李小曼的挣扎、周围的环境变化，如街灯的变化或人群的反应，来增强场景的真实感。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，在李小曼逃脱后，可以描绘她的心理活动，她如何联系王强，以及她对整个事件的新认识。这里可以引入更多的悬念，让读者好奇接下来会发生什么。', '', text, flags=re.DOTALL)
    text = re.sub(r'总的来说，我需要在不破坏原有情节的情况下，深入挖掘人物的心理和环境细节，增加紧张感和悬疑氛围，使章节内容更加丰富和引人入胜。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我会回顾一下之前的大纲，确保情节连贯。大纲中提到，.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要将这些元素转化为生动的文字。为了让故事更吸引人，我会在开头描绘.*?。然后，详细描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'加入对话可以让角色更加鲜活。.*?。同时，.*?也是关键情节，这部分需要详细展开，展示他内心的震撼和困惑。', '', text, flags=re.DOTALL)
    text = re.sub(r'在高潮部分，.*?是一个转折点，我会通过细腻的环境描写和紧凑的情节推动故事发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'例如，在教室场景中，可以加入其他学生对.*?。此外，图书馆部分可以详细描绘.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我还需要注意不要重复已有的内容，避免让读者感到冗长。同时，要确保扩展后的情节与原有内容无缝衔接，保持连贯性。例如，.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'这样，用户的小说第一章将更加丰富，吸引读者继续阅读。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更完整，我会先列出一些基本的情节框架。如果您有其他想法,可以随时提出,我会进行调整。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*雨夜记忆\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*研究动机\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*实验进展\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*伦理困境\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段主要描写.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'用户已经提供了当前的章节内容，并且指定了要求：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我要仔细阅读现有的章节内容，了解情节发展和人物设定。.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，加入更多的对话或内心独白可以让故事更生动。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望增加1200字左右，所以我要确定哪些部分可以详细展开。.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我会考虑添加一些环境描写，比如.*?。同时，加入更多的人物对话，让情节更流畅，比如.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，可以增加一些内心独白，展示林沫的心理活动，比如.*?。这些都能帮助读者更深入地理解她的性格和处境。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，要确保不重复已有内容，保持情节连贯性，并自然融入新细节。例如，.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，检查整体结构，确保新增部分与原有章节衔接自然，没有突兀的地方。同时，注意语言流畅，避免语法错误，保持中文表达的准确性。', '', text, flags=re.DOTALL)
    text = re.sub(r'总结一下，我会在以下方面进行扩展：.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'我需要考虑如何在现有基础上添加更多细节，丰富场景和人物情感。', '', text, flags=re.DOTALL)
    text = re.sub(r'如果您有其他想法,可以随时提出,我会进行调整。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 详细情节安排：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'一阵刺痛让苏雨晴猛地睁开眼睛。.*?母亲。', '', text, flags=re.DOTALL)
    text = re.sub(r'我会先从苏雨晴在地铁站遇到醉汉的情节入手，增加更多的环境描写和心理活动。.*?展示他们之间的关系和冲突。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，要注意节奏，避免情节过于拖沓。每个新增的部分都要服务于整体故事，推动剧情发展或揭示人物背景。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'嗯，用户希望我扩写一个小说章节，增加大约.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我要保持原有情节的连贯性，不能改变已有的事件顺序。然后，考虑增加哪些部分可以丰富故事。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段将展现这块晶体如何从一个简单的矿物样本变成改变她生活的关键。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来故事可能会沿着这些方向发展：', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*能量吸收特性\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*生命特征感知\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*特派调查员动机\*\*：.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'他们希望增加内容，但必须保持风格一致，并且用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*神秘来客\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*玉佩之谜\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*身份疑云\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*家族往事\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*黑暗交易\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我们将重点描写.*?。这些情节将为后续故事发展埋下重要伏笔。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我要仔细阅读当前的章节内容，理解故事的发展和角色之间的关系。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户的要求是保持情节连贯性，增加细节描写、对话或内心独白，自然融入扩展内容，并且用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，故事已经铺垫了紧张的氛围，引入了马克这个神秘人物，以及《格林伍德预言》这本书的重要性。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到用户希望增加细节和内心独白，我可以扩展.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'另外，环境描写也很重要。这些细节能增强场景的真实感和紧张氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'在扩展过程中，要注意不要重复已有的情节，而是深入挖掘角色的情感和动机，同时自然地推进故事的发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，确保语言流畅，保持原有的风格，避免加入突兀的内容。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'为了让故事更完整，我会先列出一些基本的情节发展脉络。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 详细情节设计', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*初次接触\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*进入废墟\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*紧张追逐\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*金属吊坠\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*秘密组织\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*特殊能力\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'嗯，用户希望我为小说.*?生成第一章内容，根据他们提供的大纲。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我需要仔细阅读并理解大纲的结构和要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户强调第1章要符合大纲中的对应部分，并且要求详细生动，有对话和场景描写，字数在2000到3000字之间。', '', text, flags=re.DOTALL)
    text = re.sub(r'此外，章节开头要有标题。这意味着我需要按照大纲的内容展开，同时注重细节描写和人物互动，使故事更具吸引力。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我会从故事背景入手。', '', text, flags=re.DOTALL)
    text = re.sub(r'而江夏则是一个神秘且冷酷的调查员，与方小鱼是同事关系，这为两人之间的互动提供了基础。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*场景描写\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*人物互动\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*悬念设置\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我可以开始撰写第一章的具体内容了。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'首先，我会分析每个章节可以扩展的部分。', '', text, flags=re.DOTALL)
    
    # 删除更多以"首先，我"开头的分析内容
    text = re.sub(r'首先，我(?:需要|会)分析[^\n。！？]*[。！？]', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我(?:需要|会)仔细阅读[^\n。！？]*[。！？]', '', text, flags=re.DOTALL)
    # 更精确地匹配以"首先，我"开头的完整句子
    text = re.sub(r'首先，我(?:需要|会|应该|要|得|必须|应当|理应|务必|一定|应当)(?:考虑如何|分析|仔细阅读|找出|确定|思考|理解|回顾|检查|观察|研究|探讨|评估|判断|决定|计划|准备|安排|设计|构思|创作|编写|撰写|扩展|扩展这个故事|扩展的地方)[^\n。！？]*[。！？]', '', text, flags=re.DOTALL)
    
    # 删除以"接下来，我"和"最后，"开头的分析内容
    text = re.sub(r'接下来，我(?:需要|会|应该|要|得|必须|应当|理应|务必|一定|应当)[^\n。！？]*[。！？]', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，(?:结尾部分|结尾)[^\n。！？]*[。！？]', '', text, flags=re.DOTALL)
    
    # 删除特定的AI分析内容
    text = re.sub(r'首先，我会分析每个章节可以扩展的部分。在进入废弃大楼的部分，可以详细描写环境，增加紧张氛围，比如风吹动落叶的声音，或者大楼外的警示标志。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我需要仔细阅读当前的章节内容，理解故事的发展和角色之间的关系。用户的要求是保持情节连贯性，增加细节描写、对话或内心独白，自然融入扩展内容，并且用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，我应该考虑如何扩展这个故事。可以增加更多关于老宅的背景信息，以及台钟的来历。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来，我需要找出可以扩展的地方。可以详细描写李小明的内心活动，以及他对老宅和照片的反应。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，结尾部分可以加入一些悬念，为下一章做铺垫。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'接下来的故事可能会沿着这些方向发展：.*?希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'接下来的故事可能会沿着这些方向发展：', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*.*?\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'第一章描述了叶秋发现异常代码的过程，我可以在这里加入更多关于实验室环境的描写，比如时间、天气，以及他当时的情绪变化。例如.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'第一章描述了叶秋发现异常代码的过程，我可以在这里加入更多关于实验室环境的描写，比如时间、天气，以及他当时的情绪变化。例如 \x08\n，增加一些关于显示器闪烁的具体细节，或者他打开调试模式时的心理活动\.', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'"同时，要增加对话、内心独白和环境描写，使故事更生动。还要注意不要重复已有的内容，避免让读者感到冗余."', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'例如\x08\n，增加一些关于显示器闪烁的具体细节，或者他打开调试模式时的心理活动\.', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'接下来的故事可能会沿着这些方向发展：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*Project 38的秘密\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*小艾的异常\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*李明远的身份\*\*：.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'第一章描述了叶秋发现异常代码的过程，我可以在这里加入更多关于实验室环境的描写，比如时间、天气，以及他当时的情绪变化。例如.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'"同时，要增加对话、内心独白和环境描写，使故事更生动。还要注意不要重复已有的内容，避免让读者感到冗余."', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'接下来的故事可能会沿着这些方向发展：', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*Project 38的秘密\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*小艾的异常\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*李明远的身份\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'例如\x08\n，增加一些关于显示器闪烁的具体细节，或者他打开调试模式时的心理活动\.', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'接下来的故事可能会沿着这些方向发展：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*Project 38的秘密\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*小艾的异常\*\*：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'- \*\*李明远的身份\*\*：.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'如您满意，我可以继续创作第三章，或根据您的指示调整方向。', '', text, flags=re.DOTALL)
    text = re.sub(r'如您满意，我可以继续创作', '', text, flags=re.DOTALL)
    text = re.sub(r'根据您的指示调整方向', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'"同时，要增加对话、内心独白和环境描写，使故事更生动。还要注意不要重复已有的内容，避免让读者感到冗余."', '', text, flags=re.DOTALL)
    
    # 删除更多的AI分析内容
    text = re.sub(r'通过这样的思考过程，我可以有效地帮助用户扩写小说章节，使故事更加丰富和吸引人。', '', text, flags=re.DOTALL)
    text = re.sub(r'思考过程', '', text, flags=re.DOTALL)
    
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
    
    # 删除更多的写作指导和分析内容
    text = re.sub(r'，我要确保.*?埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'我需要创造一些.*?埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过以上扩展，故事更加丰富了.*?埋下更多伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'因此，补充内容应该进一步展开这些线索.*?最后，确保语言风格与原章节一致，紧张而充满悬疑氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'好，我现在需要帮用户为小说.*?增加.*?字的内容。用户已经提供了', '', text, flags=re.DOTALL)
    text = re.sub(r'他们希望补充与主线相关的情节或细节.*?使用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'因此，补充内容应该.*?增加紧张感和悬念，同时丰富.*?背景故事。', '', text, flags=re.DOTALL)
    text = re.sub(r'考虑到用户希望补充.*?我需要精炼地添加情节。', '', text, flags=re.DOTALL)
    text = re.sub(r'或许可以加入.*?增加神秘感。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，确保语言风格与原章节一致，紧张而充满悬疑氛围。', '', text, flags=re.DOTALL)
    
    # 删除更多的分析和说明内容
    text = re.sub(r'\*\*内容可能会更加紧张和刺激，因为.*?身世之谜。\*\*', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更加连贯丰富，我会先列出一些基本的情节发展。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 本次扩写的重点', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这段扩展能满足您的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望这个扩写能满足您的要求。', '', text, flags=re.DOTALL)
    text = re.sub(r'希望以上内容符合您的要求。', '', text, flags=re.DOTALL)
    
    # 删除更多的总结性分析内容
    text = re.sub(r'通过以上扩展，故事更加丰富了.*?埋下更多伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过以上.*?使故事更加.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过这些.*?使情节更加.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'通过.*?增加.*?使.*?更加.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的写作指导和分析内容
    text = re.sub(r'为了让故事更完整，我会先列出一些基本的设定。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一部分将重点描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段将重点描写.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'重点展现.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我们将重点描写.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的分析性内容
    text = re.sub(r'首先，用户提供了一个详细的大纲，分为.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望我根据大纲生成.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'，我要考虑如何将大纲内容转化为具体的章节。', '', text, flags=re.DOTALL)
    text = re.sub(r'首先，确定.*?。然后引入.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作风格上，我需要保持生动，加入细节描写来增强画面感，比如.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，要为后续的发展埋下伏笔，比如.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'还要注意章节的连贯性，确保.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'，我会考虑如何展开第二章的内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'从.*?开始，描述.*?。然后引入.*?。最后，通过.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作过程中，我会注意.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，保持连贯性，为后续章节的发展埋下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我将根据这些思考开始撰写.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的分析和说明内容
    text = re.sub(r'好，用户希望我根据之前的大纲为小说.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'在第一章中，.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'以下是扩写后的内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'，故事可能会沿着这些方向发展：', '', text, flags=re.DOTALL)
    text = re.sub(r'此外，章节开头要有标题。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作时，要注意场景的描绘和氛围的营造，比如.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，确保不重复已有内容，自然融入扩展部分，让读者感受到紧张和悬疑的氛围。', '', text, flags=re.DOTALL)
    text = re.sub(r'主角.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的写作分析和指导内容
    text = re.sub(r'用户的大纲已经很清晰了，所以我需要按照大纲的结构来展开。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让内容生动，我需要加入具体的场景和对话。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，我要注意人物性格的刻画。', '', text, flags=re.DOTALL)
    text = re.sub(r'在写作过程中，我需要确保情节连贯，并为后续章节留下伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我要注意语言流畅，避免过于复杂的句子结构，让读者容易理解。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我可以开始按照这些思路来写作.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更加丰富和引人入胜，我会增加一些细节描写、对话以及内心独白，并确保情节连贯。', '', text, flags=re.DOTALL)
    text = re.sub(r'请您提供具体想要扩展的内容或指示，这样我可以更好地满足您的需求。', '', text, flags=re.DOTALL)
    text = re.sub(r'如果您有特定的情节或角色发展想法，请随时告诉我，我会根据这些信息进行扩写。', '', text, flags=re.DOTALL)
    text = re.sub(r'## 第二章：揭露真相的代价', '', text, flags=re.DOTALL)
    text = re.sub(r'## 补充内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'补充内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'场景[一二三四五六七八九十]+：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'标题：.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'结尾：', '', text, flags=re.DOTALL)
    
    # 删除更多的分析和说明内容
    text = re.sub(r'好，我现在需要帮用户为小说.*?补充.*?字的内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望补充与主线相关的情节或细节.*?使用中文写作。', '', text, flags=re.DOTALL)
    text = re.sub(r'因此，我需要在现有情节的基础上添加更多的内容，丰富故事，同时不偏离主线。', '', text, flags=re.DOTALL)
    text = re.sub(r'我会分析.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我可以考虑添加.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'我还需要确保补充的内容与主线相关，并且保持风格一致。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我会检查字数，确保补充内容达到.*?字符左右。', '', text, flags=re.DOTALL)
    text = re.sub(r'现在，我需要分析每个段落，寻找可以扩展的地方。', '', text, flags=re.DOTALL)
    text = re.sub(r'此外，当他们决定揭露真相时，可以加入更多关于他们计划的具体细节。', '', text, flags=re.DOTALL)
    text = re.sub(r'最后，我要确保整个扩展部分自然流畅，不显得突兀或重复。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更加丰富，我会先列出一些关键的扩展点：', '', text, flags=re.DOTALL)
    text = re.sub(r'1\..*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'2\..*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'3\..*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'4\..*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'5\..*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'推开门的一瞬间，艾琳的心跳漏了一拍。.*?现在想来', '', text, flags=re.DOTALL)
    
    # 删除更多的示范和说明内容
    text = re.sub(r'由于您还没有提供具体的章节内容，我先假设一个典型的小说章节场景来进行示范。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 示范扩写：', '', text, flags=re.DOTALL)
    text = re.sub(r'#### 原有情节：', '', text, flags=re.DOTALL)
    text = re.sub(r'#### 扩写后的内容：', '', text, flags=re.DOTALL)
    text = re.sub(r'#### 说明：', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更完整，我会先构建一些基本的设定。', '', text, flags=re.DOTALL)
    text = re.sub(r'### 章节梗概：', '', text, flags=re.DOTALL)
    text = re.sub(r'Gallery里人来人往.*?这可能与画展的安全问题有关。', '', text, flags=re.DOTALL)
    text = re.sub(r'张杰是一个私家侦探.*?这可能暗示画廊的安全问题和张杰的身份有关联。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户希望补充的内容要与主线相关.*?大约289个字符左右，确保信息量足够但不过于冗长。', '', text, flags=re.DOTALL)
    text = re.sub(r'林悦注意到周先生介绍时.*?那双眼睛，仿佛藏着无数秘密。', '', text, flags=re.DOTALL)
    
    # 删除更多的写作指导和分析内容
    text = re.sub(r'首先，可以考虑.*?这样能增强画面感。', '', text, flags=re.DOTALL)
    text = re.sub(r'同时，在与.*?让读者更了解.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'然后，在.*?增加情感深度。', '', text, flags=re.DOTALL)
    text = re.sub(r'还可以加入一些.*?使情节更加紧凑。', '', text, flags=re.DOTALL)
    text = re.sub(r'这样，用户的小说将更加丰富和引人入胜。', '', text, flags=re.DOTALL)
    text = re.sub(r'为了让故事更加丰满，我会先列出一些基本的问题框架。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段将为后续剧情发展埋下重要伏笔。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一段将展现.*?。', '', text, flags=re.DOTALL)
    text = re.sub(r'这一部分将展现.*?。', '', text, flags=re.DOTALL)
    
    # 删除更多的用户分析和查询分析内容
    text = re.sub(r'用户提供了一个查询，其中包含了具体的，同时不重复已有内容。', '', text, flags=re.DOTALL)
    text = re.sub(r'用户可能是一位.*?深层需求可能是想', '', text, flags=re.DOTALL)
    
    if blacklist:
        # 范围删除
        for pattern in blacklist.get('ranges', []):
            logger.debug(f"处理范围模式: {pattern}")
            text = re.sub(pattern + r'\s*', '', text, flags=re.DOTALL)
        
        # 全字匹配删除
        for word in blacklist.get('exact', []):
            logger.debug(f"处理精确匹配词: {word}")
            # 使用更简单的正则表达式进行测试
            text = re.sub(re.escape(word), '[已屏蔽]', text)
    
    # 调试输出，检查黑名单处理
    logger.debug(f"黑名单处理后长度: {len(text)}")
    
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
    result = '\n'.join(cleaned_lines)
    
    # 清理乱码字符（保留换行符）
    result = re.sub(r'[\x08\x0b\x0c\x07]', '', result)  # 删除常见的乱码控制字符，但保留换行符
    result = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s]', '', result)  # 保留ASCII、中文、常见标点和空白字符
    
    # 修复混用的英文
    result = re.sub(r'glance around her apartment', '环顾她的公寓', result)
    
    return result
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
                        # 调试输出，检查清理前的内容
                        logger.debug(f"合并章节前清理前长度: {len(content)}")
                        # 清理内容
                        cleaned_content = clean_content(content, blacklist)
                        logger.debug(f"合并章节前清理后长度: {len(cleaned_content)}")
                        # 确保写入的内容是正确的UTF-8编码
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

def get_model_type(config: dict = None) -> str:
    """获取模型类型
    
    Args:
        config (dict, optional): 配置字典，如果未提供则自动加载
        
    Returns:
        str: 模型类型 ("ollama" 或 "openai")
    """
    if config is None:
        config = load_config()
    
    # 从配置中获取默认模型类型
    model_selection = config.get('model_selection', {})
    default_type = model_selection.get('default_type', 'ollama')
    
    # 验证模型类型
    if default_type not in ['ollama', 'openai']:
        logger.warning(f"无效的模型类型: {default_type}，使用默认值 'ollama'")
        return 'ollama'
    
    return default_type
