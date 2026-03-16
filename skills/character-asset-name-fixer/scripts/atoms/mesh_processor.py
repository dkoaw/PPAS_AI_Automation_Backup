import bpy, os, sys
import core_utils as utils

def run(asset_name, report):
    """Refactored Mesh Processor - 100% Logic Match"""
    hiddenmesh_grp = bpy.data.objects.get(asset_name + "_hiddenMesh_Grp")

    # Re-calculate group lists based on previous stage results
    special_groups = [bpy.data.objects.get("Group"), bpy.data.objects.get("cache"), hiddenmesh_grp]
    group_empties = [obj for obj in bpy.data.objects if obj.type == 'EMPTY' and obj not in special_groups]

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # 1. Hidden / Visible Control
            if hiddenmesh_grp and obj.parent == hiddenmesh_grp:
                utils.ensure_hidden(obj, report, "hiddenMesh")
            else:
                utils.ensure_visible(obj, report, "Regular Mesh")

            part, digits = utils.parse_mesh_part_digits(obj.name, asset_name)
            
            # EXEMPTION CHECK: eyeball / vitreous
            if part is None and digits is None:
                continue # Skip renaming for these exempted objects

            if not digits: digits = "1"

            # 2. Logic based on parent
            if obj.parent in group_empties:
                # Basic name sync from parent
                parent_part = utils.parse_group_part(obj.parent.name, asset_name)     
                obj.name = asset_name + "_" + parent_part + digits
            elif hiddenmesh_grp and obj.parent == hiddenmesh_grp:
                # For hidden mesh, keep its existing identity keywords if possible
                if not obj.name.startswith(asset_name + "_"):
                    obj.name = asset_name + "_" + obj.name
            elif obj.parent not in special_groups:
                # Orphan mesh handling
                t_grp_name = asset_name + "_" + (part or "misc") + "_Grp"
                t_grp = bpy.data.objects.get(t_grp_name) or bpy.data.objects.new(t_grp_name, None)
                if t_grp.name not in bpy.data.collections.get("Collection").objects.keys():
                    bpy.data.collections.get("Collection").objects.link(t_grp)        
                t_grp.parent = bpy.data.objects.get("cache")
                obj.parent = t_grp
                obj.name = asset_name + "_" + (part or "misc") + digits

            # 3. UV Correction
            if obj.data:
                for uv in obj.data.uv_layers:
                    if uv.name not in ["map1", "furuvmap"]:
                        uv.name = "map1"
