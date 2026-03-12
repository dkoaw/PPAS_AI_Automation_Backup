import bpy
def run(results, asset_name):
    unused = [m.name for m in bpy.data.meshes if m.users == 0]
    results.append({"check": "Unused Meshes", "status": "FAIL" if unused else "PASS", "issues": unused})
