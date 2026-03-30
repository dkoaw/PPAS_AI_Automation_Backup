import bpy

# ====== 配置区 ======
# 填写你用来覆盖的 SSS 材质球名称
OVERRIDE_MAT_NAME = "3s_shader" 
# ====================

def smart_material_override():
    scene = bpy.context.scene
    override_mat = bpy.data.materials.get(OVERRIDE_MAT_NAME)
    
    if not override_mat:
        print("Error: Override material not found: " + OVERRIDE_MAT_NAME)
        return

    print("--- Starting Smart Override for Scene: " + scene.name + " ---")

    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']:
            continue
            
        for i, slot in enumerate(obj.material_slots):
            orig_mat = slot.material
            if not orig_mat:
                continue
                
            # 关键魔法 1：转移材质链接层级（保护原始场景）
            slot.link = 'OBJECT'
            
            # 关键魔法 2：真正的智能透明度检测 (节点级)
            is_transparent = False
            if orig_mat.use_nodes and orig_mat.node_tree:
                # 寻找原理化 BSDF 节点
                for node in orig_mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        # 检查 Alpha 端口是否有贴图连入，或者值是不是小于 1
                        alpha_input = node.inputs.get('Alpha')
                        if alpha_input:
                            if alpha_input.is_linked:
                                is_transparent = True
                            elif type(alpha_input.default_value) in (float, int) and alpha_input.default_value < 0.99:
                                is_transparent = True
                        break
            
            if is_transparent:
                # 遇到真正连了透明贴图的材质（毛发、睫毛等），保持原样
                slot.material = orig_mat
            else:
                # 遇到虽然模式不对但没连透明贴图的实体，无情覆盖为 SSS
                slot.material = override_mat

    print("--- Smart Override Complete! ---")

smart_material_override()