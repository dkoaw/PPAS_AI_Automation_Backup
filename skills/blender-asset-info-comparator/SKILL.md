---
name: blender-asset-info-comparator
description: 资产核心模型数据对比技能。对比两个 JSON 文件的 DAG 路径、顶点数及顶点坐标，输出详细差异报告。
---

# blender-asset-info-comparator 技能手册

## 技能描述
此技能专门用于对两个不同环节导出的资产核心结构信息（JSON 格式）进行深度比对。它能够精准识别出：
1. **层级结构差异**：哪些模型在 A 环节有但在 B 环节丢了，或者反之。
2. **拓扑差异**：模型名字对上了，但顶点总数是否发生改变。
3. **几何差异**：模型点数对上了，但顶点在空间中的坐标是否发生了微小位移或点序错乱。

## 触发条件
当用户要求“比对两个JSON文件”、“对比环节资产结构差异”、“详细对比模型数据”时触发。

## 执行方式
该技能为纯 Python 逻辑，不需要启动 Blender 即可快速运行。

**执行命令 (PowerShell)**:
```powershell
python "X:\AI_Automation\.gemini\skills\blender-asset-info-comparator\scripts\compare_asset_data.py" "路径A.json" "路径B.json" "输出报告.md"
```

## 输出产物
- 一份详细的 Markdown 对比报告。
- 包含层级缺失列表、点数不匹配列表、以及坐标漂移列表。
- 最终给出“完全一致”或“存在差异”的权威结论。
