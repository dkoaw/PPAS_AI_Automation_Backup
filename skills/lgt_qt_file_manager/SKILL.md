---
name: lgt_qt_file_manager
description: 贴图文件管理技能，唤起外部 Qt 版文件整理器。
---

# lgt_qt_file_manager

贴图文件管理技能，唤起外部 Qt 版文件整理器。

## 功能描述
作为 Blender 与外部资产库之间的桥梁，该技能负责调起基于 PySide/PyQt 开发的图形化文件管理工具，旨在解决复杂场景中贴图资源分散、路径混乱的问题。

## 核心能力
- **外部界面唤起**：作为独立窗口打开 Qt 管理界面。
- **文件重定向**：批量查找丢失的贴图并更新 Blender 内部路径。
- **资源分类**：根据文件名后缀 (e.g., _diff, _spec, _norm) 对贴图进行逻辑归类。
- **文件指纹检查**：通过 Hash 值比对贴图内容的唯一性，减少重复冗余。

## 依赖
- 需要 Python 环境下预装 PySide2 或 PySide6。
- 外部 `file_manager.py` 脚本必须存在于指定的 Pipeline 工具链路径中。
