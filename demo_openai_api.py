#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI API演示脚本
展示如何使用OpenAI兼容API生成小说内容
"""

import os
import sys
from src.model_handler import ModelHandler
from src.utils import logger

def demo_novel_generation():
    """演示小说生成"""
    print("📚 OpenAI API小说生成演示")
    print("=" * 50)
    
    try:
        # 创建ModelHandler实例，指定使用OpenAI
        print("🔧 初始化OpenAI模型处理器...")
        model_handler = ModelHandler(model_type='openai')
        
        # 1. 生成小说大纲
        print("\n📝 步骤1: 生成小说大纲")
        outline_prompt = """请为一部科幻小说生成一个详细的大纲，包含5个章节。
要求：
1. 每个章节有明确的主题和情节发展
2. 章节之间要有连贯性
3. 包含主要人物介绍和故事背景
4. 使用中文回答

请按以下格式输出：
小说标题：[标题]
总章节数：5

大纲内容：
"""
        
        print("正在生成大纲...")
        outline = model_handler.generate_text_with_model(
            outline_prompt, "outline", model_type='openai', temperature=0.8
        )
        
        if outline:
            print("✅ 大纲生成成功!")
            print(f"📖 大纲内容:\n{outline}\n")
        else:
            print("❌ 大纲生成失败")
            return False
            
        # 2. 生成第一章内容
        print("\n📝 步骤2: 生成第一章内容")
        chapter_prompt = f"""根据以下大纲，生成小说的第一章内容。

大纲：
{outline}

要求：
1. 这是第一章，要符合大纲中的对应部分
2. 内容要详细生动，有对话和场景描写
3. 字数在1000-1500字之间
4. 使用中文写作
5. 章节开头要有标题

请直接开始写作第一章的内容：
"""
        
        print("正在生成第一章...")
        chapter1 = model_handler.generate_text(
            chapter_prompt, model_type='openai', temperature=0.7
        )
        
        if chapter1:
            print("✅ 第一章生成成功!")
            print(f"📖 第一章内容:\n{chapter1[:500]}{'...' if len(chapter1) > 500 else ''}\n")
        else:
            print("❌ 第一章生成失败")
            return False
            
        # 3. 生成章节摘要
        print("\n📝 步骤3: 生成章节摘要")
        summary_prompt = f"""请为以下小说章节生成简洁的摘要。

章节内容：
{chapter1[:1000]}

要求：
1. 用中文总结主要情节
2. 控制在100-200字之间
3. 突出关键事件和人物发展

摘要：
"""
        
        print("正在生成摘要...")
        summary = model_handler.generate_text(
            summary_prompt, model_type='openai', temperature=0.3
        )
        
        if summary:
            print("✅ 摘要生成成功!")
            print(f"📋 章节摘要:\n{summary}\n")
        else:
            print("❌ 摘要生成失败")
            return False
            
        print("\n🎉 小说生成演示完成!")
        print("💡 演示展示了如何使用OpenAI API生成完整的小说内容流程")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {str(e)}")
        logger.error(f"OpenAI API演示失败: {str(e)}")
        return False

def main():
    """主函数"""
    success = demo_novel_generation()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
