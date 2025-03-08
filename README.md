### novelcreator
一个利用OLLAMA服务生成小说的软件。
## 安装和使用
1.克隆本仓库并创建虚拟环境（假设你已安装了conda）。

```bash
conda create -n novelcreatorpython=3.11
git clone https://github.com/Solid-Sea/novelcreator
cd novelcreator
```

2.运行'novel_generator.py'。

```bash
python novel_generator.py
```

注意：你的ollama仓库里应有config.yaml中指定的模型。

对于p104显卡，建议使用hf-mirror.com/ValueFX9507/Tifa-DeepsexV2-7b-MGRPO-GGUF-Q8:latest模型。

拉取：

```bash
ollama pull hf-mirror.com/ValueFX9507/Tifa-DeepsexV2-7b-MGRPO-GGUF-Q8:latest
```
