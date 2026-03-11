---
name: word-reader
description: 处理和分析 .docx (Word) 文件的图文内容。当用户提供 .docx 文件并要求读取、总结或分析（尤其是包含图片时）触发此技能。关键字：word文档、.docx
---

# Docx 图文分析工作流

当用户要求你分析 `.docx` 文件或使用包含 `word文档`、`.docx` 关键字的任务时，你**不能**直接使用 `read_file` 工具读取它。你必须严格遵循以下步骤：

### 1. 提取文字与图片
使用 `run_shell_command` 执行解包脚本。假设传入的文件路径为 `<file_path>`（注意：如果路径包含空格，请用引号包裹）：
`python scripts/extract_docx.py "<file_path>"`

### 2. 解析脚本输出
脚本会输出一段 JSON，包含以下关键字段：
- `status`: "success" 或 "error"。
- `text_content`: 文档的纯文本内容。你可以直接阅读这段文字。
- `extracted_images`: 一个包含所有提取出来的图片绝对路径的数组。
- `temp_dir`: 存放图片的临时文件夹路径。

### 3. 查看图片 (Vision 能力)
如果用户的问题涉及文档中的图片（例如：“文档里的图表说明了什么？”），或者你认为需要全面理解文档内容：
你必须使用 `read_file` 工具，**逐一读取** `extracted_images` 数组中的图片路径。你的视觉模型能力会解析这些图片。

### 4. 综合分析与回答
结合你从 JSON 中读到的文字（`text_content`），以及通过 `read_file` 看到的图片内容，为用户提供完整的分析或总结。

### 5. 清理缓存 (重要)
完成分析并给出回答后，作为一个负责任的 Agent，你必须使用 `run_shell_command` 工具，将 `temp_dir` 目录及其内部的临时文件删除，以释放用户的磁盘空间。
PowerShell 删除命令示例：`Remove-Item -Recurse -Force "<temp_dir>"`
