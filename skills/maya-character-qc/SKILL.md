---
name: maya-character-qc
description: Maya端资产质检引擎。读取通用的 qc_profiles.json 规则，在 Maya 后台无头环境 (mayapy.exe) 中执行对应的原子质检项，输出与 Blender 端完全兼容的 qc_out.json 报告。
---

# Maya Character QC (Maya 资产自动化质检)

这是一个运行在 Maya 无头环境 (`mayapy.exe`) 中的自动化质检工具。它专门用于检查 `.ma` 和 `.mb` 文件，并与 Blender 端的总控管线实现了无缝对接。

## 核心特性
1. **配置驱动**：不会硬编码质检规则，而是动态读取 `X:\AI_Automation\.gemini\skills\blender-character-qc\scripts\qc_profiles.json`。
2. **报告兼容**：输出的 `qc_out.json` 格式与 Blender 质检完全一致，上层总控可直接读取并生成 Markdown 报告。
3. **静默执行**：通过 `mayapy.exe` 在后台极速验证，无需启动 Maya 图形界面。

## 环境变量
- `QC_STEP_NAME`: 要执行的检查阶段名称（例如 `"rig"`, `"lib"`）。
- `QC_OUT_PATH`: 质检结果 JSON 文件的输出路径。
- `MAYA_FILE_PATH`: 需要质检的 `.ma` 或 `.mb` 文件路径。
