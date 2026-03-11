import bpy
import json
import sys
import os

def build_dag_path(obj):
    """构建类似 |Group|cache|... 的绝对路径"""
    path = []
    current = obj
    while current:
        path.append(current.name)
        current = current.parent
    path.reverse()
    return "|" + "|".join(path)

def extract_mesh_info():
    report = {}
    
    # 获取 cache 组
    cache_grp = bpy.data.objects.get("cache")
    if not cache_grp:
        print("Error: No 'cache' group found.")
        return None
        
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # 检查是否在 cache 下
            is_under_cache = False
            p = obj.parent
            while p:
                if p == cache_grp:
                    is_under_cache = True
                    break
                p = p.parent
                
            if is_under_cache:
                # 构建完整的 DAG 路径，包含数据块名称 (Shape)
                mesh_data = obj.data
                dag_path = build_dag_path(obj) + "|" + mesh_data.name
                
                # 提取顶点数据
                # 提示：v.co 是局部空间坐标。根据样例，通常拓扑对比使用的是局部空间数据。
                verts = []
                for v in mesh_data.vertices:
                    verts.extend([round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)])
                
                report[dag_path] = {
                    "vertices": len(mesh_data.vertices),
                    "vert_positions": verts
                }
                
    return report

if __name__ == "__main__":
    try:
        # 获取输出路径
        out_path = os.environ.get("EXTRACT_INFO_OUT", "asset_structure_info.json")
        
        data = extract_mesh_info()
        if data:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Asset core structure info exported to {out_path}")
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Failed to extract info: {str(e)}")
        sys.exit(1)
