---
name: PPAS HDR Blender Core Engine
description: Core pipeline API hooking into Blender to execute whitelist validation, strict node graph weaving, and isolation sandboxing for the HDR tool.
---

# PPAS HDR Blender Core

## 核心职责 (Core Responsibilities)
1. **防呆防爆网**: 环境安全拦截 (Context Gatekeeper)，严格检验激活场景与环境是否隶属于特定的许可区域 (Scene[母] 或是被授权光照层)。
2. **底层黑箱挂载**: 将环境参数锁死入私密的数据槽 (`bpy.context.view_layer ["HDR_Steward_Pack"]`)。
3. **环境物理克隆织补**: 将共用的 `World` 剥离重构，重新搭建 `Mapping->EnvTex->HSV->Background` 标准基底，并注射上述挂载的变量。

## 预留 DNA 暗门 (Inheritance Bridge)
向外暴露专属接口：`pass_master_genes()`。允许外界流水线执行创建动作时，强行拷贝字典封装实现唯一指定情况下的参数继承流淌。
