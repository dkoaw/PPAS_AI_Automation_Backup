import bpy, os, sys
import core_utils as utils
def run(asset_name, report):
    hidden_grp = bpy.data.objects.get(f"{asset_name}_hiddenMesh_Grp")
    special = [bpy.data.objects.get("Group"), bpy.data.objects.get("cache"), hidden_grp]
    group_empties = [o for o in bpy.data.objects if o.type=='EMPTY' and o not in special]
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if hidden_grp and obj.parent == hidden_grp: utils.ensure_hidden(obj, report, "hiddenMesh")
            else: utils.ensure_visible(obj, report, "Standard Mesh")
            part, digits = utils.parse_mesh_part_digits(obj.name, asset_name)
            if obj.parent in group_empties:
                p_part = utils.parse_group_part(obj.parent.name, asset_name)
                obj.name = f"{asset_name}_{p_part}{digits or '1'}"
            elif hidden_grp and obj.parent == hidden_grp:
                if not obj.name.startswith(f"{asset_name}_"): obj.name = f"{asset_name}_{obj.name}"
            elif obj.parent not in special:
                t_grp_name = f"{asset_name}_{part or 'misc'}_Grp"
                t_grp = bpy.data.objects.get(t_grp_name) or bpy.data.objects.new(t_grp_name, None)
                if t_grp.name not in bpy.data.collections.get("Collection").objects: bpy.data.collections.get("Collection").objects.link(t_grp)
                t_grp.parent = bpy.data.objects.get("cache"); obj.parent = t_grp; obj.name = f"{asset_name}_{part or 'misc'}{digits or '1'}"
            for uv in obj.data.uv_layers:
                if uv.name not in ["map1", "furuvmap"]: uv.name = "map1"
