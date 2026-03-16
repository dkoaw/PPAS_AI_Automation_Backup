import bpy
import re

def run(results, asset_name):
    mismatch = []
    exemption_keywords = ["eyeball", "vitreous"]
    
    for obj in bpy.data.objects:
        # We only check MESH objects that have a parent ending in _Grp
        if obj.type == 'MESH' and obj.parent and obj.parent.name.lower().endswith('_grp'):
            
            # Protection for hiddenMesh
            if 'hiddenMesh' in obj.parent.name:
                continue
                
            # EXEMPTION: Skip check for eyeball and vitreous as per user rules
            if any(k in obj.name.lower() for k in exemption_keywords):
                continue
            
            # 1. Parse Parent's Clean Identity (Mirroring Fixer logic)
            p_name = obj.parent.name
            # Physical strip of Blender auto-suffixes (.001)
            p_name = re.sub(r'\.\d+$', '', p_name)
            # Strip Asset Name prefix
            p_prefix = asset_name + "_"
            if p_name.startswith(p_prefix): p_name = p_name[len(p_prefix):]
            elif p_name.startswith(asset_name): p_name = p_name[len(asset_name):]
            # Strip _Grp suffix
            p_identity = re.sub(r'(?i)_?grp$', '', p_name).lstrip("_")
            
            # 2. Compare Child Name
            # Child should start with AssetName_Identity
            expected_base = f"{asset_name}_{p_identity}"
            
            if not obj.name.startswith(expected_base):
                mismatch.append(f"{obj.name} vs Parent {obj.parent.name}")
                
    results.append({
        "check": "Mesh Parent Logic", 
        "status": "FAIL" if mismatch else "PASS", 
        "issues": mismatch
    })
