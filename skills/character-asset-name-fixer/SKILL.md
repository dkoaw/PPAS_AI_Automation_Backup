---
name: character-asset-name-fixer
description: 角色资产命名与层级修正。当用户提供 .blend 文件并要求“修正角色资产大纲”或按规则检查修正资产大纲结构时触发此技能。关键字：修正角色资产大纲、大纲修正、命名修正。
---

# 角色资产命名修正工作流

当用户提供 `.blend` 角色资产文件，并要求你进行“资产命名修正”时，你必须严格遵循此流程。此流程基于《Blender普通角色资产命名规则》定制。

### 1. 执行静默修正 (Headless Fixer)
使用 `run_shell_command` 工具执行后台 Python 脚本。
请将 `<file_path>` 替换为用户提供的 `.blend` 文件的绝对路径（包含空格需加引号）：

```powershell
$env:QC_FIX_OUT_PATH="X:\AI_Automation\.gemini\tmp\qc_fix_out.json"; & "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" -b "<file_path>" -P "scripts/rename_fixer.py"
```

### 2. 读取修正报告
脚本运行结束后，它会在临时路径生成一份 JSON 格式的修正报告，同时会自动在原文件目录下生成一份以 `_fixed.blend` 结尾的新文件。
使用 `read_file` 工具读取该报告文件：
`X:\AI_Automation\.gemini\tmp\qc_fix_out.json`

### 3. 生成中文修正与反馈报告
根据 JSON 报告，为用户整理一份 Markdown 格式的**资产命名修正反馈报告**。
报告需包含：
1. **自动修正成功的项**（例如：Mesh 数据命名后缀自动补齐为 `Shape`）。
2. **无法自动修正，需要人工介入的项**（例如：层级结构不对、命名不符合规范、Transform 非默认值等）。
3. 提醒用户，修正后的新文件已经生成为：`[原文件名]_fixed.blend`。

### 4. 扫尾工作
质检报告发送给用户后，务必使用 `run_shell_command` 删除临时生成的 JSON 报告文件：
`Remove-Item -Path "X:\AI_Automation\.gemini\tmp\qc_fix_out.json" -Force`
