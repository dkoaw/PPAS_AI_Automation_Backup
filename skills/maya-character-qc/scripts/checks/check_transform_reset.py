# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查 cache 组内的 Transform 节点是否有未归零的位移或旋转。
    """
    issues = []
    
    cache_grp = '|Group|Geometry|cache'
    if not cmds.objExists(cache_grp):
        results.append({"check": "transform_reset", "status": "PASS", "issues": []})
        return
        
    transforms = cmds.listRelatives(cache_grp, allDescendents=True, type="transform", fullPath=True) or []
    
    for obj in transforms:
        short_name = obj.split('|')[-1]
        
        # Check translate
        t = cmds.xform(obj, query=True, translation=True, objectSpace=True)
        if any(abs(v) > 1e-5 for v in t):
            issues.append("{} (Translate NOT 0)".format(short_name))
            continue
            
        # Check rotate
        r = cmds.xform(obj, query=True, rotation=True, objectSpace=True)
        if any(abs(v) > 1e-5 for v in r):
            issues.append("{} (Rotate NOT 0)".format(short_name))
            
    if issues:
        results.append({
            "check": "transform_reset",
            "status": "FAIL",
            "issues": issues
        })
    else:
        results.append({
            "check": "transform_reset",
            "status": "PASS",
            "issues": []
        })
