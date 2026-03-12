---
name: lgt_output_nodes
description: 用于在灯光合成环节一键配置合成器（Compositor）输出节点。
---

# 🛠️ lgt_output_nodes (输出节点自动对齐技能)

## 技能描述
用于在灯光合成环节一键配置合成器（Compositor）输出节点。

## 核心特性 (V15 Precision)
1. **数据净化**：自动清理旧的合成节点树，确保每个场景的输出设置唯一且干净。
2. **自动化路径**：按照管线规范自动生成物理路径：`{文件目录}/renderout_image/{文件名}/{场景名}/{层名}/`。
3. **Pass 精准对齐**：智能扫描渲染层输出，**仅连接已启用 (Enabled) 的 Pass**，自动排除 Alpha，确保 EXR 分层文件体积最优化。
4. **管线参数**：强制使用 OpenEXR Multilayer、32-bit、ZIP 压缩。

## 导出 Operator
- `ppas.setup_output_nodes`: 自动创建并对齐输出节点。
