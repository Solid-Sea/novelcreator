#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
用于测试novelcreator项目的性能指标
"""

import time
import os
import psutil
import gc
from src.model_handler import ModelHandler
from src.novel_generator import NovelGenerator
from src.utils import load_config

def get_memory_usage():
    """获取当前内存使用量(MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def test_model_loading_performance():
    """测试模型加载性能"""
    print("=== 模型加载性能测试 ===")
    
    # 清理内存
    gc.collect()
    
    # 获取初始内存使用
    initial_memory = get_memory_usage()
    print(f"初始内存使用: {initial_memory:.2f} MB")
    
    # 测试模型加载时间
    start_time = time.time()
    start_memory = get_memory_usage()
    
    try:
        handler = ModelHandler()
        generator = NovelGenerator(handler)
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        load_time = end_time - start_time
        memory_increase = end_memory - start_memory
        
        print(f"模型加载时间: {load_time:.2f} 秒")
        print(f"模型加载后内存使用: {end_memory:.2f} MB")
        print(f"内存增加: {memory_increase:.2f} MB")
        
        return {
            'load_time': load_time,
            'initial_memory': initial_memory,
            'end_memory': end_memory,
            'memory_increase': memory_increase
        }
    except Exception as e:
        print(f"模型加载测试失败: {str(e)}")
        return None

def test_chapter_generation_performance():
    """测试章节生成性能"""
    print("\n=== 章节生成性能测试 ===")
    
    try:
        handler = ModelHandler()
        generator = NovelGenerator(handler)
        
        # 准备测试数据
        test_outline = {
            "title": "性能测试小说",
            "total_chapters": 1,
            "story_background": "这是一个用于性能测试的故事背景",
            "main_characters": [
                {
                    "name": "测试角色",
                    "role": "主角",
                    "characteristics": "喜欢测试性能",
                    "relationship": "独自测试"
                }
            ],
            "chapters": [
                {
                    "chapter_num": 1,
                    "title": "性能测试章节",
                    "summary": "测试章节生成性能",
                    "key_events": ["开始测试", "生成内容", "结束测试"],
                    "character_development": "了解性能指标",
                    "plot_points": "获取测试数据"
                }
            ]
        }
        
        # 测试章节生成时间
        start_time = time.time()
        start_memory = get_memory_usage()
        
        # 生成一个测试章节
        chapter_content = generator._generate_chapter_structured(
            title="性能测试小说",
            chapter_num=1,
            outline_data=test_outline
        )
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        generation_time = end_time - start_time
        memory_increase = end_memory - start_memory
        content_length = len(chapter_content) if chapter_content else 0
        
        print(f"章节生成时间: {generation_time:.2f} 秒")
        print(f"生成内容长度: {content_length} 字符")
        print(f"生成前内存使用: {start_memory:.2f} MB")
        print(f"生成后内存使用: {end_memory:.2f} MB")
        print(f"内存增加: {memory_increase:.2f} MB")
        
        return {
            'generation_time': generation_time,
            'content_length': content_length,
            'start_memory': start_memory,
            'end_memory': end_memory,
            'memory_increase': memory_increase
        }
    except Exception as e:
        print(f"章节生成测试失败: {str(e)}")
        return None

def test_parallel_processing_performance():
    """测试并行处理性能"""
    print("\n=== 并行处理性能测试 ===")
    
    try:
        handler = ModelHandler()
        generator = NovelGenerator(handler)
        
        # 获取并行处理配置
        max_workers = generator._max_workers
        batch_size = generator._batch_size
        
        print(f"最大工作线程数: {max_workers}")
        print(f"批处理大小: {batch_size}")
        
        # 测试并发API调用模拟
        import concurrent.futures
        import threading
        
        def worker_task(task_id):
            """工作线程任务"""
            thread_id = threading.current_thread().ident
            start_time = time.time()
            
            # 模拟API调用延迟
            time.sleep(0.1)
            
            end_time = time.time()
            return {
                'task_id': task_id,
                'thread_id': thread_id,
                'execution_time': end_time - start_time
            }
        
        # 测试并发执行
        start_time = time.time()
        start_memory = get_memory_usage()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交多个任务
            futures = [executor.submit(worker_task, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        total_time = end_time - start_time
        memory_increase = end_memory - start_memory
        completed_tasks = len(results)
        
        print(f"并发任务完成数: {completed_tasks}")
        print(f"并发执行时间: {total_time:.2f} 秒")
        print(f"执行前内存使用: {start_memory:.2f} MB")
        print(f"执行后内存使用: {end_memory:.2f} MB")
        print(f"内存增加: {memory_increase:.2f} MB")
        
        # 分析线程使用情况
        thread_ids = set(result['thread_id'] for result in results)
        print(f"使用线程数: {len(thread_ids)}")
        
        return {
            'total_time': total_time,
            'completed_tasks': completed_tasks,
            'start_memory': start_memory,
            'end_memory': end_memory,
            'memory_increase': memory_increase,
            'thread_count': len(thread_ids)
        }
    except Exception as e:
        print(f"并行处理测试失败: {str(e)}")
        return None

def main():
    """主函数"""
    print("NovelCreator 性能测试")
    print("=" * 50)
    
    # 测试模型加载性能
    model_results = test_model_loading_performance()
    
    # 测试章节生成性能
    chapter_results = test_chapter_generation_performance()
    
    # 测试并行处理性能
    parallel_results = test_parallel_processing_performance()
    
    # 输出汇总报告
    print("\n=== 性能测试汇总报告 ===")
    if model_results:
        print(f"模型加载时间: {model_results['load_time']:.2f} 秒")
        print(f"模型加载内存增加: {model_results['memory_increase']:.2f} MB")
    
    if chapter_results:
        print(f"章节生成时间: {chapter_results['generation_time']:.2f} 秒")
        print(f"生成内容长度: {chapter_results['content_length']} 字符")
        print(f"章节生成内存增加: {chapter_results['memory_increase']:.2f} MB")
    
    if parallel_results:
        print(f"并发执行时间: {parallel_results['total_time']:.2f} 秒")
        print(f"并发任务完成数: {parallel_results['completed_tasks']}")
        print(f"并发执行内存增加: {parallel_results['memory_increase']:.2f} MB")
        print(f"使用线程数: {parallel_results['thread_count']}")

if __name__ == "__main__":
    main()