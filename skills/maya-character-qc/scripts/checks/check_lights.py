# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    清除多余灯光 (检查是否有除了默认灯光外的光源)。
    """
    issues = []
    
    # 检查默认的 defaultLightSet 里是否有灯光
    if cmds.objExists('defaultLightSet'):
        lights = cmds.sets('defaultLightSet', q=True) or []
        for light in lights:
            issues.append(light)
            
    # 更严谨：检查所有非默认的灯光节点
    all_lights = cmds.ls(type=['light', 'aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'aiPhotometricLight', 'aiLightPortal']) or []
    for light in all_lights:
        trans = cmds.listRelatives(light, parent=True)
        name = trans[0] if trans else light
        if name not in issues:
            issues.append(name)

    if issues:
        results.append({
            "check": "lights",
            "status": "FAIL",
            "issues": ["Found Extra Lights: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "lights",
            "status": "PASS",
            "issues": []
        })