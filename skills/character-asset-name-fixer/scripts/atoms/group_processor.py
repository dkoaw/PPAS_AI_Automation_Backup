import bpy, os, sys
import core_utils as utils
def run(asset_name, report):
    group_empty = bpy.data.objects.get("Group")
    cache_empty = bpy.data.objects.get("cache")
    static_name = f"{asset_name}_staticCurve_Grp"
    hidden_name = f"{asset_name}_hiddenMesh_Grp"
    static_grp = next((o for o in bpy.data.objects if o.type=='EMPTY' and o.name.lower()==static_name.lower()), None)
    hidden_grp = bpy.data.objects.get(hidden_name)
    special = [group_empty, cache_empty]
    if static_grp: 
        special.append(static_grp); static_grp.parent = group_empty; static_grp.name = static_name
    if hidden_grp:
        special.append(hidden_grp); hidden_grp.parent = cache_empty
    group_empties = [obj for obj in bpy.data.objects if obj.type == 'EMPTY' and obj not in special]
    for grp in group_empties:
        if len(grp.children) == 0:
            bpy.data.objects.remove(grp, do_unlink=True); continue
        if grp.parent not in group_empties and grp.parent not in special:
            m = grp.matrix_world.copy(); grp.parent = cache_empty; grp.matrix_world = m
        part = utils.parse_group_part(grp.name, asset_name)
        expected = f"{asset_name}_{part or 'misc'}_Grp"
        if grp.name != expected: grp.name = expected
