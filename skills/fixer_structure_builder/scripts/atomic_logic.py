# -*- coding: utf-8 -*-
import bpy, os

def run(asset_name, report):
    """构建 Collection -> Group -> cache (100% 源码搬运)"""
    scripts = [t for t in bpy.data.texts if not t.users]
    for t in scripts: bpy.data.texts.remove(t)
    if scripts: report["fixed"].append(f"自动清理了 {len(scripts)} 个无用脚本")

    master_col = bpy.data.collections.get("Collection") or bpy.data.collections.new("Collection")
    if master_col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(master_col)
        
    fur_col = bpy.data.collections.get("Fur") or bpy.data.collections.new("Fur")
    if fur_col.name not in master_col.children.keys():
        master_col.children.link(fur_col)
        if fur_col.name in bpy.context.scene.collection.children.keys():
            bpy.context.scene.collection.children.unlink(fur_col)

    group_empty = bpy.data.objects.get("Group") or bpy.data.objects.new("Group", None)
    if group_empty.name not in master_col.objects.keys(): master_col.objects.link(group_empty)
    
    cache_empty = bpy.data.objects.get("cache") or bpy.data.objects.new("cache", None)
    if cache_empty.name not in master_col.objects.keys(): master_col.objects.link(cache_empty)
    cache_empty.parent = group_empty

    # 初始全量链接至 master_col
    for obj in bpy.data.objects:
        if fur_col and obj.name in fur_col.objects: continue
        if obj.name not in master_col.objects:
            try: master_col.objects.link(obj)
            except: pass
        for col in obj.users_collection:
            if col != master_col and col != fur_col: col.objects.unlink(obj)
