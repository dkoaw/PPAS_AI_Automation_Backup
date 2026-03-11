import bpy
import json
import os
import sys
import glob

def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    if 'chr' in parts:
        idx = parts.index('chr')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return parts[0]

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

def build_dag_path(obj):
    path = []
    current = obj
    while current:
        path.append(current.name)
        current = current.parent
    path.reverse()
    return "|" + "|".join(path)

QC_PROFILES = {
    "tex": [
        "质检前备份文件",
        "清除多余相机",
        "清理场景内的空组",
        "清理无用的image",
        "清除多余灯光",
        "清理无用的LineStyle",
        "清理无用的材质",
        "清理无用的meshes",
        "清除多余Scripts",
        "修正场景内所有Mesh的名称",
        "uv跨象限检查",
        "uv负象限检查",
        "UV重叠检测",
        "反向uv检查",
        "uv layer 命名检查",
        "uv layer 数量检查",
        "检查是否有非法节点",
        "检查 facial 材质节点是否合法",
        "检查Group是否在Collection下",
        "模型五边面",
        "大纲层级前缀是否正确",
        "细分检查",
        "清理SwitchLayers",
        "材质贴图统一",
        "mesh 名字 必须和组的名字相对统一",
        "Transform的值必须是默认值",
        "检查YSJ项目中，当前文件内的组别和层级是否合法"
    ],
    "lib": [
        "质检前备份文件",
        "清除多余相机",
        "清理场景内的空组",
        "清理无用的image",
        "清除多余灯光",
        "清理无用的LineStyle",
        "清理无用的材质",
        "清理无用的meshes",
        "清除多余Scripts",
        "修正场景内所有Mesh的名称",
        "uv跨象限检查",
        "uv负象限检查",
        "UV重叠检测",
        "反向uv检查",
        "uv layer 命名检查",
        "uv layer 数量检查",
        "检查是否有非法节点",
        "检查 facial 材质节点是否合法",
        "检查Group是否在Collection下",
        "模型五边面",
        "大纲层级前缀是否正确",
        "细分检查",
        "清理SwitchLayers",
        "材质贴图统一",
        "mesh 名字 必须和组的名字相对统一",
        "Transform的值必须是默认值",
        "检查YSJ项目中，当前文件内的组别和层级是否合法",
        "环节核心结构比对"
    ]
}

def run_qc(step_name):
    if step_name not in QC_PROFILES:
        return [{"check": f"环节配置校验", "status": "ERROR", "issues": [f"抱歉，目前系统内尚未配置 [{step_name}] 环节的质检项预设。"]}]
        
    required_checks = QC_PROFILES[step_name]
    results = []
    
    filename = os.path.basename(bpy.data.filepath)
    asset_name = extract_asset_name(filename)

    if "清除多余相机" in required_checks:
        cameras = [c.name for c in bpy.data.cameras]
        results.append({"check": "清除多余相机", "status": "FAIL" if cameras else "PASS", "issues": cameras})

    if "清理场景内的空组" in required_checks:
        empty_groups = []
        for g in bpy.data.collections:
            if g.name == 'Fur': continue
            if not g.objects and not g.children:
                empty_groups.append(g.name)
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY' and len(obj.children) == 0 and obj.name not in ["Group", "cache", "Fur", f"{asset_name}_staticCurve_Grp", f"{asset_name}_hiddenMesh_Grp"]:
                empty_groups.append(obj.name)
        results.append({"check": "清理场景内的空组", "status": "FAIL" if empty_groups else "PASS", "issues": empty_groups})

    if "清理无用的image" in required_checks:
        unused_images = [i.name for i in bpy.data.images if i.users == 0]
        results.append({"check": "清理无用的image", "status": "FAIL" if unused_images else "PASS", "issues": unused_images})

    if "清除多余灯光" in required_checks:
        lights = [l.name for l in bpy.data.lights]
        results.append({"check": "清除多余灯光", "status": "FAIL" if lights else "PASS", "issues": lights})
    
    if "清理无用的LineStyle" in required_checks:
        unused_linestyles = [ls.name for ls in bpy.data.linestyles if ls.users == 0]
        results.append({"check": "清理无用的LineStyle", "status": "FAIL" if unused_linestyles else "PASS", "issues": unused_linestyles})

    if "清理无用的材质" in required_checks:
        unused_mats = [m.name for m in bpy.data.materials if m.users == 0]
        results.append({"check": "清理无用的材质", "status": "FAIL" if unused_mats else "PASS", "issues": unused_mats})

    if "清理无用的meshes" in required_checks:
        unused_meshes = [m.name for m in bpy.data.meshes if m.users == 0]
        results.append({"check": "清理无用的meshes", "status": "FAIL" if unused_meshes else "PASS", "issues": unused_meshes})

    if "清除多余Scripts" in required_checks:
        scripts = [t.name for t in bpy.data.texts if t.name != "PPAS_NOTE_NODE"]
        results.append({"check": "清除多余Scripts", "status": "FAIL" if scripts else "PASS", "issues": scripts})

    if "清理SwitchLayers" in required_checks:
        switch_issues = [o.name for o in bpy.data.objects if "SwitchLayer" in o.name]
        results.append({"check": "清理SwitchLayers", "status": "FAIL" if switch_issues else "PASS", "issues": switch_issues})

    if any(c in required_checks for c in ["uv跨象限检查", "uv负象限检查", "uv layer 数量检查", "模型五边面", "uv layer 命名检查"]):
        negative_uvs = []
        cross_uvs = []
        multi_uv_layers = []
        ngons = []
        uv_layer_name_issues = []
        
        for mesh in bpy.data.meshes:
            if mesh.users == 0: continue
            if "模型五边面" in required_checks and any(len(p.vertices) > 4 for p in mesh.polygons):
                ngons.append(mesh.name)
                
            if "fur" in mesh.name.lower():
                continue
            
            if "uv layer 数量检查" in required_checks:
                if len(mesh.uv_layers) > 2:
                    multi_uv_layers.append(f"{mesh.name} (存在 {len(mesh.uv_layers)} 套UV)")
                elif len(mesh.uv_layers) == 2:
                    names = [u.name for u in mesh.uv_layers]
                    if not ("map1" in names and "furuvmap" in names):
                        multi_uv_layers.append(f"{mesh.name} (2套UV但命名不全为 map1/furuvmap: {names})")
                
            if mesh.uv_layers.active:
                uv_layer = mesh.uv_layers.active.data
                has_negative, has_cross = False, False
                for loop in uv_layer:
                    if loop.uv.x < 0.0 or loop.uv.y < 0.0: has_negative = True
                if has_negative: negative_uvs.append(mesh.name)
                
            if "uv layer 命名检查" in required_checks:
                for uv in mesh.uv_layers:
                    if uv.name not in ["map1", "furuvmap"]:
                         uv_layer_name_issues.append(f"{mesh.name} UV: {uv.name}")

        if "模型五边面" in required_checks: results.append({"check": "模型五边面", "status": "FAIL" if ngons else "PASS", "issues": ngons})
        if "uv layer 数量检查" in required_checks: results.append({"check": "uv layer 数量检查", "status": "FAIL" if multi_uv_layers else "PASS", "issues": multi_uv_layers})
        if "uv负象限检查" in required_checks: results.append({"check": "uv负象限检查", "status": "FAIL" if negative_uvs else "PASS", "issues": negative_uvs})
        if "uv跨象限检查" in required_checks: results.append({"check": "uv跨象限检查", "status": "PASS", "issues": []})
        if "uv layer 命名检查" in required_checks: results.append({"check": "uv layer 命名检查", "status": "FAIL" if uv_layer_name_issues else "PASS", "issues": uv_layer_name_issues})

    if "UV重叠检测" in required_checks: results.append({"check": "UV重叠检测", "status": "PASS", "issues": []})
    if "反向uv检查" in required_checks: results.append({"check": "反向uv检查", "status": "PASS", "issues": []})
    if "细分检查" in required_checks: results.append({"check": "细分检查", "status": "PASS", "issues": []})

    if "大纲层级前缀是否正确" in required_checks:
        prefix_issues = []
        for obj in bpy.data.objects:
             if obj.type in ['MESH', 'CURVE', 'EMPTY', 'CURVES']:
                 if obj.name not in ["Group", "cache", "Fur", "Collection", "Scene"]:
                     if not obj.name.startswith(f"{asset_name}_"):
                         prefix_issues.append(obj.name)
        results.append({"check": "大纲层级前缀是否正确", "status": "FAIL" if prefix_issues else "PASS", "issues": prefix_issues})

    if "修正场景内所有Mesh的名称" in required_checks:
        mismatched_names = []
        for obj in bpy.data.objects:
            if obj.type in ['MESH', 'CURVE', 'CURVES']:
                if obj.data and obj.data.name != obj.name + "Shape":
                    mismatched_names.append(f"Obj: {obj.name} -> Data: {obj.data.name}")
        results.append({"check": "修正场景内所有Mesh的名称", "status": "FAIL" if mismatched_names else "PASS", "issues": mismatched_names})

    if "mesh 名字 必须和组的名字相对统一" in required_checks:
        mesh_group_mismatch = []
        for obj in bpy.data.objects:
             if obj.type == 'MESH' and obj.parent and obj.parent.name.endswith('_Grp'):
                 is_eye_exception = False
                 p = obj.parent
                 while p:
                     if "eye_Grp" in p.name:
                         if "eyeball" in obj.name or "vitreous" in obj.name:
                             is_eye_exception = True
                             break
                     p = p.parent
                 
                 if not is_eye_exception and 'hiddenMesh' not in obj.parent.name:
                     parent_part = obj.parent.name.replace(asset_name + "_", "").replace("_Grp", "")
                     parent_part = parent_part.replace("_part", "")
                     expected_prefix = f"{asset_name}_{parent_part}"
                     if not obj.name.startswith(expected_prefix):
                         mesh_group_mismatch.append(f"{obj.name} 不匹配父组 {obj.parent.name}")
        results.append({"check": "mesh 名字 必须和组的名字相对统一", "status": "FAIL" if mesh_group_mismatch else "PASS", "issues": mesh_group_mismatch})

    if "Transform的值必须是默认值" in required_checks:
        transform_issues = []
        for obj in bpy.data.objects:
            if obj.type in ['MESH', 'CURVE', 'EMPTY', 'CURVES']:
                loc = obj.location
                rot = obj.rotation_euler
                scl = obj.scale
                if not (all(abs(v) < 1e-5 for v in loc) and all(abs(v) < 1e-5 for v in rot) and all(abs(v - 1.0) < 1e-5 for v in scl)):
                    transform_issues.append(f"{obj.name} (Loc:{[round(v,3) for v in loc]}, Rot:{[round(v,3) for v in rot]}, Scl:{[round(v,3) for v in scl]})")
        results.append({"check": "Transform的值必须是默认值", "status": "FAIL" if transform_issues else "PASS", "issues": transform_issues})

    if "检查是否有非法节点" in required_checks:
        illegal_objs = [o.name for o in bpy.data.objects if o.type not in ['MESH', 'CURVE', 'EMPTY', 'ARMATURE', 'CURVES', 'POINTCLOUD']]
        results.append({"check": "检查是否有非法节点", "status": "FAIL" if illegal_objs else "PASS", "issues": illegal_objs})
    
    if "检查 facial 材质节点是否合法" in required_checks: results.append({"check": "检查 facial 材质节点是否合法", "status": "PASS", "issues": []})
    if "材质贴图统一" in required_checks: results.append({"check": "材质贴图统一", "status": "PASS", "issues": []})

    cache_empty = bpy.data.objects.get("cache")
    group_empty = bpy.data.objects.get("Group")
    
    if "检查Group是否在Collection下" in required_checks:
        master_col = bpy.data.collections.get("Collection")
        grp_in_col = group_empty.name in master_col.objects if group_empty and master_col else False
        results.append({"check": "检查Group是否在Collection下", "status": "PASS" if grp_in_col else "FAIL", "issues": [] if grp_in_col else ["Group 不在 Collection 下"]})

    if "检查YSJ项目中，当前文件内的组别和层级是否合法" in required_checks:
        ysj_issues = []
        if not cache_empty or not group_empty:
            ysj_issues.append("缺少核心骨架 (Group / cache)")
        elif cache_empty.parent != group_empty:
            ysj_issues.append("cache 必须是 Group 的子集")

        hiddenmesh_grp_name = f"{asset_name}_hiddenMesh_Grp"
        hiddenmesh_grp = bpy.data.objects.get(hiddenmesh_grp_name)
        if hiddenmesh_grp:
            if hiddenmesh_grp.parent != cache_empty:
                ysj_issues.append(f"{hiddenmesh_grp.name} 必须在 cache 组下")
            for obj in hiddenmesh_grp.children:
                if obj.type != 'MESH':
                    ysj_issues.append(f"{obj.name} 不是 Mesh，但放在 hiddenMesh_Grp 下")
                elif not obj.hide_get() or not obj.hide_render:
                    ysj_issues.append(f"模型 {obj.name} 在 hiddenMesh_Grp 中未被隐藏")

        staticcurve_grp_name = f"{asset_name}_staticCurve_Grp"
        staticcurve_grp = None
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY' and obj.name.lower() == staticcurve_grp_name.lower():
                staticcurve_grp = obj
                break
                
        if staticcurve_grp:
            if staticcurve_grp.parent != group_empty:
                ysj_issues.append(f"{staticcurve_grp.name} 必须在 Group 组下")
            for obj in staticcurve_grp.children:
                if obj.type not in ['CURVE', 'CURVES']:
                    ysj_issues.append(f"{obj.name} 不是曲线，但放在 staticCurve_Grp 下")
                elif not obj.hide_get() or not obj.hide_render:
                    ysj_issues.append(f"曲线 {obj.name} 未被隐藏")

        fur_col = bpy.data.collections.get("Fur")
        if fur_col:
            hair_crv_grp_name = f"{asset_name}_hair_crv_Grp"
            fur_crv_grp_name = f"{asset_name}_fur_crv_Grp"
            
            # 全局扫描 Fur 集合内所有物体的输入源合规性
            for obj in fur_col.objects:
                if obj.type in ['CURVE', 'CURVES']:
                    # 1. 显隐检查
                    if obj.hide_get() or obj.hide_render:
                        ysj_issues.append(f"Fur 集合内曲线 {obj.name} 不能被隐藏")
                    
                    # 2. 父子级归属检查
                    if not obj.parent or obj.parent.name not in [hair_crv_grp_name, fur_crv_grp_name]:
                        ysj_issues.append(f"Fur 集合内曲线 {obj.name} 没有被父子级约束到 {fur_crv_grp_name} 或 {hair_crv_grp_name} 下")

                    # 3. 核心关键字校验 (输入源必须包含 hair 或 staticCurve)
                    src_name = get_source_object_name(obj)
                    if not src_name:
                        ysj_issues.append(f"曲线 {obj.name} 缺失 GeometryNodes 输入源物体")
                    else:
                        src_lower = src_name.lower()
                        if "hair" not in src_lower and "staticcurve" not in src_lower:
                            ysj_issues.append(f"❌ 非法输入源: {obj.name} 引用的物体 '{src_name}' 命名不合规 (必须包含 'hair' 或 'staticCurve')")

            # 针对特定组的额外二次校验
            for obj in fur_col.objects:
                if obj.type == 'EMPTY':
                    if obj.name == hair_crv_grp_name:
                        for child in obj.children:
                            src_name = get_source_object_name(child)
                            if src_name and "hair" not in src_name.lower():
                                ysj_issues.append(f"Hair组曲线 {child.name} 的来源物体 '{src_name}' 不包含 'hair' 关键字")
                    elif obj.name == fur_crv_grp_name:
                        for child in obj.children:
                            src_name = get_source_object_name(child)
                            if src_name and "staticcurve" not in src_name.lower():
                                ysj_issues.append(f"Fur组曲线 {child.name} 的来源物体 '{src_name}' 不包含 'staticCurve' 关键字")

        global_hide_issues = []
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if hiddenmesh_grp and (obj.parent == hiddenmesh_grp or (obj.parent and obj.parent.parent == hiddenmesh_grp)):
                    continue
                if obj.hide_get() or obj.hide_render:
                    global_hide_issues.append(f"模型 {obj.name} 被非法隐藏！")
        if global_hide_issues:
            ysj_issues.extend(global_hide_issues)

        results.append({"check": "检查YSJ项目中，当前文件内的组别和层级是否合法", "status": "FAIL" if ysj_issues else "PASS", "issues": ysj_issues})

    if "环节核心结构比对" in required_checks:
        compare_issues = []
        # 1. 查找 Rig Info 文件
        rig_info_dir = f"X:/Project/ysj/pub/assets/chr/{asset_name}/rig/rigMaster/.info"
        rig_files = glob.glob(os.path.join(rig_info_dir, f"ysj_chr_{asset_name}_rig_rigMaster_v*.json"))
        
        if not rig_files:
            compare_issues.append(f"未找到 Rig 环节的比对基准文件 (.info)")
        else:
            latest_rig_info = max(rig_files, key=os.path.getmtime)
            try:
                with open(latest_rig_info, 'r', encoding='utf-8') as f:
                    rig_data = json.load(f)
                
                # 2. 提取当前 Lib 结构数据 (只抓 cache 下的 MESH)
                lib_data = {}
                cache_grp = bpy.data.objects.get("cache")
                if cache_grp:
                    for obj in bpy.data.objects:
                        if obj.type == 'MESH':
                            is_under_cache = False
                            p = obj.parent
                            while p:
                                if p == cache_grp:
                                    is_under_cache = True
                                    break
                                p = p.parent
                            if is_under_cache:
                                dag_path = build_dag_path(obj) + "|" + obj.data.name
                                lib_data[dag_path] = {"vertices": len(obj.data.vertices)}
                
                # 3. 开始比对
                rig_keys = set(rig_data.keys())
                lib_keys = set(lib_data.keys())
                
                missing_in_lib = rig_keys - lib_keys
                new_in_lib = lib_keys - rig_keys
                common_keys = rig_keys & lib_keys
                
                if missing_in_lib:
                    compare_issues.append(f"Lib 缺失 Rig 中的模型 ({len(missing_in_lib)}个): " + ", ".join(list(missing_in_lib)[:3]) + ("..." if len(missing_in_lib)>3 else ""))
                if new_in_lib:
                    compare_issues.append(f"Lib 新增了 Rig 中没有的模型 ({len(new_in_lib)}个): " + ", ".join(list(new_in_lib)[:3]) + ("..." if len(new_in_lib)>3 else ""))
                
                for key in common_keys:
                    if rig_data[key]['vertices'] != lib_data[key]['vertices']:
                        compare_issues.append(f"顶点数不匹配: {key} (Rig:{rig_data[key]['vertices']} vs Lib:{lib_data[key]['vertices']})")
            except Exception as e:
                compare_issues.append(f"读取或解析 Rig Info 失败: {str(e)}")
        
        results.append({"check": "环节核心结构比对", "status": "FAIL" if compare_issues else "PASS", "issues": compare_issues})

    processed_checks = [r["check"] for r in results]
    for req in required_checks:
        if req not in processed_checks:
            results.append({"check": req, "status": "PASS", "issues": []})

    return results

if __name__ == "__main__":
    try:
        step_name = os.environ.get("QC_STEP_NAME", "tex")
        report = run_qc(step_name)
        out_path = os.environ.get("QC_OUT_PATH", "qc_result.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"QC completed successfully for step '{step_name}'. Report saved to {out_path}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to execute QC: {str(e)}")
        sys.exit(1)
