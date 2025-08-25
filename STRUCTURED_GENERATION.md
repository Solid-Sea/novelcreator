# NovelCreator Transformer 结构化生成功能说明

## 概述
结构化生成功能是NovelCreator Transformer的一项重要增强功能，通过引入结构化数据格式和故事圣经（Story Bible）机制，显著提高了AI生成内容的质量和一致性。

## 核心特性

### 1. 结构化大纲生成
使用严格的JSON格式定义小说结构，确保生成内容的逻辑性和连贯性。

**输出格式：**
```json
{
    "title": "小说标题",
    "total_chapters": 章节数量,
    "story_background": "故事背景描述",
    "main_characters": [
        {
            "name": "角色姓名",
            "role": "角色身份",
            "characteristics": "角色特征",
            "relationship": "与其他角色的关系"
        }
    ],
    "chapters": [
        {
            "chapter_num": 1,
            "title": "章节标题",
            "summary": "章节概要",
            "key_events": ["重要事件1", "重要事件2"],
            "character_development": "角色发展",
            "plot_points": "关键情节点"
        }
    ]
}
```

### 2. 故事圣经（Story Bible）
创建并维护小说的核心信息数据库，用于跟踪和保证内容一致性。

**包含内容：**
- 角色特征跟踪
- 情节点管理
- 时间线维护
- 地点记录
- 关系网络

### 3. 任务特定模型配置
根据不同生成任务使用专门优化的模型，提高生成质量。

**模型分配：**
- `outline`: 大纲生成模型
- `review`: 审查模型
- `content`: 正文生成模型

## 实现细节

### 大纲生成优化
通过明确的JSON格式要求和清理机制，确保返回纯净的结构化数据。

### 章节生成增强
基于结构化大纲信息，生成更符合整体情节发展的章节内容。

### 一致性保证
通过故事圣经跟踪关键信息，为后续的审查和修订提供参考依据。

## 使用示例

### 生成结构化大纲
```python
from src.novel_generator import NovelGenerator
from src.model_handler import ModelHandler

model_handler = ModelHandler()
generator = NovelGenerator(model_handler)

# 生成结构化大纲
outline_json = generator._generate_outline("科幻小说", 5)
outline_data = json.loads(outline_json)
```

### 创建故事圣经
```python
# 基于大纲创建故事圣经
story_bible = generator._create_story_bible(outline_data)
```

### 结构化章节生成
```python
# 使用结构化信息生成章节
chapter_content = generator._generate_chapter_structured("科幻小说", 1, outline_data)
```

## 配置说明

### config.yaml 配置
```yaml
# 任务特定模型配置
openai:
  models:
    outline: "z-ai/glm-4.5-air:free"      # 大纲生成模型
    review: "moonshotai/kimi-k2:free"     # 评论模型  
    content: "deepseek/deepseek-r1-0528:free"  # 正文生成模型
```

## 优势特点

### 1. 质量提升
- 结构化输入引导AI生成更高质量内容
- 减少无关信息和格式错误
- 提高内容连贯性

### 2. 一致性保证
- 角色特征跟踪防止前后矛盾
- 情节点管理确保逻辑连贯
- 关系网络维护角色互动合理性

### 3. 可维护性增强
- 结构化数据便于后续处理和分析
- 故事圣经提供完整的内容参考
- 模块化设计易于扩展和修改

### 4. 性能优化
- 任务特定模型提高生成效率
- 结构化处理减少重复工作
- 缓存机制加速重复操作

## 测试验证

通过专门的测试脚本验证功能正确性：
```bash
python test_structured_generation.py
```

**测试结果：**
- ✅ 结构化大纲生成成功
- ✅ JSON解析正常
- ✅ 故事圣经创建完成
- ✅ 结构化章节生成正常

## 未来扩展

### 1. 增强的跟踪机制
- 更详细的角色发展跟踪
- 复杂关系网络分析
- 时间线冲突检测

### 2. 智能优化
- 基于历史数据的生成优化
- 自适应模型选择
- 动态参数调整

### 3. 扩展功能
- 多语言支持
- 跨作品一致性维护
- 自动生成角色关系图

## 总结

结构化生成功能通过引入结构化数据处理和智能跟踪机制，显著提升了NovelCreator Transformer的内容生成质量和一致性，为创建高质量小说内容提供了坚实的技术基础。
