import bpy
def run(results, asset_name):
    empty = []
    for c in bpy.data.collections:
        if c.name == 'Fur': continue
        if not c.objects and not c.children: empty.append(c.name)
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and len(o.children) == 0:
            if o.name not in ["Group", "cache", "Fur", f"{asset_name}_staticCurve_Grp", f"{asset_name}_hiddenMesh_Grp"]:
                empty.append(o.name)
    results.append({"check": "Empty Groups", "status": "FAIL" if empty else "PASS", "issues": empty})
