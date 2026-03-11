---
name: lib-master-qc
description: ysj 项目 lib 环节的完整自动化入库流水线。串联表格读取、洗稿、质检、入库比对与自动分发。
---

# lib-master-qc 技能手册

## 技能描述
这是 lib 环节的终极自动化总控调度中心。它会：
1.  自动读取现有的 `资产入库管理表.xlsx` 评估各资产的条件。
2.  智能执行三阶段任务：**QC_step_1 (初版洗稿)**、**lib-rig (绑定入库比对)**、**QC_step_2 (最终入库)**。
3.  自动在各阶段的目录中创建文件、洗稿、导出 JSON/ABC，并修改表格中的对应状态列 (`rtk` 或同行状态)。
4.  在发现任何缺失或错误时，立即跳过当前资产，并在汇总报告中清晰记录中断原因。

## 执行机制 (容错跳过)
-   当某个资产在前置条件不足（如找不到对应文件、状态不达标）或执行中遇到错误时，脚本会安全地中断当前资产的处理。
-   **绝不崩溃**：会自动抓取下一个资产继续处理。
-   **结果公示**：所有中断、成功、失败的信息都将汇总到统一的报告中。

## 触发条件
当用户要求“执行lib入库流程”、“跑一遍完整的lib环节qc”、“处理所有资产入库”时触发。

## 执行方式
该技能支持通过参数指定项目名称（默认为 `ysj`）。

**执行命令 (PowerShell)**:
```powershell
python "X:\AI_Automation\.gemini\skills\lib-master-qc\scripts\pipeline_executor.py" "项目名"
```
*例如：`python ...\pipeline_executor.py "ysj"`*

## 输出产物
1.  物理文件将按照手册规范被分配到 `QC_step_1`, `QC_step_2`, `libRig`, `libMaster` 等目录。
2.  最终汇总报告输出至 `X:\AI_Automation\Project\项目名\report\lib_qc_pipeline_[时间戳].md` 并自动打开。
