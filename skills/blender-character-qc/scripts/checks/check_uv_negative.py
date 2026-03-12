import bpy
def run(results, asset_name):
    negative = []
    for mesh in bpy.data.meshes:
        if mesh.users > 0 and not "fur" in mesh.name.lower():
            if mesh.uv_layers.active:
                uv_layer = mesh.uv_layers.active.data
                has_neg = any(loop.uv.x < 0.0 or loop.uv.y < 0.0 for loop in uv_layer)
                if has_neg: negative.append(mesh.name)
    results.append({"check": "UV Negative Space", "status": "FAIL" if negative else "PASS", "issues": negative})
