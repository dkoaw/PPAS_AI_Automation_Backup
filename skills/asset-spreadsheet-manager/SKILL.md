---
name: asset-spreadsheet-manager
description: 生成和更新资产表格。读取指定项目的 chr, prp, env 资产，并同步 texMaster、rigMaster 和 facialTex 任务状态。
---

# asset-spreadsheet-manager 技能手册

## 技能描述
此技能用于维护和更新项目的“资产入库管理表”。它会自动从 ShotGrid 获取最新的资产列表及关键任务状态，并以 XLSX 格式持久化存储。

## ⚠️ 强制判定逻辑 (Update-First)
**每次调用该技能时，必须首先判定目标路径是否存在对应的表格文件：**
1. **若文件已存在**：系统必须以“更新模式”启动，读取现有内容。
2. **增量更新原则**：
    *   **只动三列**：系统极其守规矩，每次运行只会更新 `texMaster`、`rigMaster` 和 `facialTex` 这三列的状态，绝对不会碰你自己手动填写的其他列信息（如备注、QC状态、进度等）。
    *   **自动追新**：如果 ShotGrid 里出现了新资产，它会自动在表格末尾追加新行。

## 核心规则
1. **资产筛选**：仅处理 `chr` (角色), `prp` (道具), `env` (环境) 三种类型的资产。
2. **列序标准**：`资产类型` | `资产名称` | `texMaster` | `rigMaster` | `facialTex` | `lightMap` | `QC_step_1` | `灯光文件制作` | `libRig` | `QC_step_2` | `libMaster`。
3. **功能增强**：除了 `资产名称` 列外，所有表头均需开启 Excel **自动筛选 (AutoFilter)** 功能。
4. **状态约束**：任务状态列提供 Flow 标准状态下拉菜单，强制规范录入格式。
5. **属性放开**：文件不再设为只读，允许人工随时编辑。

## 触发条件
当用户要求“生成某某项目的资产表格”、“更新某某项目的资产表格”、“同步入库管理表”时触发。

## 执行方式
**执行命令 (PowerShell)**:
```powershell
python "X:\AI_Automation\.gemini\skills\asset-spreadsheet-manager\scripts\manage_spreadsheet.py" "项目名称"
```

## 输出产物
- `X:\AI_Automation\Project\项目名\work\spreadsheet\项目名_资产入库管理表.xlsx`
