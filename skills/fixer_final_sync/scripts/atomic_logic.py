import bpy, os

def run(asset_name, report):
    """Final global sync and Fur group cleanup (100% Source Port)"""
    fur_crv_grp_name = asset_name + "_fur_crv_Grp"
    hair_crv_grp_name = asset_name + "_hair_crv_Grp"
    
    # 1. Sync Data Names
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES']:
            if obj.data:
                expected = obj.name + "Shape"
                if obj.data.name != expected:
                    obj.data.name = expected

    # 2. Transform Scan
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES', 'EMPTY']:
            loc, rot, scl = obj.location, obj.rotation_euler, obj.scale
            is_loc_0 = all(abs(v) < 1e-5 for v in loc)
            is_rot_0 = all(abs(v) < 1e-5 for v in rot)
            is_scl_1 = all(abs(v - 1.0) < 1e-5 for v in scl)
            if not (is_loc_0 and is_rot_0 and is_scl_1):
                report["manual_fix_needed"].append("Transform Not Zero: " + str(obj.name))

    # 3. CRITICAL: Fur group explicit cleanup (Fixing the redundant group issue)
    fur_col = bpy.data.collections.get("Fur")
    if fur_col:
        for grp_name in [fur_crv_grp_name, hair_crv_grp_name]:
            grp = bpy.data.objects.get(grp_name)
            if grp:
                # Force link to Fur collection only
                if grp.name not in fur_col.objects.keys():
                    fur_col.objects.link(grp)
                
                # Unlink from ALL other collections
                for col in bpy.data.collections:
                    if col != fur_col and grp.name in col.objects.keys():
                        col.objects.unlink(grp)
                
                # Unlink from scene root collection if present
                if grp.name in bpy.context.scene.collection.objects.keys():
                    bpy.context.scene.collection.objects.unlink(grp)
                
                # REMOVE PARENT (Source line: if grp.parent is not None: grp.parent = None)
                if grp.parent is not None:
                    grp.parent = None
                    report["fixed"].append("Detached Fur container parent: " + str(grp.name))

        # Remove Fur collection if totally empty
        if len(fur_col.objects) == 0 and len(fur_col.children) == 0:
            bpy.data.collections.remove(fur_col)
