# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查场景中是否存在多余的摄像机 (排除默认四视图相机)。
    """
    issues = []
    
    # 默认的系统相机
    default_cameras = ['frontShape', 'perspShape', 'sideShape', 'topShape']
    
    # 获取所有的相机 Shape 节点
    all_cameras = cmds.ls(type='camera') or []
    
    for cam in all_cameras:
        if cam not in default_cameras:
            # 获取其 Transform 节点名
            trans = cmds.listRelatives(cam, parent=True)
            cam_name = trans[0] if trans else cam
            issues.append(cam_name)

    if issues:
        results.append({
            "check": "cameras",
            "status": "FAIL",
            "issues": ["Found Extra Cameras: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "cameras",
            "status": "PASS",
            "issues": []
        })
