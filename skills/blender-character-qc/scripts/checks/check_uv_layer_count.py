import bpy
def run(results, asset_name):
    multi_uv = []
    for mesh in bpy.data.meshes:
        if mesh.users > 0 and not "fur" in mesh.name.lower():
            if len(mesh.uv_layers) > 2:
                multi_uv.append(f"{mesh.name} (Count: {len(mesh.uv_layers)})")
            elif len(mesh.uv_layers) == 2:
                names = [u.name for u in mesh.uv_layers]
                if not ("map1" in names and "furuvmap" in names):
                    multi_uv.append(f"{mesh.name} (Invalid names: {names})")
    results.append({"check": "UV Layer Count", "status": "FAIL" if multi_uv else "PASS", "issues": multi_uv})
