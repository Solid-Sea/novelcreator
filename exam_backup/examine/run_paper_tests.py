#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行论文数据测试的脚本
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_test_framework import PaperTestFramework

def main():
    """主函数"""
    print("NovelCreator 论文数据测试执行器")
    print("=" * 60)
    
    # 创建测试框架实例
    framework = PaperTestFramework()
    
    # 运行所有测试
    results = framework.run_all_tests()
    
    # 保存结果到examine_2文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"paper_test_results_{timestamp}.json"
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examine_2', results_file)
    # 确保examine_2文件夹存在
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到: {results_path}")
    
    print("\n" + "=" * 60)
    print("论文数据测试完成!")

if __name__ == "__main__":
    main()