import bpy
def run(results, asset_name):
    issues = []
    group = bpy.data.objects.get("Group")
    cache = bpy.data.objects.get("cache")
    if not group or not cache: issues.append("Missing Group/cache skeleton")
    elif cache.parent != group: issues.append("cache must be child of Group")
    results.append({"check": "Hierarchy Nesting", "status": "FAIL" if issues else "PASS", "issues": issues})
