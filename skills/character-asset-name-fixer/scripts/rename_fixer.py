import bpy
import json
import os
import sys
import re

def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    if 'chr' in parts:
        idx = parts.index('chr')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return parts[0]

def parse_group_part(group_name, asset_name):
    name = group_name
    prefix = asset_name + "_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    elif name.startswith(asset_name):
        name = name[len(asset_name):]
    name = name.lstrip("_")
    if name.endswith("_Grp"):
        name = name[:-4]
        
    # STRONGER CLEANUP FOR "DIRTY" SUFFIXES LIKE _part1, _part113
    name = re.sub(r'_part\d*$', '', name)
    name = re.sub(r'part\d*$', '', name)
    return name

def parse_mesh_part_digits(mesh_name, asset_name):
    name = mesh_name
    prefix = asset_name + "_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    elif name.startswith(asset_name):
        name = name[len(asset_name):]
    name = name.lstrip("_")
    if name.endswith("Shape"):
        name = name[:-5]
        
    match = re.search(r'^([a-zA-Z_]+)(\d*)$', name)
    if match:
        return match.group(1), match.group(2)
        
    match = re.search(r'^(.*?)(\d+)$', name)
    if match:
        return match.group(1), match.group(2)
        
    return name, ""
    
def parse_source_curve_part(src_name, asset_name):
    name = src_name
    prefix = asset_name + "_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    elif name.startswith(asset_name):
        name = name[len(asset_name):]
    name = name.lstrip("_")
    name = re.sub(r'(?i)_?staticcurve$', '', name)
    name = re.sub(r'(?i)_?haircurve$', '', name)
    name = re.sub(r'(?i)_?hair$', '', name)
    name = re.sub(r'(?i)_?fur$', '', name)
    return name

def ensure_hidden(obj, report, prefix_msg):
    changed = False
    if not obj.hide_get():
        obj.hide_set(True)
        changed = True
    if not obj.hide_render:
        obj.hide_render = True
        changed = True
    if changed:
        report["fixed"].append(f"{prefix_msg}: 隐藏节点 {obj.name}")

def ensure_visible(obj, report, prefix_msg):
    changed = False
    if obj.hide_get():
        obj.hide_set(False)
        changed = True
    if obj.hide_render:
        obj.hide_render = False
        changed = True
    if changed:
        report["fixed"].append(f"{prefix_msg}: 显示节点 {obj.name}")

def get_source_object_name(obj):
    for mod in obj.modifiers:
        if hasattr(mod, 'target') and mod.target:
            return mod.target.name
        if hasattr(mod, 'object') and mod.object:
            return mod.object.name
        if mod.type == 'NODES':
            for key in mod.keys():
                try:
                    val = mod[key]
                    if hasattr(val, 'name') and hasattr(val, 'type'):
                        return val.name
                except:
                    pass
    return None

def force_move_to_collection(obj, target_col):
    if obj.name not in target_col.objects:
        target_col.objects.link(obj)
    for col in obj.users_collection:
        if col != target_col:
            col.objects.unlink(obj)

def run_fixer(blend_file_path):
    filename = os.path.basename(blend_file_path)
    asset_name = extract_asset_name(filename)
    
    report = {
        "asset_name": asset_name,
        "fixed": [],
        "manual_fix_needed": []
    }
    
    scripts_to_remove = [t for t in bpy.data.texts if not t.users]
    if scripts_to_remove:
        count = len(scripts_to_remove)
        for t in scripts_to_remove:
            bpy.data.texts.remove(t)
        report["fixed"].append(f"自动清理了 {count} 个无用脚本(Text)")
    
    master_col = bpy.data.collections.get("Collection")
    if not master_col:
        master_col = bpy.data.collections.new("Collection")
        bpy.context.scene.collection.children.link(master_col)
        report["fixed"].append("创建顶层 Collection")
        
    fur_col = bpy.data.collections.get("Fur")
    if not fur_col:
        fur_col = bpy.data.collections.new("Fur")
        master_col.children.link(fur_col)
        report["fixed"].append("创建 Fur 集合")
    elif fur_col.name not in master_col.children.keys():
        master_col.children.link(fur_col)
        if fur_col.name in bpy.context.scene.collection.children.keys():
            bpy.context.scene.collection.children.unlink(fur_col)
        report["fixed"].append("修正 Fur 集合层级 (归入 Collection)")

    group_empty = bpy.data.objects.get("Group")
    if not group_empty:
        group_empty = bpy.data.objects.new("Group", None)
        master_col.objects.link(group_empty)
        report["fixed"].append("创建空组节点: Group")
    
    cache_empty = bpy.data.objects.get("cache")
    if not cache_empty:
        cache_empty = bpy.data.objects.new("cache", None)
        master_col.objects.link(cache_empty)
        cache_empty.parent = group_empty
        report["fixed"].append("创建空组节点: cache (父级为Group)")
    elif cache_empty.parent != group_empty:
        cache_empty.parent = group_empty
        report["fixed"].append("修正 cache 父级为 Group")

    for obj in bpy.data.objects:
        if fur_col and obj.name in fur_col.objects:
             continue
        if obj.name not in master_col.objects:
            try:
                master_col.objects.link(obj)
            except:
                pass
        for col in obj.users_collection:
            if col != master_col and col != fur_col:
                col.objects.unlink(obj)

    group_empties = []
    special_groups = [group_empty, cache_empty]
    
    staticcurve_grp_name = f"{asset_name}_staticCurve_Grp"
    hiddenmesh_grp_name = f"{asset_name}_hiddenMesh_Grp"
    
    staticcurve_grp = None
    for obj in bpy.data.objects:
        if obj.type == 'EMPTY' and obj.name.lower() == staticcurve_grp_name.lower():
            staticcurve_grp = obj
            break
            
    hiddenmesh_grp = bpy.data.objects.get(hiddenmesh_grp_name)
    
    if staticcurve_grp:
        special_groups.append(staticcurve_grp)
        if staticcurve_grp.parent != group_empty:
            staticcurve_grp.parent = group_empty
            report["fixed"].append(f"移动 {staticcurve_grp.name} 至 Group 下")
            
        if staticcurve_grp.name != staticcurve_grp_name:
            old_name = staticcurve_grp.name
            staticcurve_grp.name = staticcurve_grp_name
            report["fixed"].append(f"修正静态曲线组命名: {old_name} -> {staticcurve_grp_name}")
            
    if hiddenmesh_grp:
        special_groups.append(hiddenmesh_grp)
        if hiddenmesh_grp.parent != cache_empty:
            hiddenmesh_grp.parent = cache_empty
            report["fixed"].append(f"移动 {hiddenmesh_grp_name} 至 cache 下")

    fur_crv_grp_name = f"{asset_name}_fur_crv_Grp"
    hair_crv_grp_name = f"{asset_name}_hair_crv_Grp"
    fur_crv_grp = bpy.data.objects.get(fur_crv_grp_name)
    hair_crv_grp = bpy.data.objects.get(hair_crv_grp_name)
    
    if fur_crv_grp: special_groups.append(fur_crv_grp)
    if hair_crv_grp: special_groups.append(hair_crv_grp)

    for obj in bpy.data.objects:
        if obj.type == 'EMPTY' and obj not in special_groups:
            group_empties.append(obj)
            
    for grp in group_empties:
        if len(grp.children) == 0:
            name_to_del = grp.name
            bpy.data.objects.remove(grp, do_unlink=True)
            report["fixed"].append(f"自动清理非法空组: {name_to_del}")
            continue

        if grp.name.endswith("_fur_crv_Grp") or grp.name.endswith("_hair_crv_Grp"):
            if grp.name not in fur_col.objects:
                fur_col.objects.link(grp)
            # Remove from ALL other collections (including master_col and scene)
            for col in grp.users_collection:
                if col != fur_col:
                    col.objects.unlink(grp)
            
            if grp.parent is not None:
                grp.parent = None
                report["fixed"].append(f"强制解除毛发容器父级绑定以符合集合规则: {grp.name}")
            
            if grp.name.endswith("_fur_crv_Grp"):
                old_n = grp.name
                grp.name = fur_crv_grp_name
                fur_crv_grp = grp
                if old_n != fur_crv_grp_name: report["fixed"].append(f"修正Fur子组命名: {old_n} -> {fur_crv_grp_name}")
            elif grp.name.endswith("_hair_crv_Grp"):
                old_n = grp.name
                grp.name = hair_crv_grp_name
                hair_crv_grp = grp
                if old_n != hair_crv_grp_name: report["fixed"].append(f"修正Hair子组命名: {old_n} -> {hair_crv_grp_name}")
        else:
            if grp.parent not in group_empties and grp.parent not in special_groups:
                matrix_copy = grp.matrix_world.copy()
                grp.parent = cache_empty
                grp.matrix_world = matrix_copy
                report["fixed"].append(f"移动组节点 {grp.name} 至 cache 下")
                
            if grp.parent == cache_empty or grp.parent in group_empties:
                is_eye_exception = False
                p = grp
                while p:
                    if "eye_Grp" in p.name:
                        if "eyeball" in grp.name or "vitreous" in grp.name:
                            is_eye_exception = True
                            break
                    p = p.parent
                
                if not is_eye_exception:
                    part = parse_group_part(grp.name, asset_name)
                    if not part:
                        part = "misc"
                    expected_grp_name = f"{asset_name}_{part}_Grp"
                    if grp.name != expected_grp_name:
                        old_name = grp.name
                        grp.name = expected_grp_name
                        report["fixed"].append(f"修正组命名: {old_name} -> {expected_grp_name}")

    fur_name_counts = {}
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if hiddenmesh_grp and obj.parent == hiddenmesh_grp:
                ensure_hidden(obj, report, "hiddenMesh组要求")
            else:
                ensure_visible(obj, report, "常规模型要求")
                
            mesh_part, digits = parse_mesh_part_digits(obj.name, asset_name)
            if not digits:
                digits = "1"
            
            if obj.parent in group_empties:
                is_eye_exception = False
                p = obj.parent
                while p:
                    if "eye_Grp" in p.name:
                        if "eyeball" in obj.name or "vitreous" in obj.name:
                            is_eye_exception = True
                            break
                    p = p.parent
                        
                if not is_eye_exception:
                    parent_part = parse_group_part(obj.parent.name, asset_name)
                    expected_name = f"{asset_name}_{parent_part}{digits}"
                    if obj.name != expected_name:
                        old_name = obj.name
                        obj.name = expected_name
                        report["fixed"].append(f"修正子级模型命名以匹配父组: {old_name} -> {expected_name}")
            elif hiddenmesh_grp and obj.parent == hiddenmesh_grp:
                if not obj.name.startswith(f"{asset_name}_"):
                    old_name = obj.name
                    expected_name = f"{asset_name}_{obj.name}"
                    obj.name = expected_name
                    report["fixed"].append(f"补齐 hiddenMesh 模型前缀: {old_name} -> {expected_name}")
            elif obj.parent not in special_groups:
                if not mesh_part:
                    mesh_part = "misc"
                expected_grp_name = f"{asset_name}_{mesh_part}_Grp"
                
                target_grp = bpy.data.objects.get(expected_grp_name)
                if not target_grp:
                    target_grp = bpy.data.objects.new(expected_grp_name, None)
                    master_col.objects.link(target_grp)
                    target_grp.parent = cache_empty
                    report["fixed"].append(f"为游离模型创建归属组: {expected_grp_name}")
                    group_empties.append(target_grp)
                
                matrix_copy = obj.matrix_world.copy()
                obj.parent = target_grp
                obj.matrix_world = matrix_copy
                report["fixed"].append(f"移动游离模型 {obj.name} 至 {expected_grp_name} 组下")
                
                expected_name = f"{asset_name}_{mesh_part}{digits}"
                if obj.name != expected_name:
                    old_name = obj.name
                    obj.name = expected_name
                    report["fixed"].append(f"修正游离模型命名: {old_name} -> {expected_name}")
                    
            if obj.type == 'MESH':
                for uv in obj.data.uv_layers:
                    if uv.name != "map1" and uv.name != "furuvmap":
                        old_uv = uv.name
                        uv.name = "map1"
                        report["fixed"].append(f"修正非法 UV 名称: {obj.name} ({old_uv} -> map1)")

        elif obj.type in ['CURVE', 'CURVES']:
            is_in_fur_col = False
            if fur_col and obj.name in fur_col.objects:
                is_in_fur_col = True
            
            p = obj.parent
            while p:
                if p.name.endswith("_fur_crv_Grp") or p.name.endswith("_hair_crv_Grp"):
                    is_in_fur_col = True
                    break
                p = p.parent
                
            if staticcurve_grp and obj.parent == staticcurve_grp:
                ensure_hidden(obj, report, "staticcurve组要求")
                part = parse_source_curve_part(obj.name, asset_name)
                new_name = f"{asset_name}_{part}_staticCurve"
                
                if obj.name != new_name:
                    old_name = obj.name
                    obj.name = new_name
                    report["fixed"].append(f"严格结构化重建静态曲线命名: {old_name} -> {obj.name}")
                    
            elif is_in_fur_col:
                ensure_visible(obj, report, "Fur组要求")
                
                if obj.name in master_col.objects:
                    master_col.objects.unlink(obj)
                if fur_col and obj.name not in fur_col.objects:
                    fur_col.objects.link(obj)
                
                src_name = get_source_object_name(obj)
                if src_name:
                    part = parse_source_curve_part(src_name, asset_name)
                    
                    if "staticcurve" in src_name.lower() or "haircurve" in src_name.lower(): 
                        if not fur_crv_grp:
                            fur_crv_grp = bpy.data.objects.new(fur_crv_grp_name, None)
                            fur_col.objects.link(fur_crv_grp)
                            special_groups.append(fur_crv_grp)
                            report["fixed"].append(f"创建Fur子组: {fur_crv_grp_name}")
                        
                        if obj.parent != fur_crv_grp:
                            obj.parent = fur_crv_grp
                            report["fixed"].append(f"强制移动毛发曲线 {obj.name} 至 {fur_crv_grp_name} 组下")
                            
                        base_new_name = f"{asset_name}_{part}_fur"
                    else:
                        if "hair" in src_name.lower():
                            if not hair_crv_grp:
                                hair_crv_grp = bpy.data.objects.new(hair_crv_grp_name, None)
                                fur_col.objects.link(hair_crv_grp)
                                special_groups.append(hair_crv_grp)
                                report["fixed"].append(f"创建Hair子组: {hair_crv_grp_name}")
                                
                            if obj.parent != hair_crv_grp:
                                obj.parent = hair_crv_grp
                                report["fixed"].append(f"强制移动头发曲线 {obj.name} 至 {hair_crv_grp_name} 组下")
                                
                            base_new_name = f"{asset_name}_{part}_hair"
                        else:
                            base_new_name = src_name
                            report["manual_fix_needed"].append(f"曲线源物体 '{src_name}' 既不包含 'staticCurve' 也不包含 'hair' 关键字，无法归类。")
                    
                    count = fur_name_counts.get(base_new_name, 0)
                    fur_name_counts[base_new_name] = count + 1
                    
                    final_name = base_new_name if count == 0 else f"{base_new_name}{count}"
                    
                    if obj.name != final_name:
                        old_name = obj.name
                        obj.name = final_name
                        report["fixed"].append(f"基于源节点结构化修正曲线命名: {old_name} -> {final_name}")

    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES']:
            expected_data_name = obj.name + "Shape"
            if obj.data and obj.data.name != expected_data_name:
                old_name = obj.data.name
                obj.data.name = expected_data_name
                report["fixed"].append(f"数据名同步重命名: {old_name} -> {expected_data_name}")
    
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES', 'EMPTY']:
            loc = obj.location
            rot = obj.rotation_euler
            scl = obj.scale
            
            is_loc_0 = all(abs(v) < 1e-5 for v in loc)
            is_rot_0 = all(abs(v) < 1e-5 for v in rot)
            is_scl_1 = all(abs(v - 1.0) < 1e-5 for v in scl)
            
            if not (is_loc_0 and is_rot_0 and is_scl_1):
                report["manual_fix_needed"].append(f"Transform 未归零: {obj.name}")

    # Final explicit Collection cleanup for Fur groups
    fur_col = bpy.data.collections.get("Fur")
    master_col = bpy.data.collections.get("Collection")
    if fur_col:
        for grp_name in [fur_crv_grp_name, hair_crv_grp_name]:
            grp = bpy.data.objects.get(grp_name)
            if grp:
                # 1. Force link to Fur collection
                try:
                    if grp.name not in fur_col.objects:
                        fur_col.objects.link(grp)
                except Exception:
                    pass
                
                # 2. Force unlink from every other collection in the file
                for col in bpy.data.collections:
                    if col != fur_col and grp.name in col.objects:
                        try:
                            col.objects.unlink(grp)
                        except Exception:
                            pass
                
                # 3. Force unlink from the Scene root if it's there
                try:
                    if grp.name in bpy.context.scene.collection.objects:
                        bpy.context.scene.collection.objects.unlink(grp)
                except Exception:
                    pass
                        
                # 4. Ensure absolutely no parent
                if grp.parent is not None:
                    grp.parent = None
                    
        # CLEANUP: If Fur collection is completely empty, remove it.
        if len(fur_col.objects) == 0 and len(fur_col.children) == 0:
            bpy.data.collections.remove(fur_col)
            report["fixed"].append("清理冗余的空 Fur 集合")
            
    return report

if __name__ == "__main__":
    try:
        blend_file_path = bpy.data.filepath
        if not blend_file_path:
            for arg in sys.argv:
                if arg.endswith('.blend'):
                    blend_file_path = arg
                    break
                    
        report = run_fixer(blend_file_path)
        
        dir_name = os.path.dirname(blend_file_path)
        base_name = os.path.basename(blend_file_path)
        name, ext = os.path.splitext(base_name)
        new_file_path = os.path.join(dir_name, f"{name}_fixed{ext}")
        bpy.ops.wm.save_as_mainfile(filepath=new_file_path)
        report["saved_file"] = new_file_path
        
        out_path = os.environ.get("QC_FIX_OUT_PATH", "qc_fix_out.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
            
        print(f"Fix completed successfully. Report saved to {out_path}")
    except Exception as e:
        print(f"Failed to execute fix: {str(e)}")
        sys.exit(1)
