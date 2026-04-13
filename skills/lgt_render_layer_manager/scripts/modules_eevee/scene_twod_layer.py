import sys
import os
import bpy

parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import ppas_layer_core

def get_or_append_material(mat_name):
    mat = bpy.data.materials.get(mat_name)
    if mat: return mat
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    for lib in asset_libs:
        if not os.path.exists(lib.path): continue
        for root, _, files in os.walk(lib.path):
            for file in files:
                if file.endswith(".blend"):
                    try:
                        with bpy.data.libraries.load(os.path.join(root, file), link=False) as (data_from, data_to):
                            if mat_name in data_from.materials: data_to.materials = [mat_name]
                    except: continue
                    new_mat = bpy.data.materials.get(mat_name)
                    if new_mat: return new_mat
    return None


def execute():
    base_name = "Scene_twod"
    engine = 'BLENDER_EEVEE'
    unique = True
    
    print(f"[Module Execute] 正在调用 EEVEE 引擎创建 {base_name} 渲染层...")
    
    # 1. 验证所需组件
    OVERRIDE_MAT_NAME = "2d_shader"
    override_mat = get_or_append_material(OVERRIDE_MAT_NAME)
    if not override_mat:
        raise Exception(f"资产库中未找到材质 '{OVERRIDE_MAT_NAME}'！中止渲染层创建。")
    
    # 2. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 3. 隔离化的本层独占设置区 (关闭 Raytracing 光追)
    new_scene.eevee.use_raytracing = False
    
    # 4. 免疫护城河：防止全域同步覆盖
    new_scene["ppas_protected_keys"] = ["use_raytracing"]
    
    # 5. 直接执行原生渲染层覆盖算法，不再注入拦截器
    new_vl.material_override = override_mat

    # 6. 自动关闭多余的灯光集合，只给本层保留 TwoD_Light
    def exclude_collection(layer_coll, target_name):
        if layer_coll.name == target_name:
            layer_coll.exclude = True
            return True
        for child in layer_coll.children:
            if exclude_collection(child, target_name):
                return True
        return False

    targets_to_close = ["TreD_Light", "Fog_Light", "Sss_Light"]
    closed_count = 0
    for t in targets_to_close:
        if exclude_collection(new_vl.layer_collection, t):
            closed_count += 1

    print(f"[Module Execute] 成功在 {new_scene.name} -> {new_vl.name} 注入 2D 渲染层设置，并排除了 {closed_count} 个非 2D 的灯光集合。")
    return new_scene, new_vl
