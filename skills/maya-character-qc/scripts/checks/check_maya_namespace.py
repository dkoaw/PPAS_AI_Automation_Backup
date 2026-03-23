# -*- coding: utf-8 -*-
import maya.cmds as cmds
import os

def run(results, asset_name):
    """
    检查场景中是否存在非法的 Namespace。
    """
    issues = []
    namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
    
    for ns in namespaces:
        if ns not in ["UI", "shared"]:
            issues.append(ns)
            
    if issues:
        results.append({
            "check": "maya_namespace",
            "status": "FAIL",
            "issues": ["Illegal Namespace found: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "maya_namespace",
            "status": "PASS",
            "issues": []
        })