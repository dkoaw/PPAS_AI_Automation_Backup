---
name: sg-data-reader
description: 读取与查询 Flow Production Tracking (ShotGrid) 数据库的技能。当用户要求查询项目、资产、镜头或任务状态时触发此技能。关键字：shotgrid、flow、查询资产、查询任务状态、任务分配。
---

# Flow Production Tracking (ShotGrid) 数据读取工作流

此技能旨在为你提供直接访问公司底层 ShotGrid (Flow) 数据库的能力。所有的查询操作都将通过内网配置好的 Python API 接口以静默方式执行。

### 1. 构造查询参数 (Input JSON)
当你需要查询数据时，首先需要构造一个 JSON 格式的查询配置文件。
支持的操作(`action`)包括：
*   `find_project`：查询项目信息。
*   `find_assets`：查询某项目下的所有资产（支持传入 `asset_type` 过滤如 'chr', 'prp', 'env'）。
*   `find_tasks`：查询某个资产或镜头的任务列表及状态（需传入 `entity_type` 为 'Asset' 或 'Shot'，`entity_name` 为实体名，以及可选的 `step` 工序名）。

**使用 `write_file` 将 JSON 保存到临时目录：**
例如保存为：`X:\AI_Automation\.gemini\tmp\sg_query_in.json`

JSON 示例（查询某个资产的贴图任务）：
```json
{
  "action": "find_tasks",
  "project_name": "ysj",
  "entity_type": "Asset",
  "entity_name": "gaogeyaoguai",
  "step": "tex"
}
```

### 2. 执行查询脚本
编写完 JSON 后，使用 `run_shell_command` 工具执行后台查询。
你必须调用集成了 `shotgun_api3` 的 Blender 内置 Python 环境（路径不可更改）：

```powershell
$env:SG_QUERY_IN="X:\AI_Automation\.gemini\tmp\sg_query_in.json"; $env:SG_QUERY_OUT="X:\AI_Automation\.gemini\tmp\sg_query_out.json"; & "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" -b -P "scripts/sg_query.py"
```

### 3. 解析结果并输出
脚本运行结束后，它会将查询结果写入你指定的 `$env:SG_QUERY_OUT` 路径。
使用 `read_file` 读取 `X:\AI_Automation\.gemini\tmp\sg_query_out.json`。
根据返回的 `status` ("success" 或 "error") 和 `data` 数据，为用户用中文总结查询结果。

### 附录：状态码对照表 (sg_status_list)
在返回的任务数据中，通常会包含简写的状态码，请翻译给用户：
*   `wtg` (Waiting To Start) -> 等待开始
*   `rdy` (Ready To Start) -> 准备开始
*   `ip` (In Progress) -> 进行中
*   `rev` (Pending Review) -> 等待审核
*   `cmpt` (Completed) -> 已完成
*   `hld` (On Hold) -> 暂停
*   `omt` (Omitted) -> 已忽略/作废

### 4. 扫尾清理
在向用户报告结果后，请执行清理命令删除临时输入和输出的 JSON 文件。
