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
    print(f"--- 启动全局 SSS 层级智能覆盖 V3 ({TARGET_LAYER_NAME}) ---")
    
    # 1. 自动提取材质
    override_mat = get_or_append_material_from_asset_libs(OVERRIDE_MAT_NAME)
    if not override_mat or not getattr(override_mat, 'use_nodes', False):
        print(f"Error: 无法获取材质 {OVERRIDE_MAT_NAME}")
        return

    # 2. 注册核心驱动函数
    CORE_HANDLER_CODE = r"""
import bpy
def get_current_layer_name(depsgraph):
    # 优先尝试获取当前 UI 窗口正在显示的渲染层（视口实时刷新最准）
    try:
        if bpy.context.window:
            return bpy.context.window.view_layer.name
    except: pass
    
    # 其次尝试全局上下文
    try:
        if bpy.context.view_layer:
            return bpy.context.view_layer.name
    except: pass
    
    # 后台离线渲染（F12）时的兜底
    if hasattr(depsgraph, "view_layer"):
        return depsgraph.view_layer.name
        
    return ""
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

    # 3. 将 3s_shader 封装为可调用的 Node Group
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

    # 4. 遍历所有材质，进行“微创手术”植入
    processed_count = 0
    for mat in bpy.data.materials:
        if mat.name == OVERRIDE_MAT_NAME or not getattr(mat, 'use_nodes', False) or not mat.node_tree:
            continue
            
        # 智能透明度检测
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
            
        # 寻找真正的原材质输出端，清理旧节点
        old_mixer = next((n for n in mat.node_tree.nodes if n.label == "Smart_SSS_Mixer"), None)
        if old_mixer:
            if not old_mixer.inputs[1].is_linked: continue
            true_orig_socket = old_mixer.inputs[1].links[0].from_socket
            mat.node_tree.nodes.remove(old_mixer)
            # 清理旧的传感器
            old_sensor = next((n for n in mat.node_tree.nodes if n.label == "Layer_Sensor"), None)
            if old_sensor: mat.node_tree.nodes.remove(old_sensor)
            # 清理旧的 SSS Group 节点
            old_sss_node = next((n for n in mat.node_tree.nodes if n.type == 'GROUP' and "SSS_Core" in getattr(n.node_tree, "name", "")), None)
            if old_sss_node: mat.node_tree.nodes.remove(old_sss_node)
        else:
            true_orig_socket = out_node.inputs[0].links[0].from_socket

        # 核心：直接在当前材质树里创建 Value 和 Driver（绕过 EEVEE 的 NodeGroup 缓存 Bug）
        val_node = mat.node_tree.nodes.new('ShaderNodeValue')
        val_node.label = "Layer_Sensor"
        
        path = val_node.outputs[0].path_from_id("default_value")
        d = val_node.outputs[0].driver_add("default_value")
        d.driver.use_self = True
        d.driver.expression = f"1.0 if get_current_layer_name(depsgraph) == '{TARGET_LAYER_NAME}' else 0.0"

        # 植入手术
        mixer = mat.node_tree.nodes.new('ShaderNodeMixShader')
        mixer.label = "Smart_SSS_Mixer"
        
        sss_node = mat.node_tree.nodes.new('ShaderNodeGroup')
        sss_node.node_tree = sss_ng
        
        # 接线
        mat.node_tree.links.new(val_node.outputs[0], mixer.inputs[0])  # 直接连驱动值
        mat.node_tree.links.new(true_orig_socket, mixer.inputs[1]) # 原材质
        mat.node_tree.links.new(sss_node.outputs[0], mixer.inputs[2]) # SSS材质
        mat.node_tree.links.new(mixer.outputs[0], out_node.inputs[0]) # 输出
        
        processed_count += 1

    # 强制刷新视图
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas: area.tag_redraw()
            
    print(f"--- 植入完成！共给 {processed_count} 个材质直接打上了底层驱动 ---")

setup_global_sss_layer()