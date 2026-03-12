import bpy
def run(results, asset_name):
    prefix_issues = []
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'EMPTY', 'CURVES']:
            if obj.name not in ["Group", "cache", "Fur", "Collection", "Scene"]:
                if not obj.name.startswith(f"{asset_name}_"):
                    prefix_issues.append(obj.name)
    results.append({"check": "Asset Prefix", "status": "FAIL" if prefix_issues else "PASS", "issues": prefix_issues})
