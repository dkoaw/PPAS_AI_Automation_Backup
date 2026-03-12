import bpy
def run(results, asset_name):
    issues = []
    for mesh in bpy.data.meshes:
        if mesh.users > 0:
            for uv in mesh.uv_layers:
                if uv.name not in ["map1", "furuvmap"]:
                    issues.append(f"{mesh.name} UV: {uv.name}")
    results.append({"check": "UV Layer Naming", "status": "FAIL" if issues else "PASS", "issues": issues})
