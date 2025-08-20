#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI兼容API使用演示脚本
展示如何使用OpenRouter等OpenAI兼容的API服务
"""

import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_handler import ModelHandler
from src.utils import load_config, logger

def setup_logging():
    """设置日志"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def demonstrate_openai_api():
    """演示OpenAI兼容API的使用"""
    print("🚀 OpenAI兼容API使用演示")
    print("=" * 50)
    
    try:
        # 加载配置
        config = load_config()
        print("✅ 配置文件加载成功")
        
        if 'openai' not in config:
            print("❌ 未找到OpenAI配置")
            return False
            
        openai_config = config['openai']
        print(f"📡 API配置:")
        print(f"   基础URL: {openai_config.get('base_url', '未设置')}")
        print(f"   模型: {openai_config.get('model', '未设置')}")
        
        # 初始化ModelHandler
        print("\n🔧 初始化ModelHandler...")
        model_handler = ModelHandler(model_type="openai")
        print("✅ ModelHandler初始化成功")
        
        # 测试不同的生成任务
        test_cases = [
            {
                "name": "简单问答",
                "prompt": "请用一句话回答：人工智能的未来发展方向是什么？",
                "temperature": 0.7
            },
            {
                "name": "创意写作",
                "prompt": "请写一个关于未来城市的简短故事开头（50字以内）：",
                "temperature": 0.8
            },
            {
                "name": "技术解释",
                "prompt": "请简单解释什么是大语言模型，适合初学者理解：",
                "temperature": 0.3
            }
        ]
        
        print("\n🧪 开始测试生成任务...")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试 {i}/{len(test_cases)}: {test_case['name']}")
            print(f"提示: {test_case['prompt']}")
            
            start_time = time.time()
            try:
                response = model_handler.generate_text(
                    test_case['prompt'], 
                    model_type="openai", 
                    temperature=test_case['temperature']
                )
                end_time = time.time()
                
                print(f"✅ 生成成功 (耗时: {end_time - start_time:.2f}秒)")
                print(f"结果: {response}")
                
            except Exception as e:
                print(f"❌ 生成失败: {str(e)}")
                continue
        
        print("\n" + "=" * 50)
        print("🎉 OpenAI兼容API演示完成!")
        return True
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")
        return False

def main():
    """主函数"""
    setup_logging()
    success = demonstrate_openai_api()
    
    if success:
        print("\n✅ 演示成功完成!")
        print("现在您可以:")
        print("1. 修改 config/config.yaml 中的OpenAI配置")
        print("2. 运行主程序使用OpenAI兼容API生成小说")
        print("3. 尝试不同的模型和参数设置")
        return 0
    else:
        print("\n❌ 演示失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
