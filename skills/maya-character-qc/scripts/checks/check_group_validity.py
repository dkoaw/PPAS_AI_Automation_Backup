# -*- coding: utf-8 -*-
import maya.cmds as cmds
import json
import os

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
RULES_JSON = os.path.join(SKILLS_DIR, "blender-fixer-atoms", "scripts", "fixer_rules.json")

def load_rules():
    try:
        with open(RULES_JSON, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}

def run(results, asset_name):
    """
    检查特殊保护组 (如 hiddenMesh_Grp, staticCurve_Grp) 的合法性。
    比如，除了这些合法白名单组之外，不应该有其他非标准命名的组。
    """
    issues = []
    
    cache_grp = '|Group|Geometry|cache'
    if not cmds.objExists(cache_grp):
        results.append({"check": "group_validity", "status": "PASS", "issues": []})
        return
        
    rules = load_rules()
    suffix = rules.get("group_processor", {}).get("default_suffix", "_Grp")
    
    # Check all groups directly under cache
    children = cmds.listRelatives(cache_grp, children=True, type="transform", fullPath=True) or []
    for child in children:
        short_name = child.split('|')[-1]
        shapes = cmds.listRelatives(child, shapes=True)
        if not shapes:
            # It's a group. Check if it adheres to AssetName_XXX_Grp format
            if not short_name.startswith(asset_name + "_") or not short_name.endswith(suffix):
                issues.append("Invalid Group Naming: " + short_name)

    if issues:
        results.append({
            "check": "group_validity",
            "status": "FAIL",
            "issues": issues
        })
    else:
        results.append({
            "check": "group_validity",
            "status": "PASS",
            "issues": []
        })