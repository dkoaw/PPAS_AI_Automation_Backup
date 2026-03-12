import bpy
def run(results, asset_name):
    cameras = [c.name for c in bpy.data.cameras]
    results.append({"check": "Extra Cameras", "status": "FAIL" if cameras else "PASS", "issues": cameras})
