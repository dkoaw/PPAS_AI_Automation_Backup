---
name: blender-asset-info-exporter
description: 输出资产核心结构信息，包含 cache 下模型的 DAG 路径、顶点数及顶点坐标，用于环节间的拓扑比对。
---

# blender-asset-info-exporter 技能手册

## 技能描述
此技能专门用于导出 Blender 资产的“核心几何指纹”。它会扫描 `cache` 组下的所有模型，记录它们的绝对层级路径 (DAG Path)、顶点总数以及每个顶点的精确局部空间坐标。

生成的 JSON 文件格式与管线标准的 `.info` 校验文件完全对齐，可用于：
1. **环节比对**：核对 `mod`, `tex`, `rig` 环节之间的拓扑是否发生非法改变。
2. **权重校验**：确保模型点序未乱，防止绑定权重失效。

## 触发条件
当用户要求“输出资产核心结构信息”、“导出模型拓扑数据”、“生成.info校验文件”时触发。

## 执行方式
该技能在后台 (Headless) 模式下执行。

**执行命令 (PowerShell)**:
```powershell
$env:EXTRACT_INFO_OUT="输出的json路径"
& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" -b "目标.blend" -P "X:\AI_Automation\.gemini\skills\blender-asset-info-exporter\scripts\export_info.py"
```

## 输出产物
- 一个包含资产所有 Mesh 拓扑信息的 JSON 文件。
- 键名为绝对路径（如 `|Group|cache|body_Grp|body|bodyShape`）。
- 值为包含 `vertices` (整数) 和 `vert_positions` (一维浮点数组) 的字典。
