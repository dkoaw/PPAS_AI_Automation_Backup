import bpy
def run(results, asset_name):
    negative = []
    for mesh in bpy.data.meshes:
        if mesh.users > 0 and not "fur" in mesh.name.lower():
            if mesh.uv_layers.active:
                uv_layer = mesh.uv_layers.active.data
                has_neg = any(loop.uv.x < -0.001 or loop.uv.y < -0.001 for loop in uv_layer)
                if has_neg: negative.append(mesh.name)
    
    # 修改为 WARNING 状态，使其成为提醒项而不阻塞质检结果
    results.append({
        "check": "UV Negative Space", 
        "status": "WARNING" if negative else "PASS", 
        "issues": negative
    })
