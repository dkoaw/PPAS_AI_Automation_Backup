import bpy, os, sys
import core_utils as utils

def run(asset_name, report):
    """Refactored Group Processor - 100% Logic Match"""
    group_empty = bpy.data.objects.get("Group")
    cache_empty = bpy.data.objects.get("cache")
    
    staticcurve_grp_name = asset_name + "_staticCurve_Grp"
    hiddenmesh_grp_name = asset_name + "_hiddenMesh_Grp"
    fur_crv_grp_name = asset_name + "_fur_crv_Grp"
    hair_crv_grp_name = asset_name + "_hair_crv_Grp"
    
    # 1. Identify all special groups FIRST to protect them
    static_grp = next((o for o in bpy.data.objects if o.type=='EMPTY' and o.name.lower()==staticcurve_grp_name.lower()), None)
    hiddenmesh_grp = bpy.data.objects.get(hiddenmesh_grp_name)
    fur_crv_grp = bpy.data.objects.get(fur_crv_grp_name)
    hair_crv_grp = bpy.data.objects.get(hair_crv_grp_name)
    
    special_groups = [group_empty, cache_empty]
    if static_grp: 
        special_groups.append(static_grp)
        static_grp.parent = group_empty
        static_grp.name = staticcurve_grp_name
    if hiddenmesh_grp:
        special_groups.append(hiddenmesh_grp)
        hiddenmesh_grp.parent = cache_empty
    if fur_crv_grp: special_groups.append(fur_crv_grp)
    if hair_crv_grp: special_groups.append(hair_crv_grp)

    # 2. Process other empties
    group_empties = [obj for obj in bpy.data.objects if obj.type == 'EMPTY' and obj not in special_groups]
    
    for grp in group_empties:
        if len(grp.children) == 0:
            name_to_del = grp.name
            bpy.data.objects.remove(grp, do_unlink=True)
            report["fixed"].append("Removed empty group: " + str(name_to_del))
            continue

        # ONLY move to cache if it's not a protected group or its child
        if grp.parent not in group_empties and grp.parent not in special_groups:
            matrix_copy = grp.matrix_world.copy()
            grp.parent = cache_empty
            grp.matrix_world = matrix_copy
            
        part = utils.parse_group_part(grp.name, asset_name)
        expected_grp_name = asset_name + "_" + (part or "misc") + "_Grp"
        if grp.name != expected_grp_name:
            grp.name = expected_grp_name
