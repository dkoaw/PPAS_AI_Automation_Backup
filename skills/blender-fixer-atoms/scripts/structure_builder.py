import bpy
def run(asset_name, report):
    # 1. Cleanup scripts
    scripts = [t for t in bpy.data.texts if not t.users]
    for t in scripts: bpy.data.texts.remove(t)
    
    # 2. Master Collection
    master_col = bpy.data.collections.get("Collection") or bpy.data.collections.new("Collection")
    if master_col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(master_col)
    
    # 3. Fur Collection (Source line 135: Force create/re-link Fur col)
    fur_col = bpy.data.collections.get("Fur")
    if not fur_col:
        fur_col = bpy.data.collections.new("Fur")
        master_col.children.link(fur_col)
    elif fur_col.name not in master_col.children.keys():
        master_col.children.link(fur_col)
        if fur_col.name in bpy.context.scene.collection.children.keys():
            bpy.context.scene.collection.children.unlink(fur_col)

    # 4. Root Empties
    group_empty = bpy.data.objects.get("Group") or bpy.data.objects.new("Group", None)
    if group_empty.name not in master_col.objects.keys(): master_col.objects.link(group_empty)
    cache_empty = bpy.data.objects.get("cache") or bpy.data.objects.new("cache", None)
    if cache_empty.name not in master_col.objects.keys(): master_col.objects.link(cache_empty)
    cache_empty.parent = group_empty
    
    # 5. Global Link to Master
    for obj in bpy.data.objects:
        if fur_col and obj.name in fur_col.objects: continue
        if obj.name not in master_col.objects:
            try: master_col.objects.link(obj)
            except: pass
        for col in obj.users_collection:
            if col != master_col and col != fur_col: col.objects.unlink(obj)
