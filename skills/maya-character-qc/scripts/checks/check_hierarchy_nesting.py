# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查大纲核心层级是否符合 |Group|Geometry|cache 的强制规范。
    """
    issues = []
    
    # 检查是否存在根节点 Group
    if not cmds.objExists("|Group"):
        issues.append("Missing Root Node: |Group")
    
    # 检查是否存在 cache
    caches = cmds.ls("cache", type="transform", l=True) or []
    if not caches:
        issues.append("Missing Core Node: cache")
    else:
        # 检查是否唯一
        if len(caches) > 1:
            issues.append("Multiple cache nodes found.")
        
        # 检查结构路径是否正确
        cache_path = caches[0]
        if cache_path != "|Group|Geometry|cache":
            issues.append("Invalid cache path. Expected |Group|Geometry|cache, found: " + cache_path)

    if issues:
        results.append({
            "check": "hierarchy_nesting",
            "status": "FAIL",
            "issues": issues
        })
    else:
        results.append({
            "check": "hierarchy_nesting",
            "status": "PASS",
            "issues": []
        })
