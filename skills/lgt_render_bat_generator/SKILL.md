---
name: lgt_render_bat_generator
description: 用于在灯光合成环节一键生成本地分层渲染的 .bat 批处理脚本。
---

# 🛠️ lgt_render_bat_generator (分层渲染批处理生成技能)

## 技能描述
用于在灯光合成环节一键生成本地分层渲染的 `.bat` 批处理脚本。

## 核心特性 (V4.1 Robust)
1. **后台驱动重注册**：生成 `.bat` 的同时，在 Blender 内部注入 `render_manager.py` 逻辑。确保在命令行后台渲染（`-b`）模式下，物体的分层显示隐藏驱动器（Visibility Drivers）依然能够正常工作。
2. **View Layer 物理隔离**：批处理文件按 View Layer 拆分渲染命令，通过强制设置 `vl.use` 实现精准的单层导出。
3. **环境参数自动提取**：自动抓取当前文件的 `frame_start`, `frame_end`, `blender_exe` 路径及文件物理位置。
4. **即时编辑**：生成成功后自动拉起 Notepad++ 打开 `.bat` 文件，方便灯光师调整渲染参数。

## 导出 Operator
- `ppas.generate_render_bat`: 生成当前文件的分层渲染批处理脚本。
