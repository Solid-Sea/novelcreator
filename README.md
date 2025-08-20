# NovelCreator Transformer

一个利用大模型服务自动生成小说的工具链，包含小说生成、文本处理和视频合成功能。

## 🚀 快速开始

1. **确保环境准备就绪**：
   ```bash
   # 检查Python版本
   python --version
   
   # 检查Ollama服务
   curl http://localhost:11434/api/tags
   ```

2. **生成你的第一部小说**：
   ```bash
   # 生成一个简单的5章小说
   python main.py novel --action new --title "我的第一部小说" --chapters 5
   
   # 查看生成结果
   ls novels/我的第一部小说/
   ```

3. **将小说转换为视频**：
   ```bash
   # 生成视频
   python main.py video --input novels/我的第一部小说/full_novel.txt --output my_first_novel.mp4
   ```

## ✨ 功能特性
- 基于大模型生成小说内容
- 智能内容去重和质量优化
- 文本后处理与格式化
- 小说转视频功能
- 自定义黑名单过滤
- 可配置模型参数

## ⚙️ 安装指南

### 前置要求
1. Python 3.8+
2. Ollama服务（本地或远程）
3. 支持CUDA的GPU（推荐，用于本地Transformers模型）

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/your-repo/novelcreator-tf.git
cd novelcreator-tf

# 安装Python依赖
pip install -r requirements.txt

# 安装额外依赖（如果requirements.txt中缺失）
pip install torch transformers opencv-python moviepy openai

# 选项1: 安装Ollama并下载模型（示例使用phi3）
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3:3.8b

# 启动Ollama服务（后台运行）
ollama serve &

# 选项2: 配置OpenAI兼容API（如OpenRouter）
# 在 config/config.yaml 中配置API密钥和基础URL
```

## 📝 配置文件

### config.yaml
```yaml
# Ollama模型配置
ollama:
  endpoint: "http://localhost:11434"  # Ollama API端点
  model: "phi3:3.8b"                  # 默认使用模型
  hf_model: "unsloth/DeepSeek-R1-Distill-Qwen-14B"  # HuggingFace模型名称
  trust_remote_code: true             # 仅在启用本地TF模式时生效

# OpenAI兼容API配置（支持OpenRouter、OpenAI等）
openai:
  api_key: "your-api-key-here"        # API密钥
  base_url: "https://api.openai.com/v1"  # API基础URL
  model: "gpt-3.5-turbo"              # 默认模型
  
  # 任务特定模型配置（可选）
  models:
    outline: "z-ai/glm-4.5-air:free"      # 大纲生成模型
    review: "moonshotai/kimi-k2:free"     # 评论/审查模型
    content: "deepseek/deepseek-r1-0528:free"  # 正文生成模型

# 路径配置
paths:
  novels_dir: "novels"       # 小说存储目录

# 系统设置
settings:
  timeout: 240                # API请求超时（秒）

  # Reader机制配置（M1）
  reader:
    enabled: true
    max_review_rounds: 2
    min_total_score: 7
    hard_fail_dims: ["coherence", "character_consistency", "safety"]
    sample_review: true
    sample_strategy: ["head", "key", "tail"]
    max_summary_len: 400
    min_chapter_chars: 4000
    sample_threshold_chars: 5000

  # 视频生成参数（与实现对齐）
  video:
    width: 1920
    height: 1080
    fps: 24
    font_size: 32
    text_color: [255, 255, 255]
    bg_color: [0, 0, 0]
    margin: 100
    line_spacing: 10
```

### blacklist.yaml
```yaml
exact:
  - "敏感词1"
  - "敏感词2"

ranges:
  - "<unsafe>.*?</unsafe>"
  - "<政治敏感>.*?</政治敏感>"
```

## 🚀 使用说明

### 生成新小说
```bash
# 生成一个10章的小说
python main.py novel --action new --title "我的科幻小说" --chapters 10

# 指定输出目录
python main.py novel --action new --title "我的奇幻小说" --output-dir "./my_novels" --chapters 5
```

### 续写小说
```bash
# 为现有小说添加5个新章节
python main.py novel --action continue --title "我的科幻小说" --chapters 5
```

### 合并章节
```bash
# 将分散的章节文件合并为完整小说
python main.py novel --action merge --title "我的科幻小说"
```

### 生成视频
```bash
# 从完整小说生成视频
python main.py video --input novels/我的科幻小说/full_novel.txt --output my_novel.mp4

# 从单个章节生成视频
python main.py video --input novels/我的科幻小说/chaps/chapter_1.txt --output chapter1.mp4
```

### 交互式模式
```bash
# 运行交互式界面
python main.py
```

### 可选参数
- `--verbose`: 显示详细日志
- `--config`: 指定配置文件路径

## 📂 文件说明
| 文件 | 功能 |
|------|------|
| `novel_generator.py` | 小说生成主程序 |
| `video_generator.py` | 视频合成模块 |
| `model_handler.py`   | 大模型交互接口 |
| `utils.py`           | 通用工具函数 |
| `blacklist.yaml`     | 内容过滤配置 |
| `config.yaml`        | 全局配置文件 |
| `resources/SimHei.ttf` | 中文字体文件 |
| `main.py`            | 统一入口脚本 |

## 🎯 内容质量改进
本项目实现了智能内容质量控制机制：
- **重复内容检测**：自动识别并过滤重复段落和句子
- **AI标记清理**：移除生成过程中的思考标记和调试信息
- **智能扩展优化**：在内容扩展过程中跳过无效重复内容
- **格式规范化**：统一章节分隔符和文本格式

## ⚠️ 注意事项
1. 安装依赖: `pip install -r requirements.txt`
2. Ollama模型: 确保下载config.yaml中指定的模型 `ollama pull <model_name>`
3. FFmpeg安装:
   - Windows: 从 https://ffmpeg.org/download.html 下载并添加至PATH
   - Linux: `sudo apt install ffmpeg`
   - Mac: `brew install ffmpeg`
4. 字体路径: 视频生成需指定字体文件路径 `--font resources/SimHei.ttf`
5. 内容过滤: 使用前配置config/blacklist.yaml过滤敏感内容

## 📜 许可证
本项目采用 [MIT License](LICENSE)
