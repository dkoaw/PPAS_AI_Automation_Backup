# -*- coding: utf-8 -*-
import maya.cmds as cmds

def run(results, asset_name):
    """
    检查缓存组内是否存在多余的、无用的材质球 (Useless Shader)。
    如果检查到有材质球，但它并没有赋予给任何缓存组内的网格，则报警。
    """
    issues = []
    
    # 获取所有的 shading engines (排除了默认的 initialShadingGroup 和 initialParticleSE)
    shading_engines = cmds.ls(type='shadingEngine') or []
    default_ses = ['initialShadingGroup', 'initialParticleSE']
    
    for se in shading_engines:
        if se in default_ses:
            continue
            
        # 获取连接到这个 shading engine 的所有 mesh
        connected_meshes = cmds.sets(se, q=True) or []
        if not connected_meshes:
            issues.append(se)

    if issues:
        results.append({
            "check": "unused_materials",
            "status": "FAIL",
            "issues": ["Found Useless Shaders: " + ", ".join(issues)]
        })
    else:
        results.append({
            "check": "unused_materials",
            "status": "PASS",
            "issues": []
        })