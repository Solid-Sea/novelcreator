# NovelCreator 配置示例

## Ollama配置示例

### 1. 基本Ollama配置

```yaml
# Ollama模型配置
ollama:
  endpoint: "http://localhost:11434"  # Ollama API端点
  model: "phi3:3.8b"                  # 默认使用模型
  hf_model: "unsloth/DeepSeek-R1-Distill-Qwen-14B"  # HuggingFace模型名称
  trust_remote_code: true             # 仅在启用本地TF模式时生效

  # 任务特定模型配置
  models:
    outline: "qwen3:8b"                # 大纲生成模型
    review: "phi3:3.8b"                # 评论/审查模型
    content: "deepseek-r1:14b"         # 正文生成模型
```

### 2. 本地模型文件配置

```yaml
# Ollama配置（使用本地模型文件）
ollama:
  endpoint: "http://localhost:11434"  # Ollama API端点
  model: "llama3:8b"                  # 默认使用模型
  hf_model: "./models/llama3_8b"      # 本地模型文件路径
  trust_remote_code: false            # 仅在启用本地TF模式时生效
```

## OpenAI兼容API配置示例

### 1. OpenRouter配置示例

```yaml
# OpenAI兼容API配置（使用OpenRouter）
openai:
  api_key: "your-openrouter-api-key-here"        # 你的OpenRouter API密钥
  base_url: "https://openrouter.ai/api/v1"       # OpenRouter API基础URL
  model: "openai/gpt-3.5-turbo"                  # 默认模型
  
  # 任务特定模型配置
  models:
    outline: "z-ai/glm-4.5-air:free"             # 大纲生成模型（免费）
    review: "moonshotai/kimi-k2:free"            # 评论/审查模型（免费）
    content: "deepseek/deepseek-r1-0528:free"    # 正文生成模型（免费）
```

### 2. 零一万物配置示例

```yaml
# OpenAI兼容API配置（使用零一万物）
openai:
  api_key: "your-yi-api-key-here"                # 你的零一万物API密钥
  base_url: "https://api.lingyiwanwu.com/v1"     # 零一万物API基础URL
  model: "yi-large"                              # 默认模型
  
  # 任务特定模型配置
  models:
    outline: "yi-medium"                         # 大纲生成模型
    review: "yi-light"                           # 评论/审查模型
    content: "yi-large"                          # 正文生成模型
```

### 3. DeepSeek配置示例

```yaml
# OpenAI兼容API配置（使用DeepSeek）
openai:
  api_key: "your-deepseek-api-key-here"          # 你的DeepSeek API密钥
  base_url: "https://api.deepseek.com/v1"        # DeepSeek API基础URL
  model: "deepseek-chat"                         # 默认模型
  
  # 任务特定模型配置
  models:
    outline: "deepseek-chat"                     # 大纲生成模型
    review: "deepseek-chat"                      # 评论/审查模型
    content: "deepseek-chat"                     # 正文生成模型
```

## 模型类型选择使用示例

### 命令行使用

```bash
# 使用OpenAI兼容API生成小说
python main.py novel --action new --title "我的小说" --chapters 5 --model-type openai

# 使用Ollama生成小说
python main.py novel --action new --title "我的小说" --chapters 5 --model-type ollama
```

### 交互式模式

在交互式模式中，系统会提示你选择模型类型：

```
请选择模型类型:
1. Ollama (本地模型)
2. OpenAI兼容API (如OpenRouter)
请输入选项编号 (默认: 2): 2
```

## 任务特定模型说明

不同的创作任务可以使用不同的模型来优化效果：

- **outline**: 大纲生成 - 适合使用思维链较强的模型
- **review**: 内容审查 - 适合使用分析能力强的模型
- **content**: 正文生成 - 适合使用创作能力强的模型

## API密钥安全

建议使用环境变量来存储API密钥：

```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"
```

然后在配置文件中使用：
```yaml
openai:
  api_key: ${OPENAI_API_KEY}  # 从环境变量读取
  base_url: "https://api.openai.com/v1"
  model: "gpt-3.5-turbo"
