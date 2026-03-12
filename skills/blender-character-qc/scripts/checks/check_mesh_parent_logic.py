import bpy
def run(results, asset_name):
    mismatch = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.parent and obj.parent.name.endswith('_Grp'):
            if 'hiddenMesh' not in obj.parent.name:
                parent_part = obj.parent.name.replace(asset_name + "_", "").replace("_Grp", "").replace("_part", "")
                expected = f"{asset_name}_{parent_part}"
                if not obj.name.startswith(expected):
                    mismatch.append(f"{obj.name} vs Parent {obj.parent.name}")
    results.append({"check": "Mesh Parent Logic", "status": "FAIL" if mismatch else "PASS", "issues": mismatch})
