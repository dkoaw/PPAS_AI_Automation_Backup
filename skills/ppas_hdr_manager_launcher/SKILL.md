---
name: ppas-hdr-manager-launcher
description: 统筹与连接 HDR 面板三大微服务模块的发射总管与事件总线。
---

# PPAS HDR Manager Launcher

## 核心职责 (Core Responsibilities)
1. **总控启动器 (Manager Launcher)**: 统筹与连接 `ppas_hdr_asset_parser` (扫描)、`ppas_hdr_qt_panel` (界面)、`ppas_hdr_blender_core` (操作) 三大微服务模块的发射总管。
2. **事件总线 (Event Bus)**: 注册 Qt UI 信号到 Blender Core 后端逻辑，维持跨线程的 GC 生命线。
3. **入口节点**: 提供 `run_manager()` 被其他 UI 调用，打开独立版 HDR 贴图选择器面板。