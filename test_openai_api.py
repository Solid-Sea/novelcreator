#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OpenAI兼容API配置的脚本
"""

import sys
import os
import logging

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_handler import ModelHandler
from src.utils import load_config

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_openai_config():
    """测试OpenAI配置"""
    print("🔍 测试OpenAI配置...")
    
    try:
        config = load_config()
        print(f"✅ 配置文件加载成功")
        
        if 'openai' in config:
            openai_config = config['openai']
            print(f"✅ OpenAI配置存在")
            print(f"   API密钥: {openai_config.get('api_key', '未设置')[:10]}...")  # 只显示前10位
            print(f"   基础URL: {openai_config.get('base_url', '未设置')}")
            print(f"   模型: {openai_config.get('model', '未设置')}")
            return True
        else:
            print("❌ OpenAI配置不存在")
            return False
            
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        return False

def test_openai_connection():
    """测试OpenAI API连接"""
    print("\n🔍 测试OpenAI API连接...")
    
    try:
        model_handler = ModelHandler(model_type="openai")
        print("✅ ModelHandler初始化成功")
        
        # 测试简单的生成请求
        test_prompt = "请用一句话回答：你好世界！"
        print(f"📝 测试提示: {test_prompt}")
        
        response = model_handler.generate_text(test_prompt, model_type="openai", temperature=0.7)
        print(f"✅ API调用成功")
        print(f"📝 生成结果: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ API调用失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🧪 OpenAI兼容API配置测试")
    print("=" * 50)
    
    setup_logging()
    
    # 测试配置
    config_ok = test_openai_config()
    
    # 测试连接
    connection_ok = False
    if config_ok:
        connection_ok = test_openai_connection()
    
    print("\n" + "=" * 50)
    if config_ok and connection_ok:
        print("🎉 所有测试通过!")
        print("✅ OpenAI兼容API配置正确且可访问")
        return 0
    else:
        print("⚠️  测试失败!")
        if not config_ok:
            print("❌ OpenAI配置存在问题")
        if not connection_ok:
            print("❌ API连接存在问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
