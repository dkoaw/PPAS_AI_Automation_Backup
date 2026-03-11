# -*- coding: utf-8 -*-
"""
PPAS LGT Modular Launcher v15.9 (Append-Only Strict Compliance)
Date: 2026-03-09
Description: 严格执行全量 UI 叠加原则，恢复全量按钮，并新增灯光渲染层管理器 (Qt 空壳)。
"""

import bpy
import sys
import os
import importlib.util
from bpy.app.handlers import persistent

# 定义技能根目录
SKILLS_ROOT = r"X:\AI_Automation\.gemini\skills"

# 终极映射表：确保 15 个模块路径绝对正确
SKILLS_TO_LOAD = {
    "proj": "lgt_project_info/scripts/logic.py",           # 1. 工程识别：自动提取项目名称并支持刷新
    "audit": "lgt_texture_audit/scripts/logic.py",         # 2. 贴图审计：VRAM 深度采样审计与优化建议 (PySide)
    "res": "lgt_texture_res_optimizer/scripts/logic.py",   # 3. 贴图优化：焦距距离自动分级 & 1k/2k/4k 物理重定向
    "s_opt": "lgt_subdivision_optimizer/scripts/logic.py", # 4. 细分优化：基于视觉距离的自动细分档位分流 (2/1, 1/0, 0/0)
    "s_ed": "lgt_subdivision_editor/scripts/logic.py",     # 5. 细分档位：手动 0, 1, 2 快捷应用 (含法线感知)
    "norm": "lgt_normal_adjuster/scripts/logic.py",        # 6. 法线调整：带 ppas_original_strength 锁定保护的强度缩放
    "mute": "lgt_emission_mute/scripts/logic.py",          # 7. 自发光屏蔽：基于驱动器的当前层自发光黑名单 (累加式)
    "world_layer": "lgt_world_layer_settings/scripts/logic.py", # 7.5 环境光分层：基于 JSON 与驱动器的单层环境光控制
    "hide": "lgt_object_hide/scripts/logic.py",            # 8. 分层隐藏：V6 Robust 驱动器隐藏 (含原动画自动迁移保护)
    "show": "lgt_object_show/scripts/logic.py",            # 9. 分层显示：强制移除隐藏黑名单并执行多级刷新 (Mute Toggle)
    "render": "lgt_render_setup/scripts/logic.py",         # 10. 渲染设置：EEVEE Next / Cycles 生产级质量一键固化 (高性能秒切)
    "out": "lgt_output_config/scripts/logic.py",           # 11. 分辨率设置：100% 比例锁定及 4 项常用规格切换
    "nodes": "lgt_output_nodes/scripts/logic.py",          # 12. 输出节点：合成器 V15 精准对齐 (跳过未激活 Pass)
    "bat": "lgt_render_bat_generator/scripts/logic.py",    # 13. 渲染 BAT：生成单层渲染批处理及内部隔离管理器
    "qt": "lgt_qt_file_manager/scripts/logic.py",          # 14. 贴图管理：唤起外部独立开发的 Qt V4 版本文件整理器
    "layer_mgr": "lgt_render_layer_manager/scripts/logic.py", # 15. 层管理器：渲染层与对象显隐专属 Qt 独立面板
    "ui": "lgt_sidebar_ui/scripts/panel.py"                # 16. 总控面板：UI 界面排版与 Operator 挂载
}

def load_skill_module(name, rel_path):
    abs_path = os.path.join(SKILLS_ROOT, rel_path)
    if not os.path.exists(abs_path): return None
    module_name = f"ppas_mod_{name}"
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod
    return None

@persistent
def global_auto_refresh_qt(dummy=None):
    """全局监听器：寻找并刷新 Qt 渲染层面板"""
    if "ppas_mod_layer_mgr" in sys.modules:
        mod = sys.modules["ppas_mod_layer_mgr"]
        if hasattr(mod, "qt_layer_mgr_ref") and mod.qt_layer_mgr_ref:
            try:
                # 延迟 0.1 秒刷新，确保底层文件路径已更新
                bpy.app.timers.register(lambda: mod.qt_layer_mgr_ref.refresh_project_name() or None, first_interval=0.1)
            except RuntimeError:
                mod.qt_layer_mgr_ref = None
            except: pass

def register():
    bpy.types.Scene.ppas_project_name = bpy.props.StringProperty(name="Project Name", default="未识别")
    all_classes = []
    loaded_mods = []
    print("--- PPAS LGT v15.9 Reloading ---")
    for key, path in SKILLS_TO_LOAD.items():
        try:
            mod = load_skill_module(key, path)
            if mod:
                loaded_mods.append(mod)
                if hasattr(mod, "classes"):
                    all_classes.extend(mod.classes)
                print(f"  [OK] {key}")
        except Exception as e:
            print(f"  [Error] {key}: {e}")

    for cls in all_classes:
        try:
            bpy.utils.register_class(cls)
        except:
            try:
                bpy.utils.unregister_class(cls)
                bpy.utils.register_class(cls)
            except: pass
            
    # 执行扩展注册钩子 (如绑定 PointerProperty)，必须在 class 注册完后执行
    for mod in loaded_mods:
        if hasattr(mod, "register_extra"):
            try:
                mod.register_extra()
            except Exception as e:
                print(f"  [Extra Register Error]: {e}")
            
    # 注册全局事件监听器
    if global_auto_refresh_qt not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(global_auto_refresh_qt)
    if global_auto_refresh_qt not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(global_auto_refresh_qt)
        
    print(f"--- PPAS LGT v15.9: {len(all_classes)} Operators Online. ---")

def unregister():
    if global_auto_refresh_qt in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(global_auto_refresh_qt)
    if global_auto_refresh_qt in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(global_auto_refresh_qt)

if __name__ == "__main__":
    register()
