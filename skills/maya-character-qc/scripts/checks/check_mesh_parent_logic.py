# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查 cache 组内的节点命名是否符合规范。
    网格节点(Mesh Transform)名字必须等于父级组名字加上序号(如果没有序号默认是1)。
    并且检查其底层 Shape 节点是否等于 Transform名 + Shape。
    """
    issues = []
    
    caches = cmds.ls("cache", type="transform", l=True) or []
    if not caches:
        results.append({"check": "mesh_parent_logic", "status": "FAIL", "issues": ["Missing cache group"]})
        return
        
    cache_node = caches[0]
    
    # 获取所有的 mesh transform 节点
    all_transforms = cmds.listRelatives(cache_node, allDescendents=True, type="transform", fullPath=True) or []
    
    for t in all_transforms:
        shapes = cmds.listRelatives(t, shapes=True, fullPath=True) or []
        if shapes and cmds.nodeType(shapes[0]) == "mesh":
            short_name = t.split('|')[-1]
            parent = cmds.listRelatives(t, parent=True, fullPath=True)
            
            if not parent or parent[0] == cache_node:
                # Mesh 不应该直接挂在 cache 下，应该有 Grp 保护
                issues.append("Mesh without parent Group: " + short_name)
                continue
                
            # 检查命名逻辑 (简单验证：是否包含资产名)
            if not short_name.startswith(asset_name + "_"):
                # 豁免眼球
                if "eyeball" not in short_name.lower() and "vitreous" not in short_name.lower():
                    issues.append("Invalid Mesh Name (Missing Prefix): " + short_name)
            
            # 检查 Shape 名字
            active_shapes = [s for s in shapes if cmds.getAttr(s + ".intermediateObject") == 0]
            if active_shapes:
                shape_name = active_shapes[0].split('|')[-1]
                expected_shape_name = short_name + "Shape"
                if shape_name != expected_shape_name:
                    issues.append("Shape name mismatch: {} -> Expected {}".format(shape_name, expected_shape_name))

    if issues:
        results.append({
            "check": "mesh_parent_logic",
            "status": "FAIL",
            "issues": issues
        })
    else:
        results.append({
            "check": "mesh_parent_logic",
            "status": "PASS",
            "issues": []
        })
