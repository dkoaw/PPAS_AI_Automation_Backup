# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查大纲中所有网格物体 (Mesh) 的前缀是否包含资产名称。
    """
    issues = []
    
    cache_grp = '|Group|Geometry|cache'
    if cmds.objExists(cache_grp):
        meshes = cmds.listRelatives(cache_grp, ad=True, type='mesh', fullPath=True) or []
        transforms = list(set([cmds.listRelatives(m, parent=True, fullPath=True)[0] for m in meshes]))
        
        for t in transforms:
            short_name = t.split('|')[-1]
            if not short_name.startswith(asset_name + "_"):
                issues.append(short_name)
                
    if issues:
        results.append({
            "check": "asset_prefix",
            "status": "FAIL",
            "issues": ["Invalid Prefix (Expected {}_): ".format(asset_name) + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "asset_prefix",
            "status": "PASS",
            "issues": []
        })