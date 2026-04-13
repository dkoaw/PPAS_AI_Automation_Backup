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

def inject_pose_v1_handler():
    HANDLER_CODE = r"""import bpy

OVERRIDE_MAT_NAME = "3s_shader"
_STORED_NATIVE_OVERRIDES = {}

def is_mat_transparent(mat):
    if not mat: return False
    name_lower = mat.name.lower()
    if "glass" in name_lower or "transp" in name_lower: return True
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_TRANSPARENT': return True
            if node.type == 'BSDF_PRINCIPLED':
                alpha_sock = node.inputs.get('Alpha')
                if alpha_sock and (alpha_sock.is_linked or alpha_sock.default_value < 1.0):
                    return True
    return False

def apply_sss(scene, *args):
    if "sss" not in scene.name.lower(): return
    override_mat = bpy.data.materials.get(OVERRIDE_MAT_NAME)
    if not override_mat: return

    # 1. 记录并清空原生覆盖
    for layer in scene.view_layers:
        if layer.use and layer.material_override:
            _STORED_NATIVE_OVERRIDES[layer.name] = layer.material_override.name
            layer.material_override = None

    # 2. 强制手术：智能跳过所有带有透明通道连线或透明属性的材质
    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
        for i, slot in enumerate(obj.material_slots):
            orig_mat = slot.material
            if not orig_mat or orig_mat.name == OVERRIDE_MAT_NAME: continue
            
            if is_mat_transparent(orig_mat):
                continue

            obj[f"auto_orig_mat_{i}"] = orig_mat.name
            slot.material = override_mat

def _restore_impl(scene_name):
    scene = bpy.data.scenes.get(scene_name)
    if not scene: return None
    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
        for i, slot in enumerate(obj.material_slots):
            prop_key = f"auto_orig_mat_{i}"
            if prop_key in obj:
                orig_mat_name = obj[prop_key]
                orig_mat = bpy.data.materials.get(orig_mat_name)
                if orig_mat: slot.material = orig_mat
                del obj[prop_key]
    for layer_name, mat_name in _STORED_NATIVE_OVERRIDES.items():
        if layer_name in scene.view_layers:
            mat = bpy.data.materials.get(mat_name)
            if mat: scene.view_layers[layer_name].material_override = mat
    _STORED_NATIVE_OVERRIDES.clear()
    return None

def restore_sss(scene, *args):
    if "sss" not in scene.name.lower(): return
    if getattr(bpy.app, "background", False):
        _restore_impl(scene.name)
    else:
        bpy.app.timers.register(lambda: _restore_impl(scene.name), first_interval=0.1)

bpy.app.handlers.render_pre.clear()
bpy.app.handlers.render_post.clear()
bpy.app.handlers.render_cancel.clear()
bpy.app.handlers.render_pre.append(apply_sss)
bpy.app.handlers.render_post.append(restore_sss)
bpy.app.handlers.render_cancel.append(restore_sss)
"""
    tname = "Auto_SSS_Render_Handler.py"
    text = bpy.data.texts.get(tname) or bpy.data.texts.new(tname)
    text.clear(); text.write(HANDLER_CODE); text.use_module = True
    exec(HANDLER_CODE, {"bpy": bpy})

def execute():
    base_name = "Scene_sss"
    engine = 'BLENDER_EEVEE'
    unique = True
    
    print(f"[Module Execute] 正在调用 EEVEE 引擎创建 {base_name} SSS渲染层...")
    
    # 1. 验证所需组件
    OVERRIDE_MAT_NAME = "3s_shader"
    override_mat = get_or_append_material(OVERRIDE_MAT_NAME)
    if not override_mat:
        raise Exception(f"资产库中未找到材质 '{OVERRIDE_MAT_NAME}'！中止渲染层创建。")
    
    # 2. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 3. 隔离化的本层独占设置区 (根据要求，关闭 Raytracing 光追)
    new_scene.eevee.use_raytracing = False
    
    # 4. 免疫护城河：防止全域同步时把它这层的设置覆盖成主场景的默认值
    new_scene["ppas_protected_keys"] = ["use_raytracing"]
    
    # 5. 原生材质覆盖覆盖 + 透贴拦截层注入
    new_vl.material_override = override_mat
    inject_pose_v1_handler()

    # 6. 自动关闭多余的灯光集合，只给本层保留 Sss_Light
    def exclude_collection(layer_coll, target_name):
        if layer_coll.name == target_name:
            layer_coll.exclude = True
            return True
        for child in layer_coll.children:
            if exclude_collection(child, target_name):
                return True
        return False

    targets_to_close = ["TreD_Light", "TwoD_Light", "Fog_Light"]
    closed_count = 0
    for t in targets_to_close:
        if exclude_collection(new_vl.layer_collection, t):
            closed_count += 1

    print(f"[Module Execute] 成功在 {new_scene.name} -> {new_vl.name} 注入 SSS 设置，并排除了 {closed_count} 个非 SSS 的灯光集合。")
    return new_scene, new_vl
