# 🛠️ lgt_render_layer_manager (灯光渲染层管理窗口技能)

## 技能描述
基于原版 `PPAS SG` 插件剥离的独立 Qt UI 面板。目前作为一个**纯净的“壳”**存在，负责展示渲染层的添加、编辑、隐藏对象控制以及附加集合功能的 UI 布局。

## 核心特性
1. **纯净 UI 架构**：原汁原味还原了原版 `render_layer_widget.py` 的所有按钮和布局结构（包含 QSplitter 和 QGridLayout）。
2. **PySide6 驱动**：从原有的 `qtpy` 适配到当前的 `PySide6` 生态，确保窗口能以 `WindowStaysOnTopHint` 模式悬浮在 Blender 顶层。
3. **占位设计**：所有按钮点击事件均已解绑，等待后续新技能逻辑的注入。

## 导出 Operator
- `ppas.open_render_layer_manager`: 唤起渲染层管理器独立窗口。
