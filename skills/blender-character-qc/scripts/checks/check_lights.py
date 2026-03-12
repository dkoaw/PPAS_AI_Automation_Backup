import bpy
def run(results, asset_name):
    lights = [l.name for l in bpy.data.lights]
    results.append({"check": "Extra Lights", "status": "FAIL" if lights else "PASS", "issues": lights})
