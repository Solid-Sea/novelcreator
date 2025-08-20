#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置测试脚本
用于验证所有依赖和配置是否正确设置
"""

import sys
import os
import importlib.util

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        return False

def check_package_installed(package_name, import_name=None):
    """检查包是否已安装"""
    if import_name is None:
        import_name = package_name
    
    print(f"🔍 检查 {package_name}...")
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            print(f"✅ {package_name} 已安装")
            return True
        else:
            print(f"❌ {package_name} 未安装")
            return False
    except ImportError:
        print(f"❌ {package_name} 未安装")
        return False

def check_ollama_service():
    """检查Ollama服务是否可用"""
    print("🔍 检查Ollama服务...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Ollama服务正常，可用模型: {[model['name'] for model in models['models']]}")
            return True
        else:
            print(f"❌ Ollama服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama服务不可用: {str(e)}")
        return False

def check_font_file():
    """检查字体文件是否存在"""
    print("🔍 检查字体文件...")
    font_path = os.path.join("resources", "SimHei.ttf")
    if os.path.exists(font_path):
        print(f"✅ 字体文件存在: {font_path}")
        return True
    else:
        print(f"❌ 字体文件不存在: {font_path}")
        return False

def check_config_files():
    """检查配置文件是否存在"""
    print("🔍 检查配置文件...")
    config_files = [
        ("主配置文件", os.path.join("config", "config.yaml")),
        ("黑名单配置", os.path.join("config", "blacklist.yaml"))
    ]
    
    all_exist = True
    for name, path in config_files:
        if os.path.exists(path):
            print(f"✅ {name}存在: {path}")
        else:
            print(f"❌ {name}不存在: {path}")
            all_exist = False
    
    return all_exist

def main():
    """主函数"""
    print("🧪 NovelCreator环境配置测试")
    print("=" * 50)
    
    checks = [
        check_python_version,
        lambda: check_package_installed("torch"),
        lambda: check_package_installed("transformers"),
        lambda: check_package_installed("PyYAML", "yaml"),
        lambda: check_package_installed("requests"),
        lambda: check_package_installed("tqdm"),
        lambda: check_package_installed("opencv-python", "cv2"),
        lambda: check_package_installed("pillow", "PIL"),
        lambda: check_package_installed("moviepy"),
        lambda: check_package_installed("numpy"),
        lambda: check_package_installed("openai"),
        check_ollama_service,
        check_font_file,
        check_config_files
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ 检查过程中出错: {str(e)}")
            results.append(False)
        print()
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有检查通过 ({passed}/{total})")
        print("✅ 环境配置完成，可以开始使用NovelCreator!")
        return 0
    else:
        print(f"⚠️  部分检查失败 ({passed}/{total})")
        print("请检查上述错误并修复后再试。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
