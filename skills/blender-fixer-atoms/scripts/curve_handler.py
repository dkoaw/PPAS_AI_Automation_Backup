import bpy, os, sys
import core_utils as utils
def run(asset_name, report):
    static_grp = bpy.data.objects.get(f"{asset_name}_staticCurve_Grp")
    fur_col = bpy.data.collections.get("Fur")
    master_col = bpy.data.collections.get("Collection")
    fur_crv_grp_name = f"{asset_name}_fur_crv_Grp"
    hair_crv_grp_name = f"{asset_name}_hair_crv_Grp"
    fur_crv_grp = bpy.data.objects.get(fur_crv_grp_name)
    hair_crv_grp = bpy.data.objects.get(hair_crv_grp_name)
    fur_name_counts = {}
    
    for obj in bpy.data.objects:
        if obj.type in ['CURVE', 'CURVES']:
            is_in_fur = (fur_col and obj.name in fur_col.objects.keys()) or \
                        any(p.name.endswith(("_fur_crv_Grp", "_hair_crv_Grp")) for p in obj.users_collection)
            if static_grp and obj.parent == static_grp:
                utils.ensure_hidden(obj, report, "staticcurve")
                part = utils.parse_source_curve_part(obj.name, asset_name)
                obj.name = f"{asset_name}_{part}_staticCurve"
            elif is_in_fur:
                utils.ensure_visible(obj, report, "Fur Group")
                if master_col and obj.name in master_col.objects.keys(): master_col.objects.unlink(obj)
                if fur_col and obj.name not in fur_col.objects.keys(): fur_col.objects.link(obj)
                src = utils.get_source_object_name(obj)
                if src:
                    part = utils.parse_source_curve_part(src, asset_name)
                    if "staticcurve" in src.lower() or "haircurve" in src.lower():
                        if not fur_crv_grp:
                            fur_crv_grp = bpy.data.objects.new(fur_crv_grp_name, None)
                            if fur_col: fur_col.objects.link(fur_crv_grp)
                        obj.parent = fur_crv_grp; base_new_name = f"{asset_name}_{part}_fur"
                    elif "hair" in src.lower():
                        if not hair_crv_grp:
                            hair_crv_grp = bpy.data.objects.new(hair_crv_grp_name, None)
                            if fur_col: fur_col.objects.link(hair_crv_grp)
                        obj.parent = hair_crv_grp; base_new_name = f"{asset_name}_{part}_hair"
                    else: continue
                    cnt = fur_name_counts.get(base_new_name, 0); fur_name_counts[base_new_name] = cnt + 1
                    obj.name = base_new_name if cnt == 0 else f"{base_new_name}{cnt}"
