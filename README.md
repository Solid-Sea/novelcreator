# NovelCreator 小说生成器

![项目图标](https://via.placeholder.com/150)  
*一个基于AI的自动小说生成工具*

## 项目简介

NovelCreator 是一个利用大型语言模型自动生成小说的工具，支持本地Llama.cpp模型和Ollama API两种方式。可以自动生成完整的小说大纲、章节细纲和正文内容。

## 功能特点

- 📖 **全自动生成**：从大纲到章节内容一键生成
- 🚀 **双模型支持**：本地Llama.cpp模型和Ollama API
- 📂 **结构化存储**：自动生成规范的目录结构
- 🔄 **断点续写**：支持从上次中断处继续生成
- 📝 **Markdown支持**：生成内容支持Markdown格式

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/your-repo/novelcreator-v2.git
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 下载模型：
   - 将GGUF格式的模型文件放入`models/`目录

## 使用方法

1. 编辑`config.yaml`配置文件
2. 运行主程序：
```bash
python novel_generator.py
```
3. 输入小说标题开始生成

## 配置说明

编辑`config.yaml`文件进行配置：

```yaml
ollama:
  endpoint: "http://localhost:11434/api/generate"
  model: "llama3"
  temperature: 0.7

llama:
  model_path: "models/your-model.gguf"
  n_ctx: 2048
  n_gpu_layers: -1

settings:
  max_retries: 3
  timeout: 60

paths:
  novels_dir: "novels"
```

## 贡献指南

欢迎提交Pull Request或Issue。请确保：
- 代码符合PEP8规范
- 提交前运行测试
- 更新相关文档

## 许可证

[MIT License](LICENSE)
