---
name: lgt_subdivision_editor
description: 用于在灯光合成环节批量调整选中物体的表面细分（Subdivision Surface）修改器参数。
---

# 🛠️ lgt_subdivision_editor (细分批量编辑技能)

## 技能描述
用于在灯光合成环节批量调整选中物体的表面细分（Subdivision Surface）修改器参数。

## 核心特性 (V4.1 Performance)
1. **高性能扫描**：利用全局材质缓存（Global Material Cache），避免冗余节点树遍历，支持大规模镜头场景。
2. **材质感知优化**：自动检测物体关联材质。若发现法线贴图（Normal Map），将强制开启修改器的 `use_limit_surface` 和 `use_custom_normals`，确保光影细节准确。
3. **参数一键同步**：支持同时设置视图细分级别（Levels）与渲染细分级别（Render Levels）。
4. **数据级访问**：绕过 Blender 操作算子（Ops），直接在数据底层修改属性，效率极高。

## 导出 Operator
- `ppas.batch_edit_subdivision`: 批量编辑选中物体的细分修改器。
