---
name: pipeline_cloud_backup
description: 用于将本地全量管线资产、模块化技能、以及 AI 的核心记忆快照一键同步至 GitHub 仓库。
---

# ☁️ pipeline_cloud_backup (管线云端备份技能)

## 技能描述
用于将本地全量管线资产、模块化技能、以及 AI 的核心记忆快照一键同步至 GitHub 仓库。

## 备份范围清单
1.  **Skills**: `X:\AI_Automation\.gemini\skills\` (所有的原子逻辑与文档)。
2.  **Tools**: `X:\AI_Automation\Pipeline_Tools\` (版本化的引导加载器)。
3.  **Memory**: 自动导出当前 AI 的 `Global Memories` 为 `memory_snapshot.md`。
4.  **Docs**: 相关的架构规划与执行流文档。

## 核心特性
- **静默认证**：采用专属 SSH Key (`id_ed25519_automation`) 实现无密码自动推送。
- **原子化快照**：每次备份前自动整理目录，确保云端结构清晰、无冗余。
- **自动日志**：Commit 信息会自动带上备份当天的日期与时间戳。

## 导出 Operator
- `ppas.cloud_backup_sync`: 执行全量云端备份同步。
