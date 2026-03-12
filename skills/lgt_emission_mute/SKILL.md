---
name: lgt_emission_mute
description: 用于在灯光环节，针对特定渲染层（View Layer）一键屏蔽全场景材质的自发光效果。
---

# 🛠️ lgt_emission_mute (自发光分层屏蔽技能)

## 技能描述
用于在灯光环节，针对特定渲染层（View Layer）一键屏蔽全场景材质的自发光效果。

## 核心特性 (V3 Accumulative)
1. **驱动器联动**：通过注入 `Global_Emission_Controller` 节点组，利用驱动器实时检测当前活跃的渲染层。
2. **分层黑名单**：支持累加模式。用户在当前层执行后，该层将被记录在屏蔽列表中。渲染该层时自发光倍率为 0，渲染其余层时恢复为 1。
3. **深度递归扫描**：自动钻取进入材质节点组（NodeGroup）内部，识别并挂接 `BSDF_PRINCIPLED` 的 "Emission Strength" 或 `EMISSION` 节点的 "Strength" 插槽。
4. **无损实时开关**：不修改材质原始数值，通过 `Emission_Mute_Mult` 节点进行逻辑截断。

## 导出 Operator
- `ppas.mute_emission_on_layer`: 将当前渲染层加入自发光屏蔽黑名单.
