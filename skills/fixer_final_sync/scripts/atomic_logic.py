# -*- coding: utf-8 -*-
import bpy, os

def run(asset_name, report):
    """全局 Data 同步、Transform 校验与集合清理 (100% 源码搬运)"""
    # 1. 物理同步 Data 名字
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES']:
            if obj.data:
                expected = obj.name + "Shape"
                if obj.data.name != expected: obj.data.name = expected

    # 2. Transform 扫描
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES', 'EMPTY']:
            loc, rot, scl = obj.location, obj.rotation_euler, obj.scale
            if not (all(abs(v)<1e-5 for v in loc) and all(abs(v)<1e-5 for v in rot) and all(abs(v-1.0)<1e-5 for v in scl)):
                report["manual_fix_needed"].append(f"Transform 未归零: {obj.name}")

    # 3. 最终集合脱水
    fur_col = bpy.data.collections.get("Fur")
    if fur_col and len(fur_col.objects)==0 and len(fur_col.children)==0:
        bpy.data.collections.remove(fur_col)
