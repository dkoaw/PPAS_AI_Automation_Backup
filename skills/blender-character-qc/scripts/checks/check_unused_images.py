import bpy
def run(results, asset_name):
    unused = [i.name for i in bpy.data.images if i.users == 0]
    results.append({"check": "Unused Images", "status": "FAIL" if unused else "PASS", "issues": unused})
