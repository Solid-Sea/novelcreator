#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# NovelCreator — CLI 入口

import os
import sys
import argparse

from src.utils import load_config, logger, show_progress, get_progress
from api_client import APIClient
from services.generator_orchestrator import GeneratorOrchestrator


def parse_arguments():
    parser = argparse.ArgumentParser(description='NovelCreator — 小说创作工具')
    subparsers = parser.add_subparsers(dest='mode', help='操作模式')

    # 小说模式
    novel = subparsers.add_parser('novel', help='小说生成')
    novel.add_argument('--action', choices=['new', 'continue', 'merge'], required=True)
    novel.add_argument('--title', required=True, help='小说标题')
    novel.add_argument('--chapters', type=int, default=10, help='章节数量')
    novel.add_argument('--output-dir', default='novels', help='输出目录')

    # 视频模式
    video = subparsers.add_parser('video', help='视频生成')
    video.add_argument('--input', required=True, help='输入文本文件')
    video.add_argument('--output', default='output.mp4', help='输出视频文件')
    video.add_argument('--font', default='resources/SimHei.ttf', help='字体文件')

    # 通用参数
    parser.add_argument('--verbose', action='store_true', help='详细日志')
    parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')
    return parser.parse_args()


def run_command(args):
    config = load_config()
    api = APIClient(config)

    if args.mode == 'novel':
        orch = GeneratorOrchestrator(api, novels_dir=args.output_dir)

        if args.action == 'new':
            orch.generate_novel(args.title, args.chapters)
            print(f'小说生成完成: {args.output_dir}/{args.title}/')

        elif args.action == 'continue':
            orch.continue_novel(args.title, 5)
            print(f'小说续写完成: {args.output_dir}/{args.title}/')

        elif args.action == 'merge':
            from src.utils import merge_chapters
            merge_chapters(os.path.join(args.output_dir, args.title))
            print(f'合并完成: {args.output_dir}/{args.title}/full_novel.txt')

    elif args.mode == 'video':
        from src.video_generator import VideoGenerator
        vg = VideoGenerator()
        vg.generate_video(args.input, args.output, args.font)
        print(f'视频生成完成: {args.output}')


def main():
    if len(sys.argv) > 1:
        args = parse_arguments()
        if args.verbose:
            logger.setLevel(__import__('logging').DEBUG)
            for h in logger.handlers:
                try:
                    h.setLevel(__import__('logging').DEBUG)
                except Exception:
                    pass
        run_command(args)
    else:
        _interactive_mode()


# ── 交互式模式（精简，保留兼容） ──────────────────────────

def _interactive_mode():
    config = load_config()
    api = APIClient(config)

    while True:
        print('\n=== NovelCreator ===')
        print('1. 生成新小说')
        print('2. 续写小说')
        print('3. 生成视频')
        print('4. 退出')
        choice = input('\n请选择: ').strip()

        if choice == '1':
            title = input('小说标题: ').strip()
            if not title:
                continue
            try:
                chapters = int(input('章节数 (默认 10): ') or '10')
            except ValueError:
                continue
            orch = GeneratorOrchestrator(api)
            orch.generate_novel(title, chapters)
            input('\n按 Enter 继续...')

        elif choice == '2':
            title = input('小说标题: ').strip()
            if not title:
                continue
            try:
                extra = int(input('续写章节数 (默认 5): ') or '5')
            except ValueError:
                continue
            orch = GeneratorOrchestrator(api)
            orch.continue_novel(title, extra)
            input('\n按 Enter 继续...')

        elif choice == '3':
            from src.video_generator import VideoGenerator
            input_file = input('输入文件路径: ').strip()
            if not input_file:
                continue
            output = input('输出路径 (默认 output.mp4): ').strip() or 'output.mp4'
            font = input('字体 (默认 resources/SimHei.ttf): ').strip() or 'resources/SimHei.ttf'
            vg = VideoGenerator()
            vg.generate_video(input_file, output, font)
            input('\n按 Enter 继续...')

        elif choice == '4':
            print('再见!')
            sys.exit(0)


if __name__ == '__main__':
    main()
