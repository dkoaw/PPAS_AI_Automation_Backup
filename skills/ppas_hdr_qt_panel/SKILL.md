---
name: PPAS HDR Qt Shield Panel
description: A completely blind and decoupled PySide graphical interface dedicated purely to user interaction, obeying the Append-Only rule.
---

# PPAS HDR Qt UI Panel

## 核心职责 (Core Responsibilities)
1. **脱壳交互板**: 独立复现管线指定的 HDR 选择器工具样貌 (Sliders, ListWidget, Buttons)。
2. **纯粹监听发射器**: 这个脚本本身严格**不得包含任何 `import bpy` 逻辑**。它一切的行为都是向外发射安全的 `Signals`，保证其可以在任何非 Blender 环境中调试或直接移植至 Unreal。
3. **白名单反馈表现**: 在被外界捕捉拦截时，自动调用封锁函数 (`.setDisabled(True)`) 防止美术发生任何越界操作。
