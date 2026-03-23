# -*- coding: utf-8 -*-
import maya.cmds as cmds
import pymel.core as pm

def run(results, asset_name):
    """
    清理/检测多余 Python 脚本 (script nodes) 和恶意病毒脚本 (leukocyte.antivirus)。
    移植自原生的 script.py。
    """
    issues = []
    
    # 1. 检查非标 script 节点
    nodes = cmds.ls(type='script') or []
    for node in nodes:
        if node not in ['MakeTSM3ControlsMenu', 'sceneConfigurationScriptNode']:
            issues.append("Script Node: {}".format(node))

    # 2. 检查后台 script job (防病毒/防污染)
    try:
        jobs = pm.scriptJob(listJobs=True) or []
        for job in jobs:
            if 'leukocyte.antivirus()' in job:
                issues.append("Malicious ScriptJob: leukocyte.antivirus found")
    except:
        pass

    if issues:
        results.append({
            "check": "extra_scripts",
            "status": "FAIL",
            "issues": ["Found unapproved scripts/jobs: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "extra_scripts",
            "status": "PASS",
            "issues": []
        })