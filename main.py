#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 项目主程序 - 支持命令行参数和交互式两种模式

import os
import sys
import argparse
import time
import yaml
from src.novel_generator import NovelGenerator
from src.video_generator import VideoGenerator
from src.model_handler import ModelHandler
from src.utils import load_blacklist, load_config, merge_chapters, logger

# 命令行参数处理函数
def parse_arguments():
    parser = argparse.ArgumentParser(description='NovelCreator Transformer - 小说创作与视频生成工具')
    subparsers = parser.add_subparsers(dest='mode', help='操作模式')

    # 小说生成模式
    novel_parser = subparsers.add_parser('novel', help='小说生成相关操作')
    novel_parser.add_argument('--action', choices=['new', 'continue', 'merge'], required=True,
                             help='操作类型: new(新建), continue(继续), merge(合并章节)')
    novel_parser.add_argument('--title', required=True, help='小说标题')
    novel_parser.add_argument('--output-dir', default='novels', help='输出目录')
    novel_parser.add_argument('--chapters', type=int, default=10, help='章节数量')

    # 视频生成模式
    video_parser = subparsers.add_parser('video', help='视频生成相关操作')
    video_parser.add_argument('--input', required=True, help='输入文本文件路径')
    video_parser.add_argument('--output', default='output.mp4', help='输出视频文件路径')
    video_parser.add_argument('--font', default='resources/SimHei.ttf', help='字体文件路径')

    # 其他模式
    other_parser = subparsers.add_parser('other', help='其他操作')
    other_parser.add_argument('--action', choices=['status', 'clean'], required=True,
                             help='操作类型: status(查看状态), clean(清理临时文件)')

    # 通用参数
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')

    return parser.parse_args()

# 非交互式命令行处理函数
def run_command_line(args):
    # 根据 --verbose 设置日志级别
    if getattr(args, 'verbose', False):
        logger.setLevel(__import__('logging').DEBUG)
        for h in logger.handlers:
            try:
                h.setLevel(__import__('logging').DEBUG)
            except Exception:
                pass
    else:
        logger.setLevel(__import__('logging').INFO)

    if args.mode == 'novel':
        model_handler = ModelHandler()
        generator = NovelGenerator(model_handler)
        
        if args.action == 'new':
            generator.generate_novel(args.title, args.output_dir, args.chapters)
            print(f"小说生成完成! 保存至: {args.output_dir}/{args.title}")
        elif args.action == 'continue':
            generator.continue_novel(args.title, args.output_dir)
            print(f"小说续写完成! 保存至: {args.output_dir}/{args.title}")
        elif args.action == 'merge':
            blacklist = load_blacklist()
            merge_chapters(os.path.join(args.output_dir, args.title), blacklist)
            print(f"章节合并完成! 完整小说保存至: {args.output_dir}/{args.title}/full_novel.txt")

    elif args.mode == 'video':
        generator = VideoGenerator()
        generator.generate_video(args.input, args.output, args.font)
        print(f"视频生成完成! 保存至: {args.output}")

    elif args.mode == 'other':
        if args.action == 'status':
            view_project_status()
        elif args.action == 'clean':
            cleanup_temp_files()

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
    title = input("请输入小说标题: ").strip()
    if not title:
        print("错误：标题不能为空")
        input("\n按Enter键继续...")
        return
        
    try:
        chapters = int(input("请输入章节数量(默认: 10): ") or "10")
    except ValueError:
        print("错误：请输入有效的数字")
        input("\n按Enter键继续...")
        return
        
    output_dir = input("请输入输出目录(默认: novels): ").strip() or "novels"
    
    try:
        model_handler = ModelHandler()
        generator = NovelGenerator(model_handler)
        generator.generate_novel(title, output_dir, chapters)
        print(f"\n小说生成完成! 保存至: {output_dir}/{title}")
    except Exception as e:
        logger.error(f"小说生成失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def continue_novel():
    """继续生成小说"""
    title = input("请输入小说名称: ").strip()
    if not title:
        print("错误：小说名称不能为空")
        input("\n按Enter键继续...")
        return
        
    try:
        additional_chapters = int(input("请输入要续写的章节数量(默认: 5): ") or "5")
    except ValueError:
        print("错误：请输入有效的数字")
        input("\n按Enter键继续...")
        return
        
    output_dir = input("请输入输出目录(默认: novels): ").strip() or "novels"
    
    try:
        model_handler = ModelHandler()
        generator = NovelGenerator(model_handler)
        generator.continue_novel(title, output_dir, additional_chapters)
        print(f"\n小说续写完成! 保存至: {output_dir}/{title}")
    except Exception as e:
        logger.error(f"小说续写失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def merge_novel_chapters():
    """合并小说章节"""
    novel_dir = input("请输入小说目录路径: ").strip()
    if not novel_dir:
        print("错误：目录路径不能为空")
        input("\n按Enter键继续...")
        return
        
    try:
        blacklist = load_blacklist()
        merge_chapters(novel_dir, blacklist)
        print(f"章节合并完成! 完整小说保存至: {novel_dir}/full_novel.txt")
    except Exception as e:
        logger.error(f"章节合并失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def generate_video_from_text():
    """从文本生成视频"""
    input_file = input("请输入小说文本文件路径: ").strip()
    if not input_file:
        print("错误：文件路径不能为空")
        input("\n按Enter键继续...")
        return
        
    output_file = input("请输入视频输出路径(默认: output.mp4): ").strip() or "output.mp4"
    font_path = input("请输入字体文件路径(默认: resources/SimHei.ttf): ").strip() or "resources/SimHei.ttf"
    
    try:
        generator = VideoGenerator()
        generator.generate_video(input_file, output_file, font_path)
        print(f"\n视频生成完成! 保存至: {output_file}")
    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}")
        print(f"错误: {str(e)}")
    
    input("\n按Enter键继续...")

def generate_video_from_directory():
    """从目录生成视频"""
    directory = input("请输入章节目录路径: ").strip()
    if not directory:
        print("错误：目录路径不能为空")
        input("\n按Enter键继续...")
        return
        
    output_file = input("请输入视频输出路径(默认: output.mp4): ").strip() or "output.mp4"
    font_path = input("请输入字体文件路径(默认: resources/SimHei.ttf): ").strip() or "resources/SimHei.ttf"
    
    try:
        generator = VideoGenerator()
        generator.generate_from_directory(directory, output_file, font_path)
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
    
    try:
        config = load_config()
        print(f"  - 配置文件: 已加载")
        print(f"  - 模型配置: {config.get('ollama', {}).get('model', '未设置')}")
        print(f"  - API端点: {config.get('ollama', {}).get('endpoint', '未设置')}")
    except Exception as e:
        print(f"  - 配置文件: 加载失败 - {str(e)}")
    
    # 检查资源文件
    font_path = os.path.join('resources', 'SimHei.ttf')
    print(f"\n资源文件:")
    print(f"  - 字体文件: {'存在' if os.path.exists(font_path) else '缺失'}")
    
    # 检查输出目录
    novels_dir = 'novels'
    if os.path.exists(novels_dir):
        novels = [d for d in os.listdir(novels_dir) if os.path.isdir(os.path.join(novels_dir, d))]
        print(f"\n已生成小说: {len(novels)} 部")
        if novels:
            print("  " + "\n  ".join(novels[:5]))  # 显示前5部
            if len(novels) > 5:
                print(f"  ... 还有 {len(novels) - 5} 部")
    else:
        print(f"\n已生成小说: 0 部")
    
    input("\n按Enter键继续...")

def cleanup_temp_files():
    """清理临时文件"""
    print("清理临时文件...")
    
    temp_dirs = ['temp', 'cache', '.tmp']
    cleaned = 0
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                cleaned += 1
                print(f"  已清理: {temp_dir}")
            except Exception as e:
                print(f"  清理失败: {temp_dir} - {str(e)}")
    
    if cleaned == 0:
        print("没有找到需要清理的临时文件")
    else:
        print(f"清理完成，共清理 {cleaned} 个目录")
    
    input("\n按Enter键继续...")

def view_config():
    """查看当前配置"""
    clear_screen()
    print("【当前配置】")
    
    try:
        config = load_config()
        print(yaml.dump(config, allow_unicode=True, default_flow_style=False))
    except Exception as e:
        print(f"读取配置失败: {str(e)}")
    
    input("\n按Enter键继续...")

def main():
    """主程序入口"""
    if len(sys.argv) > 1:
        # 命令行模式
        args = parse_arguments()
        run_command_line(args)
    else:
        # 交互式模式
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
                        generate_video_from_directory()
                    elif sub_choice == '3':
                        break
                    else:
                        print("无效选项，请重新输入")
            
            elif choice == '3':  # 配置管理
                while True:
                    sub_choice = config_management_menu()
                    if sub_choice == '1':
                        view_config()
                    elif sub_choice == '2':
                        print("功能开发中...")
                        input("\n按Enter键继续...")
                    elif sub_choice == '3':
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
