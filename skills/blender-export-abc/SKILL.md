---
name: blender-export-abc
description: 处理资产并导出为 Alembic (.abc) 文件，包含禁用修改器和设置只读属性的功能。
---

# blender-export-abc 技能手册

## 技能描述
此技能用于将 Blender 资产的 `cache` 组内容导出为标准的 Alembic (.abc) 文件。它包含以下核心自动化动作：
1. **禁用修改器**：导出前自动关闭 `cache` 组下所有 Mesh 的所有修改器显示。
2. **保持结构**：完整保留 `cache` 组及其子级的层级路径。
3. **单帧导出**：仅导出第 1 帧的静态几何数据。
4. **属性锁定**：导出后自动将生成的 `.abc` 文件设为“只读”状态（属性级软锁定）。

## 触发条件
当用户要求“导出资产核心abc”、“生成abc模型文件”、“导出cache为abc”时触发。

## 执行流 (Logic Flow)
1. **沙盒拷贝**：将 `.blend` 文件复制一份命名为 `*_outputabc.blend`。
2. **静默导出**：
   ```powershell
   & "blender.exe" "副本.blend" -b -P "export_abc.py"
   ```
3. **后置清理**：导出完成后自动删除 `*_outputabc.blend` 副本。

## 输出产物
- `{原始文件名}.abc`：位于原始 blend 文件同级目录下，状态为只读。
