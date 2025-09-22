#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存使用测试脚本
用于测试novelcreator项目的内存使用情况和优化效果
"""

import time
import os
import psutil
import gc
import tracemalloc
from src.model_handler import ModelHandler
from src.novel_generator import NovelGenerator
from src.utils import clean_content

def get_memory_usage():
    """获取当前内存使用量(MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def test_memory_optimization():
    """测试内存优化效果"""
    print("=== 内存优化效果测试 ===")
    
    # 开始内存追踪
    tracemalloc.start()
    
    # 获取初始内存使用
    initial_memory = get_memory_usage()
    print(f"初始内存使用: {initial_memory:.2f} MB")
    
    # 1. 测试模型处理器初始化的内存使用
    print("\n1. 测试模型处理器初始化内存使用...")
    start_memory = get_memory_usage()
    snapshot1 = tracemalloc.take_snapshot()
    
    handler = ModelHandler()
    
    end_memory = get_memory_usage()
    snapshot2 = tracemalloc.take_snapshot()
    memory_increase = end_memory - start_memory
    
    print(f"模型处理器初始化后内存使用: {end_memory:.2f} MB")
    print(f"内存增加: {memory_increase:.2f} MB")
    
    # 显示内存分配最多的部分
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    print("内存分配最多的前3个位置:")
    for stat in top_stats[:3]:
        print(f"  {stat}")
    
    # 2. 测试小说生成器初始化的内存使用
    print("\n2. 测试小说生成器初始化内存使用...")
    start_memory = get_memory_usage()
    snapshot1 = tracemalloc.take_snapshot()
    
    generator = NovelGenerator(handler)
    
    end_memory = get_memory_usage()
    snapshot2 = tracemalloc.take_snapshot()
    memory_increase = end_memory - start_memory
    
    print(f"小说生成器初始化后内存使用: {end_memory:.2f} MB")
    print(f"内存增加: {memory_increase:.2f} MB")
    
    # 显示内存分配最多的部分
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    print("内存分配最多的前3个位置:")
    for stat in top_stats[:3]:
        print(f"  {stat}")
    
    # 3. 测试内容清理功能的内存使用
    print("\n3. 测试内容清理功能内存使用...")
    # 创建一个大的测试文本
    large_text = "这是一个测试文本。" * 10000
    
    start_memory = get_memory_usage()
    snapshot1 = tracemalloc.take_snapshot()
    
    # 执行内容清理
    cleaned_text = clean_content(large_text, None)
    
    end_memory = get_memory_usage()
    snapshot2 = tracemalloc.take_snapshot()
    memory_increase = end_memory - start_memory
    
    print(f"原始文本长度: {len(large_text)} 字符")
    print(f"清理后文本长度: {len(cleaned_text)} 字符")
    print(f"内容清理后内存使用: {end_memory:.2f} MB")
    print(f"内存增加: {memory_increase:.2f} MB")
    
    # 显示内存分配最多的部分
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    print("内存分配最多的前3个位置:")
    for stat in top_stats[:3]:
        print(f"  {stat}")
    
    # 4. 测试垃圾回收后的内存释放
    print("\n4. 测试垃圾回收后的内存释放...")
    del handler, generator, large_text, cleaned_text
    
    gc.collect()  # 强制垃圾回收
    
    final_memory = get_memory_usage()
    print(f"垃圾回收后内存使用: {final_memory:.2f} MB")
    print(f"相比初始内存变化: {final_memory - initial_memory:.2f} MB")
    
    # 停止内存追踪
    tracemalloc.stop()
    
    return {
        'initial_memory': initial_memory,
        'final_memory': final_memory,
        'memory_difference': final_memory - initial_memory
    }

def test_memory_leak():
    """测试内存泄漏"""
    print("\n=== 内存泄漏测试 ===")
    
    initial_memory = get_memory_usage()
    print(f"初始内存使用: {initial_memory:.2f} MB")
    
    # 多次初始化和销毁对象，检查内存是否持续增长
    memory_readings = []
    
    for i in range(5):
        print(f"\n第 {i+1} 次对象初始化/销毁...")
        
        # 初始化对象
        handler = ModelHandler()
        generator = NovelGenerator(handler)
        
        # 记录内存使用
        current_memory = get_memory_usage()
        memory_readings.append(current_memory)
        print(f"  内存使用: {current_memory:.2f} MB")
        
        # 销毁对象
        del handler, generator
        gc.collect()
        
        # 等待一段时间
        time.sleep(0.1)
    
    final_memory = get_memory_usage()
    print(f"\n最终内存使用: {final_memory:.2f} MB")
    
    # 分析内存变化趋势
    memory_growth = final_memory - initial_memory
    print(f"总内存增长: {memory_growth:.2f} MB")
    
    # 检查是否有持续增长的趋势
    if len(memory_readings) > 1:
        differences = [memory_readings[i] - memory_readings[i-1] for i in range(1, len(memory_readings))]
        avg_difference = sum(differences) / len(differences)
        print(f"平均每次循环内存变化: {avg_difference:.2f} MB")
        
        if avg_difference > 1.0:  # 如果平均每次增长超过1MB，可能存在内存泄漏
            print("警告: 检测到可能的内存泄漏趋势")
            return False
        else:
            print("未检测到明显的内存泄漏")
            return True
    
    return abs(memory_growth) < 5.0 # 如果总增长小于5MB，认为没有内存泄漏

def test_streaming_file_processing():
    """测试流式文件处理是否降低了内存占用"""
    print("\n=== 流式文件处理测试 ===")
    
    # 创建一个大的测试文件
    test_file = "test_large_file.txt"
    print(f"创建测试文件: {test_file}")
    
    # 创建一个大的测试文件 (约1MB)
    with open(test_file, 'w', encoding='utf-8') as f:
        for i in range(10000):
            f.write(f"这是第 {i+1} 行测试内容，用于测试流式文件处理功能。\n")
    
    try:
        initial_memory = get_memory_usage()
        print(f"初始内存使用: {initial_memory:.2f} MB")
        
        # 测试传统的文件读取方式 (一次性加载)
        print("\n1. 测试传统文件读取方式...")
        start_memory = get_memory_usage()
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()  # 一次性读取整个文件
        
        traditional_memory = get_memory_usage()
        traditional_increase = traditional_memory - start_memory
        print(f"传统方式内存增加: {traditional_increase:.2f} MB")
        
        # 清理
        del content
        gc.collect()
        
        # 测试流式文件处理方式
        print("\n2. 测试流式文件处理方式...")
        start_memory = get_memory_usage()
        
        # 模拟流式处理 (逐行读取)
        line_count = 0
        with open(test_file, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                # 模拟处理每一行
                if line_count % 1000 == 0:
                    # 模拟处理过程中的内存使用
                    processed = line.strip()
        
        streaming_memory = get_memory_usage()
        streaming_increase = streaming_memory - start_memory
        print(f"流式处理内存增加: {streaming_increase:.2f} MB")
        print(f"处理行数: {line_count}")
        
        # 比较两种方式
        print(f"\n内存使用比较:")
        print(f"  传统方式: {traditional_increase:.2f} MB")
        print(f"  流式处理: {streaming_increase:.2f} MB")
        print(f"  内存节省: {traditional_increase - streaming_increase:.2f} MB")
        
        # 清理
        del line_count
        gc.collect()
        
        return {
            'traditional_increase': traditional_increase,
            'streaming_increase': streaming_increase,
            'memory_saving': traditional_increase - streaming_increase
        }
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n已删除测试文件: {test_file}")

def main():
    """主函数"""
    print("NovelCreator 内存使用测试")
    print("=" * 50)
    
    # 测试内存优化效果
    optimization_results = test_memory_optimization()
    
    # 测试内存泄漏
    leak_test_passed = test_memory_leak()
    
    # 测试流式文件处理
    streaming_results = test_streaming_file_processing()
    
    # 输出汇总报告
    print("\n=== 内存使用测试汇总报告 ===")
    print(f"初始内存: {optimization_results['initial_memory']:.2f} MB")
    print(f"最终内存: {optimization_results['final_memory']:.2f} MB")
    print(f"内存变化: {optimization_results['memory_difference']:.2f} MB")
    
    if leak_test_passed:
        print("✓ 内存泄漏测试: 通过")
    else:
        print("✗ 内存泄漏测试: 未通过")
    
    if streaming_results:
        print(f"流式处理内存节省: {streaming_results['memory_saving']:.2f} MB")

if __name__ == "__main__":
    main()