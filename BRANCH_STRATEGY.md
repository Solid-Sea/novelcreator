# NovelCreator — 分支策略

## 分支概览

| 分支 | 状态 | 说明 |
|------|------|------|
| `refactor/api-only` | **当前主分支** | 新架构：仅保留 API 调用层，剥离所有本地模型逻辑 |
| `transformers` | 🗄 已归档 (`archive/transformers`) | 含 Transformers/Ollama/OpenAI 三合一模型层的旧架构 |
| `main` | 🗄 已归档 (`archive/main`) | 早期版本，已合并入 transformers |
| `llama-cpp` | 🗄 已归档 (`archive/llama-cpp`) | 实验性 Llama.cpp 支持分支 |

## 归档规则

- 所有历史分支的 tip 已用 `archive/<分支名>` 标签标记，可随时通过标签检出
- 归档后的旧分支不再活跃开发，保留仅用于历史参考
- `git tag -l "archive/*"` 查看所有归档标签

## 新架构分支说明

`refactor/api-only` 是当前开发主分支，遵循以下原则：

- **API Only**：最深只到 OpenAI 兼容 API 调用，无本地模型
- **三层架构**：API 客户端 → Prompt 管理层 → 业务编排层
- **LLM 自清洗**：内容清理由 LLM 自身完成，仅极小正则兜底
- **纯异步**：使用 httpx/asyncio 替代 ThreadPoolExecutor

## 切换工作分支

```bash
# 切到主分支工作
git checkout refactor/api-only

# 如需查看旧代码
git checkout archive/transformers
```
