#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成脚本
用于执行所有测试并生成综合报告
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance_test import test_model_loading_performance, test_chapter_generation_performance, test_parallel_processing_performance
from memory_test import test_memory_optimization, test_memory_leak, test_streaming_file_processing
from interface_test import test_model_handler_interface, test_novel_generator_interface, test_utils_interface
from error_handling_test import test_model_handler_error_handling, test_novel_generator_error_handling, test_utils_error_handling

def run_all_tests():
    """运行所有测试并生成报告"""
    print("开始执行全面测试...")
    print("=" * 60)
    
    # 存储测试结果
    results = {
        'timestamp': datetime.now().isoformat(),
        'performance': {},
        'memory': {},
        'interface': {},
        'error_handling': {}
    }
    
    # 性能测试
    print("\n1. 执行性能测试...")
    try:
        results['performance']['model_loading'] = test_model_loading_performance()
        results['performance']['chapter_generation'] = test_chapter_generation_performance()
        results['performance']['parallel_processing'] = test_parallel_processing_performance()
        print("✓ 性能测试完成")
    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        results['performance']['error'] = str(e)
    
    # 内存测试
    print("\n2. 执行内存测试...")
    try:
        results['memory']['optimization'] = test_memory_optimization()
        results['memory']['leak_test'] = test_memory_leak()
        results['memory']['streaming'] = test_streaming_file_processing()
        print("✓ 内存测试完成")
    except Exception as e:
        print(f"✗ 内存测试失败: {e}")
        results['memory']['error'] = str(e)
    
    # 接口测试
    print("\n3. 执行接口测试...")
    try:
        test_model_handler_interface()
        test_novel_generator_interface()
        test_utils_interface()
        results['interface']['status'] = 'passed'
        print("✓ 接口测试完成")
    except Exception as e:
        print(f"✗ 接口测试失败: {e}")
        results['interface']['status'] = 'failed'
        results['interface']['error'] = str(e)
    
    # 错误处理测试
    print("\n4. 执行错误处理测试...")
    try:
        test_model_handler_error_handling()
        test_novel_generator_error_handling()
        test_utils_error_handling()
        results['error_handling']['status'] = 'passed'
        print("✓ 错误处理测试完成")
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        results['error_handling']['status'] = 'failed'
        results['error_handling']['error'] = str(e)
    
    return results

def generate_report(results):
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("测试报告生成中...")
    
    # 创建报告内容
    report_content = f"""
# NovelCreator 测试报告

**生成时间**: {results['timestamp']}

## 性能测试结果

### 模型加载性能
- 加载时间: {results['performance'].get('model_loading', {}).get('load_time', 'N/A'):.2f} 秒
- 内存增加: {results['performance'].get('model_loading', {}).get('memory_increase', 'N/A'):.2f} MB

### 章节生成性能
- 生成时间: {results['performance'].get('chapter_generation', {}).get('generation_time', 'N/A'):.2f} 秒
- 内容长度: {results['performance'].get('chapter_generation', {}).get('content_length', 'N/A')} 字符
- 内存增加: {results['performance'].get('chapter_generation', {}).get('memory_increase', 'N/A'):.2f} MB

### 并行处理性能
- 执行时间: {results['performance'].get('parallel_processing', {}).get('total_time', 'N/A'):.2f} 秒
- 完成任务数: {results['performance'].get('parallel_processing', {}).get('completed_tasks', 'N/A')}
- 使用线程数: {results['performance'].get('parallel_processing', {}).get('thread_count', 'N/A')}

## 内存测试结果

### 内存优化效果
- 初始内存: {results['memory'].get('optimization', {}).get('initial_memory', 'N/A'):.2f} MB
- 最终内存: {results['memory'].get('optimization', {}).get('final_memory', 'N/A'):.2f} MB
- 内存变化: {results['memory'].get('optimization', {}).get('memory_difference', 'N/A'):.2f} MB

### 流式文件处理
- 内存节省: {results['memory'].get('streaming', {}).get('memory_saving', 'N/A'):.2f} MB

## 接口测试结果
- 状态: {results['interface'].get('status', 'N/A')}

## 错误处理测试结果
- 状态: {results['error_handling'].get('status', 'N/A')}
"""
    
    # 保存报告
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 保存JSON格式的详细结果
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 测试报告已保存到: {report_path}")
    print(f"✓ 详细结果已保存到: {json_path}")
    
    return report_content

def main():
    """主函数"""
    print("NovelCreator 综合测试报告生成器")
    print("=" * 60)
    
    # 运行所有测试
    results = run_all_tests()
    
    # 生成报告
    report = generate_report(results)
    
    print("\n" + "=" * 60)
    print("测试完成!")

if __name__ == "__main__":
    main()