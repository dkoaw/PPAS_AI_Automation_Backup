# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查缓存组内是否存在多余的中间态(Orig) Shape 节点。
    移植自原生的 fix_orig_shape.py 逻辑的检查部分。
    """
    issues = []
    
    # 获取缓存组下的所有网格
    cache_grp = '|Group|Geometry|cache'
    if not cmds.objExists(cache_grp):
        # 缓存组不存在的问题交给 hierarchy_nesting 去报，这里不重复报
        results.append({"check": "rig_fix_orig_shape", "status": "PASS", "issues": []})
        return

    meshes = cmds.ls(cache_grp, dag=True, type='mesh', long=True) or []
    mesh_dict = {}
    for m in meshes:
        trans = cmds.listRelatives(m, parent=True, fullPath=True)[0]
        mesh_dict.setdefault(trans, []).append(m)

    for transform_name, shapes in mesh_dict.items():
        not_intermediate_shapes = [s for s in shapes if cmds.getAttr(s + ".intermediateObject") == 0]
        short_trans_name = transform_name.split('|')[-1]
        
        if not not_intermediate_shapes or len(not_intermediate_shapes) >= 2:
            issues.append(short_trans_name + " (Missing or Multiple Active Shapes)")
            continue

        tweaks = cmds.listConnections(not_intermediate_shapes[0] + '.tweakLocation') or []
        if not tweaks:
            # 如果存在多余的 intermediate 但是没有 tweak 连接
            if len(shapes) > 1:
                issues.append(short_trans_name + " (Has Unused Orig Shapes)")
            continue

        orig_shapes = cmds.listConnections(tweaks[0] + '.input[0].inputGeometry', d=False, s=True, p=True) or []
        if not orig_shapes:
            issues.append(short_trans_name + " (Tweak node has no Orig Shape connected)")
        elif len(orig_shapes) == 1:
            now_orig = orig_shapes[0].split('.')[0]
            for d_node in shapes:
                if d_node not in [now_orig, not_intermediate_shapes[0]]:
                    issues.append(short_trans_name + " (Found Unused Orig Shape: {})".format(d_node.split('|')[-1]))
        else:
            issues.append(short_trans_name + " (Connected to Multiple Orig Shapes)")

    if issues:
        results.append({
            "check": "rig_fix_orig_shape",
            "status": "FAIL",
            "issues": issues
        })
    else:
        results.append({
            "check": "rig_fix_orig_shape",
            "status": "PASS",
            "issues": []
        })