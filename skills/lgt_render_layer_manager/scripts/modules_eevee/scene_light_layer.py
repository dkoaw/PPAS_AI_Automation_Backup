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
    执行【3维光照层】的核心逻辑
    - 渲染器：EEVEE (全局默认)
    - Scene层级唯一：否 (每次点击全新生成独立层环境)
    - 渲染层级递增：从 Scene_light_001 起递增
    """
    base_name = "Scene_light"
    engine = 'BLENDER_EEVEE'
    unique = True
    
    print(f"[Module Execute] 正在调用 EEVEE 引擎创建 {base_name} 3维光照层...")
    
    # 1. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 2. 隔离化的本层独占设置区 (三维灯光层需要阴影光追)
    new_scene.eevee.use_shadows = True
    new_scene.eevee.use_raytracing = True
    
    # 3. 免疫护城河：防止被意外覆盖
    new_scene["ppas_protected_keys"] = ["use_shadows", "use_raytracing"]
    
    # 4. ViewLayer 层级独占勾选
    new_vl.use_pass_z = True
    new_vl.use_pass_cryptomatte_object = True
    new_vl.use_pass_cryptomatte_material = True
    
    # 5. 自动运用【管线专属：自发光静音黑魔法】关闭本层全体材质的自发光 (EMI)
    if hasattr(bpy.ops.ppas, 'mute_emission_on_layer'):
        try:
            # 修改 context 以符合算子调用的环境安全限制
            active_window = bpy.context.window or bpy.data.window_managers[0].windows[0]
            with bpy.context.temp_override(window=active_window, scene=new_scene, view_layer=new_vl):
                bpy.ops.ppas.mute_emission_on_layer()
                print(f"[Module Execute] 成功在 {new_vl.name} 执行 [层关闭 EMI] 技能。")
        except Exception as e:
            print(f"[Module Execute] 层关闭 EMI 技能调用失败: {e}")
            
    # 6. 自动关闭特定灯光集合 (TwoD_Light, Fog_Light, Sss_Light)
    def exclude_collection(layer_coll, target_name):
        if layer_coll.name == target_name:
            layer_coll.exclude = True
            return True
        for child in layer_coll.children:
            if exclude_collection(child, target_name):
                return True
        return False

    targets_to_close = ["TwoD_Light", "Fog_Light", "Sss_Light"]
    closed_count = 0
    for t in targets_to_close:
        if exclude_collection(new_vl.layer_collection, t):
            closed_count += 1
            
    print(f"[Module Execute] 成功在 {new_vl.name} 排除 (Exclude) 了 {closed_count} 个特定的灯光集合。")
                
    return new_scene, new_vl
