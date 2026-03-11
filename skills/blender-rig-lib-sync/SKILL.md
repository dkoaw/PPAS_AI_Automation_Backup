---
name: blender-rig-lib-sync
description: Rig环节与Lib环节的资产数据比对与入库技能，自动执行结构比对并在通过后复制原生的 Maya 绑定文件。
---

# blender-rig-lib-sync 技能手册

## 技能描述
此技能用于执行 Rig 环节到 Lib 环节的最终跨资产校验与自动入库流程。

## 执行流程
1. **状态侦测**：调用 sg-data-reader 获取 ShotGrid 中 igMaster 任务的状态。若状态为 pub 或 	mpub，触发比对。
2. **结构比对**：调用 lender-asset-info-comparator 比对 Rig JSON 与 Lib JSON。
3. **成功入库 (PASS)**：如果比对完全一致，将最新的 **Rig 环节源文件（严格保持其原有的 .ma 或 .mb Maya 文件格式）** 拷贝到指定的入库路径：
   X:\AI_Automation\Project\ysj\work\assets_lib\chr\{资产名}\libRig\ysj_chr_{资产名}_lib_libRig.ma (后缀根据源文件而定，绝不篡改文件格式)。
4. **失败降级 (FAIL)**：如果比对不通过，系统将自动调用 lender-export-abc 技能，导出资产核心结构 ABC 文件备用，并输出详细的失败报告。
