---
name: blender-fixer-atoms
description: 包含 Blender 管线通用的原子化处理逻辑，如网格清理、组命名、曲线处理、文件夹结构构建等。
---

# 🧩 blender-fixer-atoms (Blender 管线原子逻辑零件包)

## 技能描述
提供一系列可插拔的原子化处理零件，支持不同类型的资产（角色、道具、场景）在管线中的标准化修正。

## 模块清单
- `structure_builder.py`: 构建基础 Outliner 层级结构。
- `group_processor.py`: 处理组命名规范与属性同步。
- `mesh_processor.py`: 网格清理、重命名、UV/材质审计。
- `curve_handler.py`: 针对曲线物体的标准化处理。
- `core_utils.py`: 提供资产名称提取、前缀管理等底层工具。
- `final_sync.py`: 执行最后的场景层级对齐与清理。

## 使用方法
```python
# 在修正器主脚本中注入该路径并按需加载模块
```
