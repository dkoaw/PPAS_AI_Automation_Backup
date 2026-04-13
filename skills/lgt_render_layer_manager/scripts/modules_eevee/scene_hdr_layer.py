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
    执行【HDR 层】的核心逻辑
    - 渲染器：CYCLES
    - Scene层级唯一：是 (Scene_hdr)
    - 渲染层级递增：是 (Scene_hdr_001, 002...)
    - 特殊要求：关闭 All_light 集合
    """
    base_name = "Scene_hdr"
    engine = 'BLENDER_EEVEE'
    unique = True
    
    print(f"[Module Execute] 正在调用 {engine} 引擎创建 {base_name} 渲染层...")
    
    # 1. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 2. 自动关闭 All_Light (及所有子集，按照原有的递归排他逻辑)
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
        print(f"[Module Execute] 成功在 {new_vl.name} 排除 (Exclude) 了全树枝的 All_Light 集合。")
        
        
    # 3. 自动运用【管线专属：层级自发光静音】关闭全局/该层所有自发光
    if hasattr(bpy.ops.ppas, 'mute_emission_on_layer'):
        try:
            active_window = bpy.context.window or bpy.data.window_managers[0].windows[0]
            with bpy.context.temp_override(window=active_window, scene=new_scene, view_layer=new_vl):
                bpy.ops.ppas.mute_emission_on_layer()
                print(f"[Module Execute] 成功在 {new_vl.name} 执行 [层关闭 EMI 自发光] 技能。")
        except Exception as e:
            print(f"[Module Execute] 层关闭 EMI 自发光调用失败: {e}")

    # HDR 的继承母场景管线早已写入到 ppas_hdr_blender_core 中
    # 当新建图层名称包含 Scene_hdr 时，它会自动向母场景剥夺继承数据
                
    return new_scene, new_vl
