# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查缓存组内是否存在多余的、无子节点的空组(Empty Groups)。
    """
    issues = []
    
    cache_grp = '|Group|Geometry|cache'
    if not cmds.objExists(cache_grp):
        results.append({"check": "empty_groups", "status": "PASS", "issues": []})
        return
        
    all_transforms = cmds.listRelatives(cache_grp, allDescendents=True, type="transform", fullPath=True) or []
    
    for t in all_transforms:
        shapes = cmds.listRelatives(t, shapes=True)
        children = cmds.listRelatives(t, children=True, type="transform")
        if not shapes and not children:
            issues.append(t.split('|')[-1])

    if issues:
        results.append({
            "check": "empty_groups",
            "status": "FAIL",
            "issues": ["Found Empty Groups: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "empty_groups",
            "status": "PASS",
            "issues": []
        })