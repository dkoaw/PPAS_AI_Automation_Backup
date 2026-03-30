---
name: lgt_sss_layer_setup
description: 用于在灯光环节一键创建 SSS 专用场景与分层，并自动挂载支持原生预览和农场渲染的智能拦截器。
---

# 🛠️ lgt_sss_layer_setup (SSS 渲染层一键装配)

## 技能描述
一键创建 `Scene_sss` 场景与 `Scene_sss_xxx` 渲染层，自动提取 `3s_shader` 资产，并挂载双轨制渲染拦截器。

## 核心特性
1. **自动提取**：全网资产库搜索并提取 `3s_shader`，防止多次导入。
2. **场景层级构建**：如果不存在则自动链接复制创建 `Scene_sss`，并依次生成 `Scene_sss_001` 等序列层。
3. **原生预览共存**：创建层后立即在原生 `Material Override` 中填入材质，满足视口快速粗略预览需求。
4. **后台智能拦截（卸磨杀驴）**：按 F12 或命令行渲染时，自动清空原生 Override，进行精细化手术级覆盖（保留透明毛发），渲染结束后再完美还原视口预览。

## 导出 Operator
- `ppas.setup_sss_layer`: 执行全套 SSS 场景装配与拦截器植入。