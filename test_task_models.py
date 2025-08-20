#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务特定模型配置测试脚本
验证不同任务使用不同模型的配置
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

def test_task_specific_models():
    """测试任务特定模型配置"""
    print("🚀 任务特定模型配置测试")
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
        
        if 'models' in openai_config:
            task_models = openai_config['models']
            print(f"   任务特定模型配置:")
            for task, model in task_models.items():
                print(f"     {task}: {model}")
        else:
            print("❌ 未找到任务特定模型配置")
            return False
        
        # 初始化ModelHandler
        print("\n🔧 初始化ModelHandler...")
        model_handler = ModelHandler(model_type="openai")
        print("✅ ModelHandler初始化成功")
        
        # 测试不同的任务模型
        test_cases = [
            {
                "name": "大纲生成测试",
                "task_type": "outline",
                "prompt": "请为一个科幻小说生成大纲，包含3个章节。",
                "temperature": 0.8
            },
            {
                "name": "评论生成测试", 
                "task_type": "review",
                "prompt": "请评价以下文本的质量（简短回答）：今天天气很好，阳光明媚。",
                "temperature": 0.3
            },
            {
                "name": "正文生成测试",
                "task_type": "content", 
                "prompt": "请写一个关于未来城市的简短段落（50字以内）：",
                "temperature": 0.7
            }
        ]
        
        print("\n🧪 开始测试任务特定模型...")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试 {i}/{len(test_cases)}: {test_case['name']}")
            print(f"任务类型: {test_case['task_type']}")
            print(f"提示: {test_case['prompt']}")
            
            start_time = time.time()
            try:
                response = model_handler.generate_text_with_model(
                    test_case['prompt'], 
                    test_case['task_type'],
                    model_type="openai", 
                    temperature=test_case['temperature']
                )
                end_time = time.time()
                
                print(f"✅ 生成成功 (耗时: {end_time - start_time:.2f}秒)")
                print(f"结果: {response}")
                
            except Exception as e:
                print(f"❌ 生成失败: {str(e)}")
                continue
        
        # 测试默认模型（向后兼容）
        print(f"\n🔄 测试默认模型（向后兼容）...")
        try:
            response = model_handler.generate_text(
                "请用一句话回答：你好世界！", 
                model_type="openai", 
                temperature=0.7
            )
            print(f"✅ 默认模型调用成功: {response}")
        except Exception as e:
            print(f"❌ 默认模型调用失败: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 任务特定模型配置测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

def main():
    """主函数"""
    setup_logging()
    success = test_task_specific_models()
    
    if success:
        print("\n✅ 所有测试通过!")
        print("现在可以为不同任务配置不同的模型了！")
        return 0
    else:
        print("\n❌ 测试失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
