import bpy
def run(asset_name, report):
    scripts = [t for t in bpy.data.texts if not t.users]
    for t in scripts: bpy.data.texts.remove(t)
    master_col = bpy.data.collections.get("Collection") or bpy.data.collections.new("Collection")
    if master_col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(master_col)
    fur_col = bpy.data.collections.get("Fur") or bpy.data.collections.new("Fur")
    if fur_col.name not in master_col.children.keys():
        master_col.children.link(fur_col)
    group_empty = bpy.data.objects.get("Group") or bpy.data.objects.new("Group", None)
    if group_empty.name not in master_col.objects.keys(): master_col.objects.link(group_empty)
    cache_empty = bpy.data.objects.get("cache") or bpy.data.objects.new("cache", None)
    if cache_empty.name not in master_col.objects.keys(): master_col.objects.link(cache_empty)
    cache_empty.parent = group_empty
    for obj in bpy.data.objects:
        if fur_col and obj.name in fur_col.objects: continue
        if obj.name not in master_col.objects:
            try: master_col.objects.link(obj)
            except: pass
