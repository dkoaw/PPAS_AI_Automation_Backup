---
name: lgt_normal_adjuster
description: 用于在灯光合成环节批量调整场景中所有材质的法线（Normal Map）和凹凸（Bump）强度。
---

# 🛠️ lgt_normal_adjuster (法线强度批量调整技能)

## 技能描述
用于在灯光合成环节批量调整场景中所有材质的法线（Normal Map）和凹凸（Bump）强度。

## 核心特性 (V2.0)
1. **原始值锁定**：首次执行时，会自动将当前的强度值记录在节点的 `["ppas_original_strength"]` 自定义属性中。
2. **防叠加计算**：后续的所有调整都将基于这个“原始值”进行乘法运算，而非在当前值基础上连乘，确保了操作的可逆性和准确性。
3. **5.0 兼容**：完全适配 Blender 5.0+ 的 `data.node_groups` 架构。

## 导出 Operator
- `ppas.adjust_normal_strength`: 批量调整法线强度。
