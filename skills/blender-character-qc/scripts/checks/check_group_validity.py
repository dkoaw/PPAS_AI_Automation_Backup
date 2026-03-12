import bpy
def run(results, asset_name):
    # Specialized logic for hiddenMesh and staticCurve group validity
    issues = []
    hidden_name = f"{asset_name}_hiddenMesh_Grp"
    static_name = f"{asset_name}_staticCurve_Grp"
    
    hidden = bpy.data.objects.get(hidden_name)
    if hidden:
        if hidden.parent != bpy.data.objects.get("cache"): issues.append(f"{hidden_name} must be under cache")
        for c in hidden.children:
            if c.type != 'MESH': issues.append(f"{c.name} is not Mesh in hidden group")
            elif not c.hide_get() or not c.hide_render: issues.append(f"{c.name} must be hidden")
            
    results.append({"check": "Group Validity", "status": "FAIL" if issues else "PASS", "issues": issues})
