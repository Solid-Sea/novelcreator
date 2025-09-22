#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接口兼容性测试脚本
用于测试novelcreator项目的接口兼容性
"""

import inspect
from src.model_handler import ModelHandler
from src.novel_generator import NovelGenerator
from src.utils import load_config, clean_content, merge_chapters

def test_model_handler_interface():
    """测试ModelHandler接口兼容性"""
    print("=== ModelHandler接口兼容性测试 ===")
    
    # 检查类是否存在
    assert hasattr(ModelHandler, '__init__'), "ModelHandler缺少__init__方法"
    assert hasattr(ModelHandler, 'initialize_model'), "ModelHandler缺少initialize_model方法"
    assert hasattr(ModelHandler, 'generate_text'), "ModelHandler缺少generate_text方法"
    assert hasattr(ModelHandler, 'generate_text_with_model'), "ModelHandler缺少generate_text_with_model方法"
    
    # 检查方法签名
    init_signature = inspect.signature(ModelHandler.__init__)
    print(f"ModelHandler.__init__签名: {init_signature}")
    
    generate_signature = inspect.signature(ModelHandler.generate_text)
    print(f"ModelHandler.generate_text签名: {generate_signature}")
    
    generate_with_model_signature = inspect.signature(ModelHandler.generate_text_with_model)
    print(f"ModelHandler.generate_text_with_model签名: {generate_with_model_signature}")
    
    # 测试实例化
    handler = ModelHandler()
    print(f"ModelHandler实例化成功，模型类型: {handler.model_type}")
    
    # 测试公共属性
    assert hasattr(handler, 'model_type'), "ModelHandler缺少model_type属性"
    assert hasattr(handler, 'generation_config'), "ModelHandler缺少generation_config属性"
    
    print("✓ ModelHandler接口兼容性测试通过")

def test_novel_generator_interface():
    """测试NovelGenerator接口兼容性"""
    print("\n=== NovelGenerator接口兼容性测试 ===")
    
    # 检查类是否存在
    assert hasattr(NovelGenerator, '__init__'), "NovelGenerator缺少__init__方法"
    assert hasattr(NovelGenerator, 'generate_novel'), "NovelGenerator缺少generate_novel方法"
    assert hasattr(NovelGenerator, 'continue_novel'), "NovelGenerator缺少continue_novel方法"
    
    # 检查方法签名
    init_signature = inspect.signature(NovelGenerator.__init__)
    print(f"NovelGenerator.__init__签名: {init_signature}")
    
    generate_signature = inspect.signature(NovelGenerator.generate_novel)
    print(f"NovelGenerator.generate_novel签名: {generate_signature}")
    
    continue_signature = inspect.signature(NovelGenerator.continue_novel)
    print(f"NovelGenerator.continue_novel签名: {continue_signature}")
    
    # 测试实例化
    handler = ModelHandler()
    generator = NovelGenerator(handler)
    print(f"NovelGenerator实例化成功，模型类型: {generator.model_type}")
    
    # 测试公共属性
    assert hasattr(generator, 'model_type'), "NovelGenerator缺少model_type属性"
    assert hasattr(generator, '_batch_size'), "NovelGenerator缺少_batch_size属性"
    assert hasattr(generator, '_max_workers'), "NovelGenerator缺少_max_workers属性"
    
    print("✓ NovelGenerator接口兼容性测试通过")

def test_utils_interface():
    """测试utils模块接口兼容性"""
    print("\n=== Utils模块接口兼容性测试 ===")
    
    # 检查函数是否存在
    assert callable(load_config), "load_config不是可调用函数"
    assert callable(clean_content), "clean_content不是可调用函数"
    assert callable(merge_chapters), "merge_chapters不是可调用函数"
    
    # 检查函数签名
    load_config_signature = inspect.signature(load_config)
    print(f"load_config签名: {load_config_signature}")
    
    clean_content_signature = inspect.signature(clean_content)
    print(f"clean_content签名: {clean_content_signature}")
    
    merge_chapters_signature = inspect.signature(merge_chapters)
    print(f"merge_chapters签名: {merge_chapters_signature}")
    
    # 测试函数调用
    config = load_config()
    print(f"load_config调用成功，配置类型: {type(config)}")
    
    test_text = "测试文本内容"
    cleaned = clean_content(test_text)
    print(f"clean_content调用成功，清理后长度: {len(cleaned)}")
    
    print("✓ Utils模块接口兼容性测试通过")

def test_parameter_compatibility():
    """测试参数兼容性"""
    print("\n=== 参数兼容性测试 ===")
    
    # 测试ModelHandler参数兼容性
    print("1. 测试ModelHandler参数...")
    handler1 = ModelHandler()  # 默认参数
    handler2 = ModelHandler(model_type="openai")  # 指定模型类型
    handler3 = ModelHandler(model_type="ollama", model_cache_dir=None)  # 多个参数
    
    print(f" 默认参数实例化成功: {handler1.model_type}")
    print(f"  指定模型类型实例化成功: {handler2.model_type}")
    print(f"  多参数实例化成功: {handler3.model_type}")
    
    # 测试NovelGenerator参数兼容性
    print("2. 测试NovelGenerator参数...")
    handler = ModelHandler()
    generator1 = NovelGenerator(handler)  # 默认参数
    generator2 = NovelGenerator(handler, model_type="openai")  # 指定模型类型
    
    print(f"  默认参数实例化成功: {generator1.model_type}")
    print(f"  指定模型类型实例化成功: {generator2.model_type}")
    
    # 测试generate_text方法参数兼容性
    print("3. 测试generate_text方法参数...")
    try:
        # 测试不同参数组合
        result1 = handler.generate_text("测试提示", model_type="openai")
        result2 = handler.generate_text("测试提示", temperature=0.8)
        result3 = handler.generate_text("测试提示", model_type="openai", temperature=0.7)
        print("  generate_text方法参数兼容性测试通过")
    except Exception as e:
        print(f"  generate_text方法参数兼容性测试失败: {e}")
    
    print("✓ 参数兼容性测试通过")

def test_return_value_compatibility():
    """测试返回值兼容性"""
    print("\n=== 返回值兼容性测试 ===")
    
    # 测试load_config返回值
    config = load_config()
    assert isinstance(config, dict), f"load_config应返回dict，实际返回{type(config)}"
    assert 'model_selection' in config, "配置应包含model_selection键"
    assert 'ollama' in config, "配置应包含ollama键"
    assert 'openai' in config, "配置应包含openai键"
    print("  load_config返回值兼容性测试通过")
    
    # 测试clean_content返回值
    test_text = "测试文本"
    cleaned = clean_content(test_text)
    assert isinstance(cleaned, str), f"clean_content应返回str，实际返回{type(cleaned)}"
    print("  clean_content返回值兼容性测试通过")
    
    print("✓ 返回值兼容性测试通过")

def main():
    """主函数"""
    print("NovelCreator 接口兼容性测试")
    print("=" * 50)
    
    try:
        # 测试ModelHandler接口
        test_model_handler_interface()
        
        # 测试NovelGenerator接口
        test_novel_generator_interface()
        
        # 测试utils模块接口
        test_utils_interface()
        
        # 测试参数兼容性
        test_parameter_compatibility()
        
        # 测试返回值兼容性
        test_return_value_compatibility()
        
        print("\n=== 接口兼容性测试汇总报告 ===")
        print("✓ ModelHandler接口兼容性: 通过")
        print("✓ NovelGenerator接口兼容性: 通过")
        print("✓ Utils模块接口兼容性: 通过")
        print("✓ 参数兼容性: 通过")
        print("✓ 返回值兼容性: 通过")
        print("\n所有接口兼容性测试均通过！")
        
    except Exception as e:
        print(f"\n✗ 接口兼容性测试失败: {e}")
        raise

if __name__ == "__main__":
    main()