import bpy
import os

# ================= 配置区 =================
OVERRIDE_MAT_NAME = "3s_shader" 
TARGET_LAYER_NAME = "SSS_Pass"
# ==========================================

def get_or_append_material_from_asset_libs(mat_name):
    mat = bpy.data.materials.get(mat_name)
    if mat: return mat
        
    print(f"[{mat_name}] not found locally. Hunting in Asset Libraries...")
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
                            if mat_name in data_from.materials:
                                data_to.materials = [mat_name]
                    except: continue
                        
                    new_mat = bpy.data.materials.get(mat_name)
                    if new_mat: return new_mat
    return None

def setup_global_sss_layer():
    print(f"--- 启动全局 SSS 层级智能覆盖 ({TARGET_LAYER_NAME}) ---")
    
    # 1. 自动提取材质
    override_mat = get_or_append_material_from_asset_libs(OVERRIDE_MAT_NAME)
    if not override_mat or not override_mat.use_nodes:
        print(f"Error: 无法获取材质 {OVERRIDE_MAT_NAME}")
        return

    # 2. 注册核心驱动函数逻辑
    CORE_HANDLER_CODE = r"""
import bpy
def get_current_layer_name(depsgraph):
    if hasattr(depsgraph, "view_layer"): return depsgraph.view_layer.name
    try: return bpy.context.view_layer.name
    except: return ""
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

    # 3. 将 3s_shader 封装为可调用的 Node Group (材质层级)
    sss_group_name = f"SSS_Core_Group_{OVERRIDE_MAT_NAME}"
    if sss_group_name in bpy.data.node_groups:
        sss_ng = bpy.data.node_groups[sss_group_name]
    else:
        sss_ng = bpy.data.node_groups.new(sss_group_name, 'ShaderNodeTree')
        if hasattr(sss_ng, 'interface'):
            sss_ng.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
        else:
            sss_ng.outputs.new('NodeSocketShader', "Shader")
            
        out_node = sss_ng.nodes.new('NodeGroupOutput')
        
        # 复制 3s_shader 里的节点
        # 这里只做最基础的复制，如果 3s_shader 是复杂的，建议直接在库里把它做成 Node Group
        src_output = next((n for n in override_mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if src_output and src_output.inputs[0].is_linked:
            src_bsdf = src_output.inputs[0].links[0].from_node
            new_bsdf = sss_ng.nodes.new(src_bsdf.bl_idname)
            if src_bsdf.type == 'GROUP':
                new_bsdf.node_tree = src_bsdf.node_tree
            for inp in src_bsdf.inputs:
                if not inp.is_linked and hasattr(new_bsdf.inputs.get(inp.name), "default_value"):
                    try: new_bsdf.inputs[inp.name].default_value = inp.default_value
                    except: pass
            sss_ng.links.new(new_bsdf.outputs[0], out_node.inputs[0])

    # 4. 控制器节点组逻辑 (输出 0 或 1)
    ctrl_group_name = "Global_SSS_Controller"
    if ctrl_group_name in bpy.data.node_groups:
        ctrl_ng = bpy.data.node_groups[ctrl_group_name]
    else:
        ctrl_ng = bpy.data.node_groups.new(ctrl_group_name, 'ShaderNodeTree')
        if hasattr(ctrl_ng, 'interface'):
            ctrl_ng.interface.new_socket("Is_SSS_Layer", in_out='OUTPUT', socket_type='NodeSocketFloat')
        else:
            ctrl_ng.outputs.new('NodeSocketFloat', "Is_SSS_Layer")
        
        val_node = ctrl_ng.nodes.new('ShaderNodeValue')
        val_node.name = "Value"
        out_node = ctrl_ng.nodes.new('NodeGroupOutput')
        ctrl_ng.links.new(val_node.outputs[0], out_node.inputs[0])
        
        # 添加驱动器
        path = val_node.outputs[0].path_from_id("default_value")
        # 清除可能存在的旧驱动
        if ctrl_ng.animation_data and ctrl_ng.animation_data.drivers:
            d = ctrl_ng.animation_data.drivers.find(path)
            if d: ctrl_ng.driver_remove(path)
            
        d = val_node.outputs[0].driver_add("default_value")
        d.driver.use_self = True
        d.driver.expression = f"1.0 if get_current_layer_name(depsgraph) == '{TARGET_LAYER_NAME}' else 0.0"

    # 5. 遍历所有材质，进行“微创手术”植入
    processed_count = 0
    for mat in bpy.data.materials:
        if mat.name == OVERRIDE_MAT_NAME or not mat.use_nodes or not mat.node_tree:
            continue
            
        # 智能透明度检测 (节点级)
        is_transparent = False
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                alpha_input = node.inputs.get('Alpha')
                if alpha_input and (alpha_input.is_linked or (type(alpha_input.default_value) in (float, int) and alpha_input.default_value < 0.99)):
                    is_transparent = True
                break
                
        # 遇到透明材质直接跳过
        if is_transparent: continue

        # 寻找最终输出节点
        out_node = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not out_node or not out_node.inputs[0].is_linked: continue
            
        orig_link = out_node.inputs[0].links[0]
        
        # 防止重复植入
        if orig_link.from_node.type == 'MIX_SHADER' and orig_link.from_node.label == "Smart_SSS_Mixer":
            continue

        # 植入手术
        mixer = mat.node_tree.nodes.new('ShaderNodeMixShader')
        mixer.label = "Smart_SSS_Mixer"
        
        ctrl_node = mat.node_tree.nodes.new('ShaderNodeGroup')
        ctrl_node.node_tree = ctrl_ng
        
        sss_node = mat.node_tree.nodes.new('ShaderNodeGroup')
        sss_node.node_tree = sss_ng
        
        # 接线
        mat.node_tree.links.new(ctrl_node.outputs[0], mixer.inputs[0]) # Fac 控制器
        mat.node_tree.links.new(orig_link.from_socket, mixer.inputs[1]) # Shader 1 原材质
        mat.node_tree.links.new(sss_node.outputs[0], mixer.inputs[2]) # Shader 2 SSS 材质
        mat.node_tree.links.new(mixer.outputs[0], out_node.inputs[0]) # 输出到表面
        
        processed_count += 1

    # 强制刷新
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas: area.tag_redraw()
            
    print(f"--- 植入完成！共给 {processed_count} 个材质做了底层驱动覆盖 ---")

setup_global_sss_layer()