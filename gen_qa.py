#!/usr/bin/env python3
"""生成 3 章小说供质量评估"""
import sys
sys.path.insert(0, '.')

from api_client import APIClient
from src.utils import load_config
from services.generator_orchestrator import GeneratorOrchestrator

config = load_config()
api = APIClient(config)
orch = GeneratorOrchestrator(api)

title = '质量评估测试'
orch.generate_novel(title, chapters=3)
print('生成完成')
