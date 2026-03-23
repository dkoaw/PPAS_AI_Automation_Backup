# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检测场景中非标非法节点 (Unknown nodes/plugins)。
    """
    issues = []
    
    # Check for unknown nodes
    unknown_nodes = cmds.ls(type='unknown') or []
    if unknown_nodes:
        issues.append("Unknown Nodes: " + str(len(unknown_nodes)))
        
    # Check for unknown plugins
    unknown_plugins = cmds.unknownPlugin(query=True, list=True) or []
    if unknown_plugins:
        issues.append("Unknown Plugins: " + ", ".join(unknown_plugins))

    if issues:
        results.append({
            "check": "illegal_nodes",
            "status": "FAIL",
            "issues": issues
        })
    else:
        results.append({
            "check": "illegal_nodes",
            "status": "PASS",
            "issues": []
        })