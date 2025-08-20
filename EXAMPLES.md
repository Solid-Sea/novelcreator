# NovelCreator 使用示例

## 📚 基本使用示例

### 1. 生成新小说

```bash
# 生成一个5章的科幻小说
python main.py novel --action new --title "星际探险" --chapters 5

# 生成一个10章的奇幻小说，指定输出目录
python main.py novel --action new --title "魔法王国" --output-dir "./my_books" --chapters 10
```

### 2. 续写现有小说

```bash
# 为"星际探险"添加3个新章节
python main.py novel --action continue --title "星际探险" --chapters 3
```

### 3. 合并章节为完整小说

```bash
# 将分散的章节合并为完整小说
python main.py novel --action merge --title "星际探险"
```

### 4. 生成视频

```bash
# 从完整小说生成视频
python main.py video --input novels/星际探险/full_novel.txt --output interstellar_journey.mp4

# 从单个章节生成视频
python main.py video --input novels/星际探险/chaps/chapter_1.txt --output chapter1.mp4
```

## 🎯 高级使用示例

### 1. 使用不同模型

```bash
# 在配置文件中指定不同的模型
# 编辑 config/config.yaml 修改 ollama.model 字段

# 或者使用命令行参数（如果支持）
python main.py novel --action new --title "测试小说" --model "qwen3:8b"
```

### 2. 自定义配置

```bash
# 使用自定义配置文件
python main.py novel --action new --title "自定义小说" --config ./my_config.yaml
```

### 3. 详细日志模式

```bash
# 启用详细日志查看生成过程
python main.py novel --action new --title "详细日志测试" --chapters 3 --verbose
```

## 🖥️ 交互式模式使用

```bash
# 启动交互式界面
python main.py

# 然后按照菜单提示操作：
# 1. 选择"生成小说"
# 2. 选择"创建新小说"
# 3. 输入小说标题和章节数量
# 4. 等待生成完成
```

## 📁 项目结构说明

生成的小说将按以下结构存储：

```
novels/
├── 星际探险/
│   ├── chaps/
│   │   ├── chapter_1.txt
│   │   ├── chapter_2.txt
│   │   └── ...
│   ├── summaries/
│   │   ├── chapter_1.txt
│   │   └── ...
│   ├── reviews/
│   │   ├── chapter_1.json
│   │   └── ...
│   ├── outline.txt          # 小说大纲
│   └── full_novel.txt       # 完整合并的小说
```

## 🎥 视频生成说明

视频生成将把文本内容转换为带有字幕的视频：

```bash
# 基本视频生成
python main.py video --input novels/星际探险/full_novel.txt --output my_novel.mp4

# 指定字体文件
python main.py video --input novels/星际探险/full_novel.txt --output my_novel.mp4 --font resources/SimHei.ttf
```

## ⚙️ 配置文件自定义

### config.yaml 自定义示例

```yaml
# 选项1: 使用Ollama模型
ollama:
  endpoint: "http://localhost:11434"
  model: "qwen3:8b"  # 更强大的模型

# 选项2: 使用OpenAI兼容API（如OpenRouter）
openai:
  api_key: "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"
  base_url: "https://openrouter.ai/api/v1"
  model: "openrouter/auto"
  
  # 任务特定模型配置（可选）
  models:
    outline: "z-ai/glm-4.5-air:free"      # 大纲生成模型
    review: "moonshotai/kimi-k2:free"     # 评论/审查模型
    content: "deepseek/deepseek-r1-0528:free"  # 正文生成模型

# 调整生成参数
settings:
  timeout: 300  # 增加超时时间
  
  # 调整章节长度要求
  reader:
    min_chapter_chars: 5000  # 更长的章节
    max_review_rounds: 3     # 更多审查轮次
```

### blacklist.yaml 自定义示例

```yaml
exact:
  - "暴力"
  - "色情"
  - "政治敏感词"
  - "广告内容"

ranges:
  - "<unsafe>.*?</unsafe>"
  - "<政治敏感>.*?</政治敏感>"
  - "http[s]?://.*?"  # 过滤URL
```

## 🧪 测试和调试

### 1. 环境检查

```bash
# 运行环境检查脚本
python test_environment.py
```

### 2. 快速测试生成

```bash
# 生成一个很短的小说用于测试
python main.py novel --action new --title "测试小说" --chapters 1
```

### 3. 查看生成进度

```bash
# 查看生成的日志文件
tail -f novel_gen.log
```

## 🚀 性能优化建议

1. **模型选择**：根据硬件配置选择合适的模型
   - 轻量级：phi3:3.8b（速度快，资源占用少）
   - 高质量：qwen3:8b（质量更好，需要更多资源）

2. **章节长度**：合理设置章节长度以平衡质量和生成时间

3. **并行处理**：可以同时运行多个不同的生成任务

4. **资源监控**：监控内存和GPU使用情况，避免资源耗尽
