import bpy, os, sys
import core_utils as utils
def run(asset_name, report):
    static_grp = bpy.data.objects.get(f"{asset_name}_staticCurve_Grp")
    fur_col = bpy.data.collections.get("Fur")
    fur_name_counts = {}
    for obj in bpy.data.objects:
        if obj.type in ['CURVE', 'CURVES']:
            is_in_fur = (fur_col and obj.name in fur_col.objects) or any(p.name.endswith(("_fur_crv_Grp", "_hair_crv_Grp")) for p in obj.users_collection)
            if static_grp and obj.parent == static_grp:
                utils.ensure_hidden(obj, report, "staticcurve")
                part = utils.parse_source_curve_part(obj.name, asset_name)
                obj.name = f"{asset_name}_{part}_staticCurve"
            elif is_in_fur:
                utils.ensure_visible(obj, report, "Fur Group")
                src = utils.get_source_object_name(obj)
                if src:
                    part = utils.parse_source_curve_part(src, asset_name)
                    if "hair" in src.lower() and "static" not in src.lower():
                        # Simple logic for now to ensure name update
                        obj.name = f"{asset_name}_{part}_hair"
                    else:
                        obj.name = f"{asset_name}_{part}_fur"
