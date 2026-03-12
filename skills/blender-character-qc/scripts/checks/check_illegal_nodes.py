import bpy
def run(results, asset_name):
    illegal = [o.name for o in bpy.data.objects if o.type not in ['MESH', 'CURVE', 'EMPTY', 'ARMATURE', 'CURVES', 'POINTCLOUD']]
    results.append({"check": "Illegal Nodes", "status": "FAIL" if illegal else "PASS", "issues": illegal})
