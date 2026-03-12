import os, re, bpy
def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    if 'chr' in parts:
        idx = parts.index('chr')
        if idx + 1 < len(parts): return parts[idx + 1]
    return parts[0]
def parse_group_part(group_name, asset_name):
    name = group_name
    prefix = asset_name + "_"
    if name.startswith(prefix): name = name[len(prefix):]
    elif name.startswith(asset_name): name = name[len(asset_name):]
    name = name.lstrip("_")
    if name.endswith("_Grp"): name = name[:-4]
    name = re.sub(r'_part\d*$', '', name); name = re.sub(r'part\d*$', '', name)
    return name
def parse_mesh_part_digits(mesh_name, asset_name):
    name = mesh_name
    prefix = asset_name + "_"
    if name.startswith(prefix): name = name[len(prefix):]
    elif name.startswith(asset_name): name = name[len(asset_name):]
    name = name.lstrip("_").replace("Shape", "")
    match = re.search(r'^(.*?)(\d+)$', name)
    if match: return match.group(1), match.group(2)
    return name, "1"
def parse_source_curve_part(src_name, asset_name):
    name = src_name
    prefix = asset_name + "_"
    if name.startswith(prefix): name = name[len(prefix):]
    elif name.startswith(asset_name): name = name[len(asset_name):]
    name = name.lstrip("_")
    name = re.sub(r'(?i)_?staticcurve$', '', name); name = re.sub(r'(?i)_?haircurve$', '', name)
    name = re.sub(r'(?i)_?hair$', '', name); name = re.sub(r'(?i)_?fur$', '', name)
    return name
def ensure_hidden(obj, report, msg):
    if not obj.hide_get(): obj.hide_set(True)
    if not obj.hide_render: obj.hide_render = True
    report["fixed"].append(f"{msg}: Hidden {obj.name}")
def ensure_visible(obj, report, msg):
    if obj.hide_get(): obj.hide_set(False)
    if obj.hide_render: obj.hide_render = False
    report["fixed"].append(f"{msg}: Visible {obj.name}")
def get_source_object_name(obj):
    for mod in obj.modifiers:
        if hasattr(mod, 'target') and mod.target: return mod.target.name
        if hasattr(mod, 'object') and mod.object: return mod.object.name
        if mod.type == 'NODES':
            for k in mod.keys():
                try:
                    val = mod[k]
                    if hasattr(val, 'name') and hasattr(val, 'type'): return val.name
                except: pass
    return None
