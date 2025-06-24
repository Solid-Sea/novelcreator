# NovelCreator Transformer

一个利用大模型服务自动生成小说的工具链，包含小说生成、文本处理和视频合成功能。

## ✨ 功能特性
- 基于大模型生成小说内容
- 文本后处理与格式化
- 小说转视频功能
- 自定义黑名单过滤
- 可配置模型参数

## ⚙️ 安装指南

### 前置要求
1. Python 3.8+
2. Ollama服务（本地或远程）
3. 支持CUDA的GPU（推荐）

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/your-repo/novelcreator-tf.git
cd novelcreator-tf

# 安装Python依赖
pip install -r requirements.txt

# 安装Ollama并下载模型（示例使用llama3）
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# 启动Ollama服务（后台运行）
ollama serve &
```

## 📝 配置文件

### config.yaml
```yaml
model: "llama3"  # 使用的大模型名称
max_length: 2000  # 生成文本最大长度
temperature: 0.7  # 生成随机性控制
```

### blacklist.yaml
```yaml
# 内容过滤黑名单
banned_words:
  - "暴力"
  - "色情"
  - "政治敏感词"
```

## 🚀 使用说明

### 生成小说
```bash
python main.py --mode novel --prompt "科幻小说大纲" --output story.txt
```

### 生成视频
```bash
python main.py --mode video --input story.txt --output video.mp4 \
  --font resources/SimHei.ttf
```

### 可选参数
- `--verbose`: 显示详细日志
- `--length`: 指定生成内容长度
- `--model`: 覆盖配置文件中的模型设置

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
