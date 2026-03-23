# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查场景中是否存在未使用的蒙皮影响物(Skin Deformation)。
    """
    issues = []
    
    geometry = 'Geometry'
    if cmds.objExists(geometry):
        meshes = cmds.listRelatives(geometry, ad=True, f=True, type='mesh') or []
        if meshes:
            transforms = cmds.listRelatives(meshes, p=True, f=True) or []
            transforms = list(set(transforms))
            
            for obj in transforms:
                history = cmds.listHistory(obj, pruneDagObjects=True) or []
                skinClusters = cmds.ls(history, type='skinCluster')
                if skinClusters:
                    for sc in skinClusters:
                        # 检查是否有权重为0的影响物
                        influences = cmds.skinCluster(sc, query=True, influence=True) or []
                        weighted_influences = cmds.skinCluster(sc, query=True, weightedInfluence=True) or []
                        
                        unused = set(influences) - set(weighted_influences)
                        if unused:
                            issues.append("{} (Cluster: {})".format(obj.split('|')[-1], sc))
                            
    if issues:
        results.append({
            "check": "rig_unused_skin",
            "status": "FAIL",
            "issues": ["Unused Skin Influences found on: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "rig_unused_skin",
            "status": "PASS",
            "issues": []
        })