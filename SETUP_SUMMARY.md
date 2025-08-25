# NovelCreator 设置摘要

## 📋 系统要求

- **Python版本**: 3.8 或更高版本
- **操作系统**: Windows, macOS, 或 Linux
- **内存**: 至少 8GB RAM (推荐 16GB+)
- **存储**: 至少 10GB 可用空间

## 🛠️ 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/your-repo/novelcreator-tf.git
cd novelcreator-tf
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置模型服务

#### 选项A: 使用Ollama (本地模型)
```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull phi3:3.8b

# 启动服务
ollama serve &
```

#### 选项B: 使用OpenAI兼容API
在 `config/config.yaml` 中配置API密钥和基础URL。

## ⚙️ 配置文件说明

### 主配置文件: `config/config.yaml`

```yaml
# 模型选择配置
model_selection:
  default_type: "openai"  # 默认模型类型: "ollama" 或 "openai"

# Ollama配置
ollama:
  endpoint: "http://localhost:11434"
  model: "phi3:3.8b"

# OpenAI兼容API配置
openai:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-3.5-turbo"
  
  # 任务特定模型
  models:
    outline: "model-for-outline"
    review: "model-for-review"
    content: "model-for-content"
```

## 🚀 使用方法

### 命令行模式

```bash
# 生成新小说
python main.py novel --action new --title "小说标题" --chapters 10

# 指定模型类型
python main.py novel --action new --title "小说标题" --chapters 10 --model-type openai

# 续写小说
python main.py novel --action continue --title "小说标题" --chapters 5

# 合并章节
python main.py novel --action merge --title "小说标题"

# 生成视频
python main.py video --input input.txt --output output.mp4
```

### 交互式模式

```bash
python main.py
```

## 🧪 测试工具

### 环境检查
```bash
python test_environment.py
```

### OpenAI API测试
```bash
python test_openai_api.py
```

### 任务模型测试
```bash
python test_task_models.py
```

### OpenAI API演示
```bash
python demo_openai_api.py
```

## 📁 目录结构

```
novelcreator-tf/
├── config/              # 配置文件
│   ├── config.yaml      # 主配置文件
│   └── blacklist.yaml   # 黑名单配置
├── resources/           # 资源文件
│   └── SimHei.ttf       # 中文字体
├── src/                 # 源代码
│   ├── model_handler.py # 模型处理器
│   ├── novel_generator.py # 小说生成器
│   ├── utils.py         # 工具函数
│   └── video_generator.py # 视频生成器
├── novels/              # 生成的小说目录
├── main.py              # 主程序入口
├── requirements.txt     # Python依赖
└── README.md           # 项目说明
```

## 🔧 常见问题解决

### 1. 依赖安装问题
```bash
# 升级pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 2. 中文字体问题
确保 `resources/SimHei.ttf` 文件存在，或在视频生成时指定其他中文字体路径。

### 3. API连接问题
- 检查网络连接
- 验证API密钥是否正确
- 确认基础URL是否正确

### 4. 模型加载问题
- 检查模型是否正确下载
- 确认模型名称是否正确
- 验证模型服务是否正常运行

### 5. FFmpeg安装问题
- Windows: 从 https://ffmpeg.org/download.html 下载并添加至PATH，或使用conda安装: `conda install ffmpeg`
- Linux: `sudo apt install ffmpeg`
- Mac: `brew install ffmpeg`
确保FFmpeg已正确安装并可在命令行中访问: `ffmpeg -version`

## 🎯 最佳实践

### 1. 模型选择建议
- **本地开发**: 使用Ollama以节省API费用
- **生产环境**: 使用高质量的OpenAI兼容API
- **混合使用**: 根据任务类型选择合适的模型

### 2. 配置管理
- 使用环境变量存储敏感信息
- 为不同环境创建不同的配置文件
- 定期备份配置文件

### 3. 性能优化
- 合理设置超时时间
- 使用适当的温度参数
- 启用缓存机制

## 📚 学习资源

- [README.md](README.md) - 详细使用说明
- [EXAMPLES.md](EXAMPLES.md) - 配置示例
- [API文档](docs/api.md) - API使用说明
- [开发指南](docs/development.md) - 开发者指南

## 🆘 技术支持

如遇到问题，请：
1. 运行 `python test_environment.py` 检查环境
2. 查看日志文件 `novel_gen.log`
3. 在GitHub提交Issue
