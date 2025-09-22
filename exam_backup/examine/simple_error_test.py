#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版错误处理测试
"""

from src.model_handler import ModelHandler
from src.novel_generator import NovelGenerator
from src.utils import clean_content

def test_error_handling():
    """测试错误处理"""
    print("开始错误处理测试...")
    
    # 测试1: ModelHandler初始化
    try:
        handler = ModelHandler()
        print("✓ ModelHandler初始化成功")
    except Exception as e:
        print(f"✗ ModelHandler初始化失败: {e}")
        return False
    
    # 测试2: NovelGenerator初始化
    try:
        generator = NovelGenerator(handler)
        print("✓ NovelGenerator初始化成功")
    except Exception as e:
        print(f"✗ NovelGenerator初始化失败: {e}")
        return False
    
    # 测试3: clean_content处理None值
    try:
        result = clean_content(None)
        print("✓ clean_content处理None值成功")
    except Exception as e:
        print(f"✗ clean_content处理None值失败: {e}")
        return False
    
    # 测试4: 无效模型类型
    try:
        handler_invalid = ModelHandler(model_type="invalid_model_type")
        print("  警告: 无效模型类型未被拒绝")
    except Exception as e:
        print(f"✓ 无效模型类型被正确拒绝: {type(e).__name__}")
    
    print("所有错误处理测试完成!")
    return True

if __name__ == "__main__":
    test_error_handling()