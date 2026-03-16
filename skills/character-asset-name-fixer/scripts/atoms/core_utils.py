import os, re, bpy

def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    for tag in ['chr', 'prp', 'env']:
        if tag in parts:
            idx = parts.index(tag)
            if idx + 1 < len(parts): return parts[idx + 1]
    PROJECTS = ['ysj', 'ssx']
    if parts[0].lower() in PROJECTS and len(parts) > 1:
        if parts[1].lower() in ['chr', 'prp', 'env'] and len(parts) > 2: return parts[2]
        return parts[1]
    return parts[0]

def parse_group_part(group_name, asset_name):
    """V2.2 - Ultra Clean Identity Extraction"""
    name = group_name
    # 1. Physical strip of ALL Blender auto-suffixes (.001, .002)
    name = re.sub(r'\.\d+$', '', name)
    # 2. Handle Asset Name prefix
    pfx = asset_name + "_"
    if name.startswith(pfx): name = name[len(pfx):]
    elif name.startswith(asset_name): name = name[len(asset_name):]
    # 3. Aggressive removal of ANY internal _Grp or _grp markers
    name = re.sub(r'(?i)_?grp', '', name)
    return name.strip("_")

def parse_mesh_part_digits(mesh_name, asset_name):
    name = mesh_name
    pfx = asset_name + "_"
    if name.startswith(pfx): name = name[len(pfx):]
    elif name.startswith(asset_name): name = name[len(asset_name):]
    name = name.lstrip("_").replace("Shape", "")
    if "eyeball" in name.lower() or "vitreous" in name.lower(): return None, None
    match = re.search(r'^([a-zA-Z_]+)(\d*)$', name)
    if match: return match.group(1), match.group(2)
    match = re.search(r'^(.*?)(\d+)$', name)
    if match: return match.group(1), match.group(2)
    return name, ""

def parse_source_curve_part(src_name, asset_name):
    name = src_name
    prefix = asset_name + "_"
    if name.startswith(prefix): name = name[len(prefix):]
    elif name.startswith(asset_name): name = name[len(asset_name):]
    name = name.lstrip("_")
    name = re.sub(r'(?i)_?staticcurve$', '', name)
    name = re.sub(r'(?i)_?haircurve$', '', name)
    name = re.sub(r'(?i)_?hair$', '', name)
    name = re.sub(r'(?i)_?fur$', '', name)
    return name

def ensure_hidden(obj, report, msg):
    if not obj.hide_get(): obj.hide_set(True)
    if not obj.hide_render: obj.hide_render = True
    report["fixed"].append(str(msg) + ": Hidden " + str(obj.name))

def ensure_visible(obj, report, msg):
    if obj.hide_get(): obj.hide_set(False)
    if obj.hide_render: obj.hide_render = False
    report["fixed"].append(str(msg) + ": Visible " + str(obj.name))

def get_source_object_name(obj):
    for mod in obj.modifiers:
        if hasattr(mod, 'target') and mod.target: return mod.target.name
        if hasattr(mod, 'object') and mod.object: return mod.object.name
        if mod.type == 'NODES':
            for key in mod.keys():
                try:
                    val = mod[key]
                    if hasattr(val, 'name') and hasattr(val, 'type'): return val.name 
                except: pass
    return None
