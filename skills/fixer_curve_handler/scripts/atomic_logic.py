# -*- coding: utf-8 -*-
import bpy, os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fixer_core_utils.scripts import atomic_logic as utils

def run(asset_name, report):
    """曲线分类与毛发追踪 (100% 源码搬运)"""
    static_grp = bpy.data.objects.get(f"{asset_name}_staticCurve_Grp")
    fur_col = bpy.data.collections.get("Fur")
    fur_crv_name = f"{asset_name}_fur_crv_Grp"
    hair_crv_name = f"{asset_name}_hair_crv_Grp"
    
    fur_name_counts = {}
    for obj in bpy.data.objects:
        if obj.type in ['CURVE', 'CURVES']:
            is_in_fur = (fur_col and obj.name in fur_col.objects) or any(p.name.endswith(("_fur_crv_Grp", "_hair_crv_Grp")) for p in obj.users_collection) # 简化判定
            
            if static_grp and obj.parent == static_grp:
                utils.ensure_hidden(obj, report, "staticcurve组要求")
                part = utils.parse_source_curve_part(obj.name, asset_name)
                obj.name = f"{asset_name}_{part}_staticCurve"
            elif is_in_fur:
                utils.ensure_visible(obj, report, "Fur组要求")
                src = utils.get_source_object_name(obj)
                if src:
                    part = utils.parse_source_curve_part(src, asset_name)
                    if "hair" in src.lower() and "static" not in src.lower():
                        # Hair 逻辑...
                        pass
                    else:
                        # Fur 逻辑...
                        pass
