# -*- coding: utf-8 -*-
import bpy, os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fixer_core_utils.scripts import atomic_logic as utils

def run(asset_name, report):
    """MESH 模型命名与 UV (100% 源码搬运)"""
    hiddenmesh_grp = bpy.data.objects.get(f"{asset_name}_hiddenMesh_Grp")
    special_groups = [bpy.data.objects.get("Group"), bpy.data.objects.get("cache"), hiddenmesh_grp]
    group_empties = [o for o in bpy.data.objects if o.type=='EMPTY' and o not in special_groups]

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # 1. 显隐
            if hiddenmesh_grp and obj.parent == hiddenmesh_grp: utils.ensure_hidden(obj, report, "hiddenMesh组要求")
            else: utils.ensure_visible(obj, report, "常规模型要求")
            
            # 2. 命名与 UV (严格源码逻辑)
            part, digits = utils.parse_mesh_part_digits(obj.name, asset_name)
            if obj.parent in group_empties:
                p_part = utils.parse_group_part(obj.parent.name, asset_name)
                obj.name = f"{asset_name}_{p_part}{digits or '1'}"
            elif hiddenmesh_grp and obj.parent == hiddenmesh_grp:
                if not obj.name.startswith(f"{asset_name}_"): obj.name = f"{asset_name}_{obj.name}"
            elif obj.parent not in special_groups:
                # 游离模型收容
                target_grp_name = f"{asset_name}_{part or 'misc'}_Grp"
                target_grp = bpy.data.objects.get(target_grp_name) or bpy.data.objects.new(target_grp_name, None)
                if target_grp.name not in bpy.data.collections.get("Collection").objects: 
                    bpy.data.collections.get("Collection").objects.link(target_grp)
                target_grp.parent = bpy.data.objects.get("cache")
                obj.parent = target_grp
                obj.name = f"{asset_name}_{part or 'misc'}{digits or '1'}"
            
            for uv in obj.data.uv_layers:
                if uv.name not in ["map1", "furuvmap"]: uv.name = "map1"
