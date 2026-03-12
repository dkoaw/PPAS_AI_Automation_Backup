# -*- coding: utf-8 -*-
import bpy, os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fixer_core_utils.scripts import atomic_logic as utils

def run(asset_name, report):
    """组节点更名与物理归位 (100% 源码搬运)"""
    group_empty = bpy.data.objects.get("Group")
    cache_empty = bpy.data.objects.get("cache")
    staticcurve_grp_name = f"{asset_name}_staticCurve_Grp"
    hiddenmesh_grp_name = f"{asset_name}_hiddenMesh_Grp"
    
    # 物理识别特殊组
    static_grp = next((o for o in bpy.data.objects if o.type=='EMPTY' and o.name.lower()==staticcurve_grp_name.lower()), None)
    hiddenmesh_grp = bpy.data.objects.get(hiddenmesh_grp_name)
    
    special_groups = [group_empty, cache_empty]
    if static_grp: 
        special_groups.append(static_grp)
        static_grp.parent = group_empty
        static_grp.name = staticcurve_grp_name
    if hiddenmesh_grp:
        special_groups.append(hiddenmesh_grp)
        hiddenmesh_grp.parent = cache_empty

    group_empties = [obj for obj in bpy.data.objects if obj.type == 'EMPTY' and obj not in special_groups]
    
    for grp in group_empties:
        if len(grp.children) == 0:
            name_to_del = grp.name
            bpy.data.objects.remove(grp, do_unlink=True)
            report["fixed"].append(f"清理非法空组: {name_to_del}")
            continue
        
        # 强制归位于 cache 下
        if grp.parent not in group_empties and grp.parent not in special_groups:
            matrix_copy = grp.matrix_world.copy()
            grp.parent = cache_empty
            grp.matrix_world = matrix_copy
            
        part = utils.parse_group_part(grp.name, asset_name)
        expected_grp_name = f"{asset_name}_{part or 'misc'}_Grp"
        if grp.name != expected_grp_name:
            grp.name = expected_grp_name
