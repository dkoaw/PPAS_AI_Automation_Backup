import sys
import os
import bpy

# 确保能找到同级的 ppas_layer_core
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import ppas_layer_core

def execute():
    """
    执行【Cycles 3维光照层】的核心逻辑
    - 渲染器：CYCLES
    - Scene层级唯一：是 (SceneC_light)
    - 渲染层级递增：视图层自增 SceneC_light_001
    """
    base_name = "SceneC_light"
    engine = 'CYCLES'
    unique = True
    
    print(f"[Module Execute] 正在调用 CYCLES 引擎创建 {base_name} 3维光照层...")
    
    # 1. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    # 2. ViewLayer 层级勾选
    # 通道勾选 (遵照诉求：不随意勾选附加通道)
    # 勾选 Denoising Data
    try:
        new_vl.cycles.denoising_store_passes = True
    except AttributeError:
        pass # 版本兼容防报错
    
    # 3. 自动运用【管线专属：层级自发光静音】关闭全局/该层所有自发光
    if hasattr(bpy.ops.ppas, 'mute_emission_on_layer'):
        try:
            active_window = bpy.context.window or bpy.data.window_managers[0].windows[0]
            with bpy.context.temp_override(window=active_window, scene=new_scene, view_layer=new_vl):
                bpy.ops.ppas.mute_emission_on_layer()
                print(f"[Module Execute] 成功在 {new_vl.name} 执行 [层关闭 EMI 自发光] 技能。")
        except Exception as e:
            print(f"[Module Execute] 层关闭 EMI 自发光调用失败: {e}")
            
    # 4. 只保留 TreD_Light，关闭 ALL_Light 下的其他灯光组
    def keep_only_tred_light(layer_coll):
        closed_count = 0
        if layer_coll.name.lower() == "all_light":
            for child in layer_coll.children:
                if child.name.lower() != "tred_light":
                    child.exclude = True
                    closed_count += 1
            return closed_count
            
        for child in layer_coll.children:
            res = keep_only_tred_light(child)
            if res > 0:
                return res
        return 0

    closed_count = keep_only_tred_light(new_vl.layer_collection)
            
    print(f"[Module Execute] 成功在 {new_vl.name} 排除了 {closed_count} 个非 TreD_Light 的灯光组。")
                
    return new_scene, new_vl
