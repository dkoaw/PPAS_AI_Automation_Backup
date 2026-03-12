---
name: lgt_render_setup
description: 渲染参数一键设置技能，固化 EEVEE Next 和 Cycles 的生产级质量参数。
---

# lgt_render_setup

渲染参数一键设置技能，固化 EEVEE Next 和 Cycles 的生产级质量参数。

## 功能描述
该技能提供了行业标准的渲染参数一键设置功能，旨在避免手动调整可能导致的参数遗漏或质量不一。涵盖了 EEVEE Next 和 Cycles 两大引擎的各种光照、采样、降噪及光追细节配置。

## 固化参数包括
- **Cycles 设置**：最大采样率 (Max Samples)、降噪器选择 (OpenImageDenoise/OptiX)、路径追踪深度 (Max Bounces)、性能分块 (Tile Size) 等。
- **EEVEE Next 设置**：阴影分辨率 (Shadow Resolution)、间接光照设置 (Indirect Lighting)、屏幕空间反射 (Screen Space Reflections)、光追开关等。
- **渲染限制**：防止由于参数过高导致的渲染时间失控。

## 使用建议
灯光师在完成灯光布局后，应调用此技能以确保输出文件符合后期合成要求的采样质量和色彩空间。
