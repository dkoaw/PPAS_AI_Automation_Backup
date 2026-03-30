import bpy

# 你想要置顶的修改器名字（按顺序排列，第一个在最顶上）
target_modifiers = ["ani_cache", "USD_Transform_Fix"]

# 获取当前选中的所有物体
selected_objs = bpy.context.selected_objects

print("--- 开始移动修改器 ---")

for obj in selected_objs:
    if obj.type not in ['MESH', 'CURVES', 'SURFACE']:
        continue
        
    # 必须把当前物体设为活跃物体，Blender API 才允许移动它的修改器
    bpy.context.view_layer.objects.active = obj
    
    # 遍历目标修改器，依次把它们移到最前面
    for index, mod_name in enumerate(target_modifiers):
        # 检查这个物体上到底有没有这个修改器
        if mod_name in obj.modifiers:
            # 关键 API：把它移动到指定的层级 (0 是最顶上, 1 是第二层)
            bpy.ops.object.modifier_move_to_index(modifier=mod_name, index=index)
            print(f"[{obj.name}] 成功将 '{mod_name}' 移到第 {index} 层。")

print("--- 执行完毕！ ---")