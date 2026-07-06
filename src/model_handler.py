# -*- coding: utf-8 -*-
# 此文件已弃用 — 所有功能迁移至 api_client.py + services/
# model_type、torch、transformers 等概念已全部移除

import logging
logger = logging.getLogger('ModelHandler')

class ModelHandler:
    """兼容桩 — 旧代码调用时会报错提示迁移。

    迁移指南：
    from api_client import APIClient
    client = APIClient(config)
    response = client.chat_completion(messages=[...], task_type=...)
    """
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            'ModelHandler 已移除。请使用 api_client.APIClient 替代。\n'
            '旧: model_handler.generate_text(prompt, model_type, temperature)\n'
            '新: api_client.chat_completion(messages=[{"role":"user","content":prompt}], temperature=...)'
        )
