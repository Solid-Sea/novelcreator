# NovelCreator 使用示例

本文档提供了NovelCreator的各种使用示例，帮助用户快速上手。

## 🚀 快速开始示例

### 1. 生成简单小说
```bash
# 生成一个5章的小说
python main.py novel --action new --title "我的第一部小说" --chapters 5

# 查看生成的小说
ls novels/我的第一部小说/
```

### 2. 生成视频
```bash
# 从完整小说生成视频
python main.py video --input novels/我的第一部小说/full_novel.txt --output my_first_novel.mp4
```

## 📚 小说生成示例

### 基本用法
```bash
# 生成10章科幻小说
python main.py novel --action new --title "星际探险" --chapters 10

# 生成奇幻小说，指定输出目录
python main.py novel --action new --title "魔法王国" --output-dir "./my_books" --chapters 8

# 使用特定模型类型
python main.py novel --action new --title "悬疑故事" --chapters 6 --model-type openai
```

### 续写小说
```bash
# 为现有小说添加新章节
python main.py novel --action continue --title "星际探险" --chapters 3

# 指定不同的输出目录
python main.py novel --action continue --title "魔法王国" --output-dir "./my_books" --chapters 2
```

### 合并章节
```bash
# 将分散的章节合并为完整小说
python main.py novel --action merge --title "星际探险"

# 指定特定目录
python main.py novel --action merge --title "魔法王国" --output-dir "./my_books"
```

## 🎬 视频生成示例

### 从完整小说生成视频
```bash
# 基本用法
python main.py video --input novels/星际探险/full_novel.txt --output interstellar.mp4

# 指定字体和输出路径
python main.py video --input novels/魔法王国/full_novel.txt --output fantasy.mp4 --font resources/SimHei.ttf
```

### 从单个章节生成视频
```bash
# 生成第一章视频
python main.py video --input novels/星际探险/chaps/chapter_1.txt --output chapter1.mp4

# 生成多个章节视频
python main.py video --input novels/魔法王国/chaps/chapter_1.txt --output magic_ch1.mp4
python main.py video --input novels/魔法王国/chaps/chapter_2.txt --output magic_ch2.mp4
```

## 🖥️ 交互式模式示例

```bash
# 启动交互式界面
python main.py

# 交互式界面将显示以下菜单：
# 【主菜单】
# 1. 生成小说
# 2. 生成视频
# 3. 配置管理
# 4. 查看项目状态
# 5. 清理临时文件
# 6. 退出
```

## ⚙️ 高级配置示例

### 配置文件使用
```bash
# 使用自定义配置文件
python main.py novel --action new --title "自定义小说" --config ./my_config.yaml --chapters 5

# 启用详细日志
python main.py novel --action new --title "详细日志小说" --verbose --chapters 3
```

### 模型选择示例
```bash
# 强制使用Ollama模型
python main.py novel --action new --title "本地小说" --model-type ollama --chapters 4

# 强制使用OpenAI兼容API
python main.py novel --action new --title "云端小说" --model-type openai --chapters 6
```

## 🧪 测试和验证示例

### 环境检查
```bash
# 检查所有依赖和配置
python test_environment.py
```

### API连接测试
```bash
# 测试OpenAI API连接
python test_openai_api.py

# 测试特定任务模型
python test_task_models.py
```

## 📁 目录结构示例

生成的小说目录结构如下：
```
novels/
└── 我的科幻小说/
    ├── chaps/              # 章节目录
    │   ├── chapter_1.txt   # 第一章
    │   ├── chapter_2.txt   # 第二章
    │   └── ...             # 其他章节
    ├── reviews/            # 审查文件目录
    │   ├── chapter_1.json  # 第一章审查
    │   └── ...             # 其他审查文件
    ├── summaries/          # 摘要目录
    │   ├── chapter_1.txt   # 第一章摘要
    │   └── ...             # 其他摘要
    ├── outline.txt         # 小说大纲
    ├── story_bible.json    # 故事圣经
    └── full_novel.txt      # 完整小说
```

## 🎯 最佳实践示例

### 1. 分阶段生成
```bash
# 第一阶段：生成大纲和前几章
python main.py novel --action new --title "长篇小说" --chapters 3

# 第二阶段：续写更多章节
python main.py novel --action continue --title "长篇小说" --chapters 7

# 第三阶段：合并所有章节
python main.py novel --action merge --title "长篇小说"
```

### 2. 批量处理
```bash
# 生成多个小说
for title in "小说1" "小说2" "小说3"; do
    python main.py novel --action new --title "$title" --chapters 5
done
```

### 3. 视频批量生成
```bash
# 为所有小说生成视频
for novel_dir in novels/*/; do
    novel_name=$(basename "$novel_dir")
    python main.py video --input "$novel_dir/full_novel.txt" --output "${novel_name}.mp4"
done
```

## 🛠️ 故障排除示例

### 常见问题解决
```bash
# 如果遇到API连接问题，检查配置
python test_environment.py

# 如果模型加载失败，检查模型服务
curl http://localhost:11434/api/tags

# 如果视频生成失败，检查FFmpeg
ffmpeg -version

# 查看详细日志
python main.py novel --action new --title "测试小说" --verbose --chapters 1
```

### 日志分析
```bash
# 查看生成日志
tail -f novel_gen.log

# 搜索特定错误
grep "ERROR" novel_gen.log

# 统计生成进度
grep "章节生成完成" novel_gen.log | wc -l
```

## 📊 性能优化示例

### 1. 调整超时设置
在 `config/config.yaml` 中：
```yaml
settings:
  timeout: 300  # 增加超时时间以处理复杂请求
```

### 2. 模型参数调优
```bash
# 使用不同的温度参数生成不同风格的内容
# 在代码中调整 temperature 参数来控制创造性
```

### 3. 批量处理优化
```bash
# 使用并行处理生成多个小说
python main.py novel --action new --title "小说1" --chapters 5 &
python main.py novel --action new --title "小说2" --chapters 5 &
wait  # 等待所有后台任务完成
```

## 🎨 自定义配置示例

### 自定义黑名单
`config/blacklist.yaml`:
```yaml
exact:
  - "暴力"
  - "色情"
  - "政治敏感词"

ranges:
  - "<unsafe>.*?</unsafe>"
  - "<政治敏感>.*?</政治敏感>"
```

### 自定义视频参数
`config/config.yaml`:
```yaml
settings:
  video:
    width: 1920
    height: 1080
    fps: 24
    font_size: 36
    text_color: [255, 255, 255]
    bg_color: [0, 0, 0]
    margin: 120
    line_spacing: 15
```

这些示例应该能帮助用户快速上手NovelCreator并充分利用其功能。
