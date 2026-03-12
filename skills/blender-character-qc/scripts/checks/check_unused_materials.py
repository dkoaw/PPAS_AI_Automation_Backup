import bpy
def run(results, asset_name):
    unused = [m.name for m in bpy.data.materials if m.users == 0]
    results.append({"check": "Unused Materials", "status": "FAIL" if unused else "PASS", "issues": unused})
