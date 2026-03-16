# -*- coding: utf-8 -*-
import maya.cmds as cmds
import maya.api.OpenMaya as om
import json
import os
import re

def get_mesh_info():
    report = {}
    
    # 查找所有的 cache 组 (兼容带 Namespace 或多层级的情况)
    all_caches = cmds.ls('*:cache', long=True) + cmds.ls('cache', long=True)
    cache_grp = None
    for c in all_caches:
        if 'Group' in c:  # 只要路径里包含 Group 即认为是核心资产节点
            cache_grp = c
            break
            
    if not cache_grp:
        print("Error: No 'cache' group found under a 'Group' hierarchy in Maya scene.")
        print("Available caches:", all_caches)
        return report
    
    # 递归获取 cache 下所有的 mesh shape
    meshes = cmds.listRelatives(cache_grp, allDescendents=True, type='mesh', fullPath=True) or []
    
    for mesh in meshes:
        # [核心过滤]: 坚决跳过中间节点 (Intermediate Objects) 
        # 绑定文件中通常包含被蒙皮变形器隐藏的 Orig 节点，这些不能参与比对
        if cmds.getAttr(mesh + ".intermediateObject"):
            continue
            
        # [核心清洗]: 清理命名空间和中间杂项层级，使其与 Blender 纯净路径对齐
        # 例如: "|rig_v01:Group|Geometry|rig_v01:cache|..." -> "|Group|cache|..."
        dag_path_clean = re.sub(r'\|[^\|:]+:', '|', mesh)
        dag_path_clean = re.sub(r'\|Group.*?\|cache\|', '|Group|cache|', dag_path_clean)
        
        # 提取顶点坐标
        sel = om.MSelectionList()
        sel.add(mesh)
        dag_path_obj = sel.getDagPath(0)
        
        mesh_fn = om.MFnMesh(dag_path_obj)
        
        # 读取世界空间坐标 (World Space)
        # 这确保了无论绑定组层级怎么位移，最终拿到的都是模型在世界中的绝对位置
        # Maya 的单位默认是 cm，Y轴向上，这与 Blender 转换后的系统一致
        points = mesh_fn.getPoints(om.MSpace.kWorld)
        
        verts = []
        for p in points:
            verts.extend([round(p.x, 6), round(p.y, 6), round(p.z, 6)])
            
        report[dag_path_clean] = {
            "vertices": len(points),
            "vert_positions": verts
        }
        
    return report

def main():
    # 默认输出逻辑 (遵循绑定管线规范)
    current_file = cmds.file(q=True, sceneName=True)
    if current_file:
        dir_path = os.path.dirname(current_file)
        base_name = os.path.splitext(os.path.basename(current_file))[0]
        
        # 强制将输出指向 .info 隐藏目录
        info_dir = os.path.join(dir_path, ".info")
        if not os.path.exists(info_dir):
            os.makedirs(info_dir)
            
        # 命名与 Maya 原文件严格对齐 (例如 xxx_v001.json)
        out_path = os.path.join(info_dir, base_name + ".json")
    else:
        out_path = "maya_structure_info.json"
        
    # 允许环境变量覆盖 (用于自动化流水线测试)
    out_path = os.environ.get("MAYA_OUT_JSON", out_path)
            
    print("Extracting mesh info (Fast OpenMaya Mode)...")
    data = get_mesh_info()
    
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print("Maya structure info successfully exported to: " + out_path)

if __name__ == "__main__":
    # 如果是在 Maya UI 中运行，可以直接调用
    main()
