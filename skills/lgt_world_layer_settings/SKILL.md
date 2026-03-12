---
name: lgt_world_layer_settings
description: 由于 Blender 的 World Shader 是全局的，不同渲染层默认共享同一套 HDR 参数。
---

# 🛠️ lgt_world_layer_settings (环境光分层设置技能)

## 技能描述
由于 Blender 的 World Shader 是全局的，不同渲染层默认共享同一套 HDR 参数。此技能打破了这一限制，允许用户为**每个渲染层单独设置不同的环境光参数（Hue、Saturation、Value、Strength）**。

## 核心特性 (Driver-JSON 架构)
1. **数据沙盒存储**：将每层的环境光参数以 JSON 字符串形式安全地保存在 `world["ppas_layer_params"]` 自定义属性中。
2. **底层驱动劫持**：自动在 `Hue/Saturation` 和 `Background` 节点上挂载驱动器。渲染时，驱动器会通过 `get_world_param_for_layer` 实时拉取当前激活层对应的参数。
3. **UI 记忆预载**：点击按钮呼出面板时，会自动读取当前层之前保存的参数进行预填，所见即所得。

## 导出 Operator
- `ppas.set_world_layer_params`: 弹出参数设置面板并将其应用到当前渲染层。
