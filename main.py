#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 项目主程序 - 命令行交互界面

import os
import sys
import argparse
import time
from src.novel_generator import NovelGenerator
from src.video_generator import VideoGenerator
from src.model_handler import ModelHandler
from src.utils import load_blacklist, load_config, setup_logger, clean_content, merge_chapters

# 初始化日志
logger = setup_logger()

def clear_screen():
    """清空终端屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """显示项目横幅"""
    print("""
==================================================
          NovelCreator Transformer v1.0
      小说创作与视频生成一体化工具 - 交互式控制台
==================================================
    """)

def main_menu():
    """主菜单"""
    clear_screen()
    display_banner()
    print("【主菜单】")
    print("1. 生成小说")
    print("2. 生成视频")
    print("3. 配置管理")
    print("4. 查看项目状态")
    print("5. 清理临时文件")
    print("6. 退出")
    
    choice = input("\n请输入选项编号: ")
    return choice

def novel_generation_menu():
    """小说生成子菜单"""
    clear_screen()
    print("【小说生成】")
    print("1. 创建新小说")
    print("2. 继续生成小说")
    print("3. 合并小说章节")
    print("4. 返回主菜单")
    
    choice = input("\n请输入选项编号: ")
    return choice

def video_generation_menu():
    """视频生成子菜单"""
    clear_screen()
    print("【视频生成】")
    print("1. 从小说文本生成视频")
    print("2. 从章节目录生成视频")
    print("3. 返回主菜单")
    
    choice = input("\n请输入选项编号: ")
    return choice

def config_management_menu():
    """配置管理子菜单"""
    clear_screen()
    print("【配置管理】")
    print("1. 查看当前配置")
    print("2. 编辑模型配置")
    print("3. 编辑黑名单")
    print("4. 返回主菜单")
    
    choice = input("\n请输入选项编号: ")
    return choice

def generate_novel():
    """生成新小说"""
    theme = input("请输入小说主题: ")
    output_dir = input("请输入输出目录(默认: novels): ") or "novels"
    
    try:
        model_handler = ModelHandler()
        generator = NovelGenerator(model_handler)
        generator.generate_novel(theme, output_dir)
        print(f"\n小说生成完成! 保存至: {output_dir}/{theme}")
    except Exception as e:
        logger.error(f"小说生成失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def continue_novel():
    """继续生成小说"""
    book_title = input("请输入小说名称: ")
    print(f"继续生成小说: {book_title}...")
    # 实现继续生成逻辑
    input("\n按Enter键继续...")

def merge_novel_chapters():
    """合并小说章节"""
    novel_dir = input("请输入小说目录路径: ")
    try:
        merge_chapters(novel_dir)
        print(f"章节合并完成! 完整小说保存至: {novel_dir}/full_novel.txt")
    except Exception as e:
        logger.error(f"章节合并失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def generate_video_from_text():
    """从文本生成视频"""
    input_file = input("请输入小说文本文件路径: ")
    output_file = input("请输入视频输出路径(默认: output.mp4): ") or "output.mp4"
    
    try:
        generator = VideoGenerator()
        generator.generate_from_text(input_file, output_file)
        print(f"\n视频生成完成! 保存至: {output_file}")
    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def view_project_status():
    """查看项目状态"""
    clear_screen()
    print("【项目状态】")
    print(f"工作目录: {os.getcwd()}")
    print("\n核心模块:")
    print(f"  - 模型处理器: {'已加载' if hasattr(ModelHandler, 'initialize_model') else '未加载'}")
    print(f"  - 小说生成器: {'就绪' if hasattr(NovelGenerator, 'generate_novel') else '未就绪'}")
    print(f"  - 视频生成器: {'就绪' if hasattr(VideoGenerator, 'generate_from_text') else '未就绪'}")
    
    # 显示配置状态
    try:
        config = load_config()
        print("\n当前配置:")
        print(f"  - 模型: {config.get('ollama', {}).get('model', '未设置')}")
        print(f"  - API端点: {config.get('ollama', {}).get('endpoint', '未设置')}")
    except:
        print("\n配置加载失败")
    
    input("\n按Enter键返回主菜单...")

def cleanup_temp_files():
    """清理临时文件"""
    print("清理临时文件...")
    # 实现清理逻辑
    print("临时文件清理完成!")
    input("\n按Enter键继续...")

def main():
    """主程序入口"""
    while True:
        choice = main_menu()
        
        if choice == '1':  # 生成小说
            while True:
                sub_choice = novel_generation_menu()
                if sub_choice == '1':
                    generate_novel()
                elif sub_choice == '2':
                    continue_novel()
                elif sub_choice == '3':
                    merge_novel_chapters()
                elif sub_choice == '4':
                    break
                else:
                    print("无效选项，请重新输入")
        
        elif choice == '2':  # 生成视频
            while True:
                sub_choice = video_generation_menu()
                if sub_choice == '1':
                    generate_video_from_text()
                elif sub_choice == '2':
                    print("功能开发中...")
                    input("\n按Enter键继续...")
                elif sub_choice == '3':
                    break
                else:
                    print("无效选项，请重新输入")
        
        elif choice == '3':  # 配置管理
            while True:
                sub_choice = config_management_menu()
                if sub_choice == '1':
                    # 查看配置
                    print("功能开发中...")
                    input("\n按Enter键继续...")
                elif sub_choice == '2':
                    # 编辑模型配置
                    print("功能开发中...")
                    input("\n按Enter键继续...")
                elif sub_choice == '3':
                    # 编辑黑名单
                    print("功能开发中...")
                    input("\n按Enter键继续...")
                elif sub_choice == '4':
                    break
                else:
                    print("无效选项，请重新输入")
        
        elif choice == '4':  # 查看项目状态
            view_project_status()
        
        elif choice == '5':  # 清理临时文件
            cleanup_temp_files()
        
        elif choice == '6':  # 退出
            print("\n感谢使用 NovelCreator Transformer!")
            sys.exit(0)
        
        else:
            print("无效选项，请重新输入")
            time.sleep(1)

if __name__ == "__main__":
    main()
