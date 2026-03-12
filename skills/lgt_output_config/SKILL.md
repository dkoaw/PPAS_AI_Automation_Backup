---
name: lgt_output_config
description: 渲染输出配置技能，快速切换 100% 比例的分辨率预设。
---

# lgt_output_config

渲染输出配置技能，快速切换 100% 比例的分辨率预设。

## 功能描述
该技能用于管理 Blender 场景的分辨率设置，提供了常用格式（如 1080p, 2K, 4K 等）的快速切换功能。核心特点在于一键将 Resolution Percentage 锁定在 100%，以保证最终输出的文件分辨率符合交付标准。

## 主要预设
- **1080p (FHD)**: 1920 x 1080, 1.0 aspect ratio.
- **2K DCI**: 2048 x 1080.
- **4K DCI**: 4096 x 2160.
- **社交媒体格式**: 如 1080 x 1350 (4:5) 或 1080 x 1920 (9:16)。

## 额外功能
- 自动更新输出文件路径前缀（结合 `lgt_project_info`）。
- 同步更新渲染摄像机的传感器尺寸以匹配画面长宽比。
- 确认色彩管理 (Color Management) 的输出变换 (View Transform) 设置。
