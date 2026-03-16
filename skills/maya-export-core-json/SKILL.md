---
name: maya-export-core-json
description: maya2025导出核心架构模型json。基于 Maya 2025 OpenMaya API 的极速导出工具，能够自动过滤绑定中间节点，清洗命名空间与包裹组层级，输出与 Blender 端完美对齐的模型结构与世界坐标指纹 JSON。
---
# maya2025导出核心架构模型json (maya-export-core-json)

该技能提供了一个在 Maya 端运行的纯 Python 脚本，用于提取 `rigMaster` 环节绑定的核心模型数据。

## 核心特性
1. **纯净提取**：利用 `intermediateObject` 属性自动过滤蒙皮带来的无用变形源节点。
2. **层级清洗**：自动将绑定师附加的 Namespace (`rig_v01:`) 或包裹组 (`|Geometry|`) 物理洗去，强制规范为 `|Group|cache|...` 的基准路线。
3. **坐标映射**：直接读取模型的 World Space 坐标，无需在意绑定层级的缩放位移。

## 使用方法
可以在 Maya 2025 内部的脚本编辑器 (Script Editor) 中直接运行 `scripts/export_maya_info.py`。
它会自动在当前 `.ma` 文件的同目录下，生成一个同名的 `.json` 指纹文件供下游环节 (lib) 进行比对质检。
