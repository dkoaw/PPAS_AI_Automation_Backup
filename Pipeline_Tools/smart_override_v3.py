import bpy
import os

# ====== 配置区 ======
OVERRIDE_MAT_NAME = "3s_shader" 
# ====================

def get_or_append_material_from_asset_libs(mat_name):
    """自动遍历全网资产库，寻找并偷取材质"""
    # 1. 先检查本地内存有没有
    mat = bpy.data.materials.get(mat_name)
    if mat:
        return mat # 已经存在，直接返回
        
    print(f"[{mat_name}] not found locally. Hunting in Asset Libraries...")
    
    # 2. 获取所有已注册的资产库路径
    prefs = bpy.context.preferences
    asset_libs = prefs.filepaths.asset_libraries
    
    if not asset_libs:
        print("Error: No Asset Libraries configured in Blender Preferences!")
        return None
        
    # 3. 遍历资产库文件夹下的所有 .blend 文件
    for lib in asset_libs:
        lib_path = lib.path
        if not os.path.exists(lib_path): continue
            
        print(f"  -> Scanning Library: {lib.name} ({lib_path})")
        for root, dirs, files in os.walk(lib_path):
            for file in files:
                if file.endswith(".blend"):
                    blend_path = os.path.join(root, file)
                    
                    # 尝试不打开文件，只窥探里面的材质列表
                    try:
                        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                            if mat_name in data_from.materials:
                                print(f"  [FOUND!] Found '{mat_name}' in {file}. Appending now...")
                                data_to.materials = [mat_name]
                    except Exception as e:
                        continue # 忽略损坏的 blend 文件
                        
                    # 检查是否成功偷取到了
                    new_mat = bpy.data.materials.get(mat_name)
                    if new_mat:
                        return new_mat

    print(f"Error: Material '{mat_name}' could not be found in ANY Asset Library.")
    return None


def save_and_apply_override():
    scene = bpy.context.scene
    
    # 全自动资产库搜索提取
    override_mat = get_or_append_material_from_asset_libs(OVERRIDE_MAT_NAME)
    if not override_mat:
        return

    print("--- [ON] Applying SSS Override ---")
    count = 0

    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
            
        for i, slot in enumerate(obj.material_slots):
            orig_mat = slot.material
            if not orig_mat: continue
                
            # 记录原始材质名字到物体的自定义属性里
            prop_key = f"orig_mat_{i}"
            
            # 如果还没有记录过，就记录下来（防止重复运行覆盖掉记录）
            if prop_key not in obj:
                obj[prop_key] = orig_mat.name
            
            # 智能透明检测
            is_transparent = False
            if orig_mat.use_nodes and orig_mat.node_tree:
                for node in orig_mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        alpha_input = node.inputs.get('Alpha')
                        if alpha_input:
                            if alpha_input.is_linked:
                                is_transparent = True
                            elif type(alpha_input.default_value) in (float, int) and alpha_input.default_value < 0.99:
                                is_transparent = True
                        break
            
            if not is_transparent:
                slot.material = override_mat
                count += 1

    print(f"--- SSS Override Applied to {count} slots! ---")


def restore_original_materials():
    scene = bpy.context.scene
    print("--- [OFF] Restoring Original Materials ---")
    count = 0
    
    for obj in scene.objects:
        if obj.type not in ['MESH', 'CURVES', 'SURFACE']: continue
            
        for i, slot in enumerate(obj.material_slots):
            prop_key = f"orig_mat_{i}"
            
            # 如果这个槽位有备份记录
            if prop_key in obj:
                orig_mat_name = obj[prop_key]
                orig_mat = bpy.data.materials.get(orig_mat_name)
                
                if orig_mat:
                    slot.material = orig_mat
                    count += 1
                
                # 恢复完之后删除记录
                del obj[prop_key]
                
    print(f"--- Restored {count} slots to original materials! ---")

# ==========================================
# 控制台：在这里选择你要执行的动作！
# ==========================================

# 开启 SSS 覆盖（去掉下面这行的 # 号并运行）
save_and_apply_override()

# 恢复原始材质（去掉下面这行的 # 号并运行）
# restore_original_materials()