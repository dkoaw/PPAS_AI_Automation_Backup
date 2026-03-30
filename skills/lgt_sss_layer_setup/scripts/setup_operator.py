import bpy
import os
import re

class PPAS_OT_setup_sss_layer(bpy.types.Operator):
    """一键创建带智能拦截器的 SSS 分层 (支持原生预览)"""
    bl_idname = "ppas.setup_sss_layer"
    bl_label = "新建 SSS 分层"
    bl_options = {'REGISTER', 'UNDO'}

    def get_or_append_material(self, mat_name):
        mat = bpy.data.materials.get(mat_name)
        if mat: return mat
        
        prefs = bpy.context.preferences
        asset_libs = prefs.filepaths.asset_libraries
        if not asset_libs: return None
        
        for lib in asset_libs:
            lib_path = lib.path
            if not os.path.exists(lib_path): continue
            for root, dirs, files in os.walk(lib_path):
                for file in files:
                    if file.endswith(".blend"):
                        try:
                            with bpy.data.libraries.load(os.path.join(root, file), link=False) as (data_from, data_to):
                                if mat_name in data_from.materials:
                                    data_to.materials = [mat_name]
                        except: continue
                        new_mat = bpy.data.materials.get(mat_name)
                        if new_mat: return new_mat
        return None

    def inject_handler(self):
        HANDLER_CODE = r"""import bpy

# =================
OVERRIDE_MAT_NAME = "3s_shader"
_STORED_NATIVE_OVERRIDES = {}
# =================

def apply_sss(scene, *args):
    if "sss" not in scene.name.lower(): return
    
    override_mat = bpy.data.materials.get(OVERRIDE_MAT_NAME)
    if not override_mat: return
    
    # 1. 没收兵权：记录并清空原生粗暴覆盖，为手术做准备
    for layer in scene.view_layers:
        if layer.use and layer.material_override:
            _STORED_NATIVE_OVERRIDES[layer.name] = layer.material_override.name
            layer.material_override = None
            
    # 2. 精细手术：跳过透明材质，精确覆盖
    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
        for i, slot in enumerate(obj.material_slots):
            orig_mat = slot.material
            if not orig_mat: continue
            
            is_transparent = False
            if getattr(orig_mat, 'use_nodes', False) and orig_mat.node_tree:
                for node in orig_mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        alpha_input = node.inputs.get('Alpha')
                        if alpha_input and (alpha_input.is_linked or (type(alpha_input.default_value) in (float, int) and alpha_input.default_value < 0.99)):
                            is_transparent = True
                        break
            if is_transparent: continue
            
            obj[f"auto_orig_mat_{i}"] = orig_mat.name
            slot.material = override_mat

def restore_sss(scene, *args):
    if "sss" not in scene.name.lower(): return
    
    # 1. 恢复精细手术的修改
    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
        for i, slot in enumerate(obj.material_slots):
            prop_key = f"auto_orig_mat_{i}"
            if prop_key in obj:
                orig_mat_name = obj[prop_key]
                orig_mat = bpy.data.materials.get(orig_mat_name)
                if orig_mat: slot.material = orig_mat
                del obj[prop_key]
                
    # 2. 归还兵权：把原生覆盖还回去，保证视口预览继续生效
    for layer_name, mat_name in _STORED_NATIVE_OVERRIDES.items():
        if layer_name in scene.view_layers:
            mat = bpy.data.materials.get(mat_name)
            if mat:
                scene.view_layers[layer_name].material_override = mat
    _STORED_NATIVE_OVERRIDES.clear()

# 强制清理并重新注册
bpy.app.handlers.render_pre.clear()
bpy.app.handlers.render_post.clear()
bpy.app.handlers.render_cancel.clear()
bpy.app.handlers.render_pre.append(apply_sss)
bpy.app.handlers.render_post.append(restore_sss)
bpy.app.handlers.render_cancel.append(restore_sss)
"""
        tname = "Auto_SSS_Render_Handler.py"
        text = bpy.data.texts.get(tname) or bpy.data.texts.new(tname)
        text.clear()
        text.write(HANDLER_CODE)
        text.use_module = True 
        try:
            exec(HANDLER_CODE, {"bpy": bpy})
        except: pass

    def execute(self, context):
        mat_name = "3s_shader"
        
        # 1. 提取材质
        override_mat = self.get_or_append_material(mat_name)
        if not override_mat:
            self.report({'ERROR'}, f"资产库中未找到材质 '{mat_name}'")
            return {'CANCELLED'}
            
        # 2. 切换或创建场景
        scene_name = "Scene_sss"
        if scene_name not in bpy.data.scenes:
            bpy.ops.scene.new(type='LINK_COPY')
            context.scene.name = scene_name
        else:
            context.window.scene = bpy.data.scenes[scene_name]
            
        current_scene = context.scene
        
        # 3. 寻找最大的层序号
        max_index = 0
        pattern = re.compile(r"Scene_sss_(\d{3})")
        for layer in current_scene.view_layers:
            match = pattern.search(layer.name)
            if match:
                idx = int(match.group(1))
                if idx > max_index: max_index = idx
                
        new_layer_name = f"Scene_sss_{max_index + 1:03d}"
        
        # 4. 创建新层
        bpy.ops.scene.view_layer_add(type='COPY')
        new_layer = current_scene.view_layers[-1] # The newly copied one is active
        new_layer.name = new_layer_name
        
        # 5. 设置原生覆盖（为了视口预览）
        new_layer.material_override = override_mat
        
        # 6. 植入拦截器代码
        self.inject_handler()
        
        self.report({'INFO'}, f"成功创建: 场景 '{scene_name}' -> 层 '{new_layer_name}'")
        return {'FINISHED'}

classes = (
    PPAS_OT_setup_sss_layer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
