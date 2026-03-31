import bpy
import os
import re

class PPAS_OT_setup_sss_layer(bpy.types.Operator):
    """一键创建 SSS 分层 (克隆自 pose_v1 稳定版: 视口覆盖 + 渲染拦截器)"""
    bl_idname = "ppas.setup_sss_layer"
    bl_label = "新建 SSS 分层 (Pose_v1 Stable)"
    bl_options = {'REGISTER', 'UNDO'}

    OVERRIDE_MAT_NAME = "3s_shader"

    def get_or_append_material(self, mat_name):
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

    def inject_pose_v1_handler(self):
        # 完全复制自 pose_v1.blend 的拦截器源码
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
            
            # 使用智能检测：如果挂载了 Alpha 贴图或透明度 < 1.0，则保留原材质（保留透明效果）
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

    def execute(self, context):
        override_mat = self.get_or_append_material(self.OVERRIDE_MAT_NAME)
        if not override_mat:
            self.report({'ERROR'}, f"资产库中未找到材质 '{self.OVERRIDE_MAT_NAME}'")
            return {'CANCELLED'}

        # 1. 切换/创建 Scene_sss 场景 (为了匹配拦截器中的 sss 关键词判断)
        scene_name = "Scene_sss"
        if scene_name not in bpy.data.scenes:
            bpy.ops.scene.new(type='LINK_COPY')
            context.scene.name = scene_name
        else:
            context.window.scene = bpy.data.scenes[scene_name]
        
        current_scene = context.scene
        
        # 2. 寻找最大层序号并创建
        max_idx = 0
        for l in current_scene.view_layers:
            m = re.search(r"Scene_sss_(\d{3})", l.name)
            if m: max_idx = max(max_idx, int(m.group(1)))
        
        new_layer_name = f"Scene_sss_{max_idx + 1:03d}"
        bpy.ops.scene.view_layer_add(type='COPY')
        new_layer = current_scene.view_layers[-1]
        new_layer.name = new_layer_name
        
        # 3. 设置原生覆盖 (保视口预览)
        new_layer.material_override = override_mat
        
        # 4. 植入拦截器 (保正式渲染效果)
        self.inject_pose_v1_handler()
        
        self.report({'INFO'}, f"SSS 逻辑已完全克隆自 pose_v1: 场景 '{scene_name}' -> 层 '{new_layer_name}'")
        return {'FINISHED'}

classes = (
    PPAS_OT_setup_sss_layer,
)

def register(): 
    for cls in classes: bpy.utils.register_class(cls)

def unregister(): 
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
