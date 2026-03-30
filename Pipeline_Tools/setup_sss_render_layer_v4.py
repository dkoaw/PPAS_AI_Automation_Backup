import bpy
import os

# ================= 配置区 =================
OVERRIDE_MAT_NAME = "3s_shader" 
TARGET_LAYER_NAME = "SSS_Pass"
# ==========================================

def get_or_append_material_from_asset_libs(mat_name):
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
                    blend_path = os.path.join(root, file)
                    try:
                        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                            if mat_name in data_from.materials: data_to.materials = [mat_name]
                    except: continue
                    new_mat = bpy.data.materials.get(mat_name)
                    if new_mat: return new_mat
    return None

def setup_global_sss_layer():
    print(f"--- 启动全局 SSS 层级智能覆盖 V4 ({TARGET_LAYER_NAME}) ---")
    
    override_mat = get_or_append_material_from_asset_libs(OVERRIDE_MAT_NAME)
    if not override_mat or not getattr(override_mat, 'use_nodes', False):
        print(f"Error: 无法获取材质 {OVERRIDE_MAT_NAME}")
        return

    # 1. 核心驱动函数 (防闪退缓存版)
    CORE_HANDLER_CODE = r"""
import bpy

def get_current_layer_name(depsgraph):
    # 获取全局缓存（解决 EEVEE 后台着色器编译线程丢失上下文导致闪退的问题）
    ns = bpy.app.driver_namespace
    if "_LAST_LAYER" not in ns:
        ns["_LAST_LAYER"] = "ViewLayer"
        
    # 优先尝试获取当前 UI 窗口正在显示的渲染层
    try:
        if bpy.context.window:
            ns["_LAST_LAYER"] = bpy.context.window.view_layer.name
            return ns["_LAST_LAYER"]
    except: pass
    
    # 其次看 depsgraph 是否携带真实名字
    if hasattr(depsgraph, "view_layer") and depsgraph.view_layer.name:
        ns["_LAST_LAYER"] = depsgraph.view_layer.name
        return ns["_LAST_LAYER"]
        
    # 如果是在极恶劣的后台编译环境（什么都拿不到），直接返回上一毫秒的缓存状态！
    return ns["_LAST_LAYER"]

def register():
    bpy.app.driver_namespace["get_current_layer_name"] = get_current_layer_name
if __name__ == "__main__": register()
"""
    tname = "Global_Layer_Driver_SSS.py"
    text = bpy.data.texts.get(tname) or bpy.data.texts.new(tname)
    text.clear()
    text.write(CORE_HANDLER_CODE)
    text.use_module = True 
    try:
        exec(CORE_HANDLER_CODE, {"bpy": bpy})
        bpy.app.driver_namespace["get_current_layer_name"] = bpy.app.driver_namespace.get("get_current_layer_name")
    except: pass

    # 2. 准备 SSS 材质组
    sss_group_name = f"SSS_Core_Group_{OVERRIDE_MAT_NAME}"
    if sss_group_name not in bpy.data.node_groups:
        sss_ng = bpy.data.node_groups.new(sss_group_name, 'ShaderNodeTree')
        if hasattr(sss_ng, 'interface'):
            sss_ng.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
        else:
            sss_ng.outputs.new('NodeSocketShader', "Shader")
        out_node = sss_ng.nodes.new('NodeGroupOutput')
        src_output = next((n for n in override_mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if src_output and src_output.inputs[0].is_linked:
            src_bsdf = src_output.inputs[0].links[0].from_node
            new_bsdf = sss_ng.nodes.new(src_bsdf.bl_idname)
            if src_bsdf.type == 'GROUP': new_bsdf.node_tree = src_bsdf.node_tree
            for inp in src_bsdf.inputs:
                if not inp.is_linked and hasattr(new_bsdf.inputs.get(inp.name), "default_value"):
                    try: new_bsdf.inputs[inp.name].default_value = inp.default_value
                    except: pass
            sss_ng.links.new(new_bsdf.outputs[0], out_node.inputs[0])
    sss_ng = bpy.data.node_groups[sss_group_name]

    # 3. 创建 Geometry Nodes 属性注入器
    gn_name = "SSS_Attribute_Injector"
    if gn_name not in bpy.data.node_groups:
        gn = bpy.data.node_groups.new(gn_name, 'GeometryNodeTree')
        if hasattr(gn, 'interface'):
            gn.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            gn.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        else:
            gn.inputs.new('NodeSocketGeometry', "Geometry")
            gn.outputs.new('NodeSocketGeometry', "Geometry")
        
        g_in = gn.nodes.new('NodeGroupInput')
        g_out = gn.nodes.new('NodeGroupOutput')
        
        store_attr = gn.nodes.new('GeometryNodeStoreNamedAttribute')
        store_attr.data_type = 'FLOAT'
        
        # In Blender 4.0+, the inputs are: 0:Geometry, 1:Selection, 2:Name, 3:Value
        try:
            store_attr.inputs["Name"].default_value = "SSS_Factor"
            store_attr.inputs["Value"].default_value = 1.0
        except:
            store_attr.inputs[2].default_value = "SSS_Factor"
            store_attr.inputs[3].default_value = 1.0
        
        gn.links.new(g_in.outputs[0], store_attr.inputs[0])
        gn.links.new(store_attr.outputs[0], g_out.inputs[0])
    gn = bpy.data.node_groups[gn_name]

    # 4. 清洗和改造所有材质
    for mat in bpy.data.materials:
        if mat.name == OVERRIDE_MAT_NAME or not getattr(mat, 'use_nodes', False) or not mat.node_tree: continue
            
        is_transparent = False
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                alpha_input = node.inputs.get('Alpha')
                if alpha_input and (alpha_input.is_linked or (type(alpha_input.default_value) in (float, int) and alpha_input.default_value < 0.99)):
                    is_transparent = True
                break
        if is_transparent: continue

        out_node = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not out_node or not out_node.inputs[0].is_linked: continue
            
        old_mixer = next((n for n in mat.node_tree.nodes if n.label == "Smart_SSS_Mixer"), None)
        if old_mixer:
            if not old_mixer.inputs[1].is_linked: continue
            true_orig_socket = old_mixer.inputs[1].links[0].from_socket
            mat.node_tree.nodes.remove(old_mixer)
            for n in list(mat.node_tree.nodes):
                if n.label == "Layer_Sensor" or (n.type == 'GROUP' and "SSS_Core" in getattr(n.node_tree, "name", "")):
                    mat.node_tree.nodes.remove(n)
        else:
            true_orig_socket = out_node.inputs[0].links[0].from_socket

        # 植入新的 Attribute 传感器
        attr_node = mat.node_tree.nodes.new('ShaderNodeAttribute')
        attr_node.attribute_name = "SSS_Factor"
        attr_node.label = "Layer_Sensor"
        
        mixer = mat.node_tree.nodes.new('ShaderNodeMixShader')
        mixer.label = "Smart_SSS_Mixer"
        
        sss_node = mat.node_tree.nodes.new('ShaderNodeGroup')
        sss_node.node_tree = sss_ng
        
        mat.node_tree.links.new(attr_node.outputs['Fac'], mixer.inputs[0])
        mat.node_tree.links.new(true_orig_socket, mixer.inputs[1])
        mat.node_tree.links.new(sss_node.outputs[0], mixer.inputs[2])
        mat.node_tree.links.new(mixer.outputs[0], out_node.inputs[0])

    # 5. 给所有实体物体挂载 GeoNode 并上驱动
    mod_name = "SSS_Layer_Trigger"
    driver_expr = f"1 if get_current_layer_name(depsgraph) == '{TARGET_LAYER_NAME}' else 0"
    
    for obj in bpy.context.scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
        
        has_opaque = False
        for slot in obj.material_slots:
            if slot.material and next((n for n in slot.material.node_tree.nodes if n.label == "Smart_SSS_Mixer"), None):
                has_opaque = True
                break
        if not has_opaque: continue

        mod = obj.modifiers.get(mod_name)
        if not mod: mod = obj.modifiers.new(name=mod_name, type='NODES')
        mod.node_group = gn
        
        for prop in ["show_viewport", "show_render"]:
            obj.driver_remove("modifiers[\"" + mod_name + "\"]." + prop)
            d = obj.driver_add("modifiers[\"" + mod_name + "\"]." + prop)
            d.driver.use_self = True
            d.driver.expression = driver_expr

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas: area.tag_redraw()
            
    print(f"--- V4 升级完成！已完美绕过材质全局评估限制 ---")

setup_global_sss_layer()