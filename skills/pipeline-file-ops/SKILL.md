---
name: pipeline-file-ops
description: 提供管线通用的文件处理原子操作，如搜索最新版本、清理残留、原子化读写映射等，支持 Python 2/3。
---

# 📂 pipeline-file-ops (管线通用文件操作技能)

## 技能描述
提供管线通用的文件处理原子操作，旨在消除各 Stage 脚本中的代码冗余，确保文件读写与路径管理的稳固性。

## 核心接口
### `file_ops.py`
- `get_latest_file(directory, pattern)`: 使用 glob 搜索目录下符合 pattern 的最新修改文件。
- `pre_clean_stale_files(filepath)`: 在写入/拷贝前，强制物理删除已存在的文件或旧版备份。
- `post_clean_atomic_save(filepath)`: (占位/扩展用) 用于确保文件写入完整。
- `unicode_fallback()`: 自动处理 Python 2/3 的 `unicode` 类型兼容。

## 使用方法
```python
from pipeline_file_ops import file_ops
# 或者在无法直接导入的情况下注入 sys.path
```
