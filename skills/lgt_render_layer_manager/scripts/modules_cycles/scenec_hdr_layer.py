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
    执行【Cycles HDR 层】的核心逻辑
    - 渲染器：CYCLES
    - Scene层级唯一：是 (SceneC_hdr)
    - 渲染层级递增：视图层自增 SceneC_hdr_001
    """
    base_name = "SceneC_hdr"
    engine = 'CYCLES'
    unique = True
    
    print(f"[Module Execute] 正在调用 CYCLES 引擎创建 {base_name} HDR层...")
    
    # 1. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 2. ViewLayer 层级勾选
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
            
    # 4. HDR 层专属特权：暴力关闭整颗 ALL_Light 树枝
    def exclude_collection(layer_coll, target_name):
        # 兼容不区分大小写的匹配，防止命名不一致
        if layer_coll.name.lower() == target_name.lower():
            layer_coll.exclude = True
            return True
        for child in layer_coll.children:
            if exclude_collection(child, target_name):
                return True
        return False
        
    if exclude_collection(new_vl.layer_collection, "all_light"):
        print(f"[Module Execute] 成功在 {new_vl.name} 排除了全部 ALL_Light 集合资源。")
                
    return new_scene, new_vl
