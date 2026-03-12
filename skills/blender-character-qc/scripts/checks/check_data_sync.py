import bpy
def run(results, asset_name):
    mismatch = []
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES']:
            if obj.data and obj.data.name != obj.name + "Shape":
                mismatch.append(f"Obj: {obj.name} -> Data: {obj.data.name}")
    results.append({"check": "Data Name Sync", "status": "FAIL" if mismatch else "PASS", "issues": mismatch})
