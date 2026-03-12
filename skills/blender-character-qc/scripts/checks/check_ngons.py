import bpy
def run(results, asset_name):
    ngons = []
    for mesh in bpy.data.meshes:
        if mesh.users > 0 and any(len(p.vertices) > 4 for p in mesh.polygons):
            ngons.append(mesh.name)
    results.append({"check": "N-Gons Check", "status": "FAIL" if ngons else "PASS", "issues": ngons})
