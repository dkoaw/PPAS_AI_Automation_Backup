import bpy
import os
import sys
import stat
import subprocess

def disable_all_modifiers(obj):
    """禁用物体的所有修改器显示和渲染"""
    if not hasattr(obj, 'modifiers'):
        return
    for mod in obj.modifiers:
        mod.show_viewport = False
        mod.show_render = False

def run_export_abc():
    blend_file = bpy.data.filepath
    if not blend_file:
        print("Error: No blend file path found.")
        return
        
    dir_path = os.path.dirname(blend_file)
    base_name = os.path.basename(blend_file)
    
    name_clean = os.path.splitext(base_name)[0]
    name_clean = name_clean.replace("_outputabc", "")
    name_clean = name_clean.replace("_fixed", "")
    
    abc_name = name_clean + ".abc"
    abc_path = os.path.join(dir_path, abc_name)
    
    cache_grp = bpy.data.objects.get("cache")
    if not cache_grp:
        print("Error: No 'cache' group found.")
        return

    # 1. 强行显示所有物体，防止导出器因为隐藏而跳过
    # 因为这是在 _outputabc 临时文件中操作，所以直接全局开启，不需要还原
    for obj in bpy.data.objects:
        obj.hide_viewport = False
        obj.hide_set(False)
        obj.hide_render = False

    # 2. 递归收集并选中所有 cache 下的物体
    bpy.ops.object.select_all(action='DESELECT')
    
    export_objects = []
    def collect_hierarchy(parent):
        export_objects.append(parent)
        for child in parent.children:
            collect_hierarchy(child)
            
    collect_hierarchy(cache_grp)
    
    for obj in export_objects:
        obj.select_set(True)
        if obj.type == 'MESH':
            disable_all_modifiers(obj)
            
    # 3. 设置导出参数并执行 Alembic 导出 (Blender 5.0 API)
    try:
        # 解除只读（如果存在）
        if os.path.exists(abc_path):
            cmd = "Set-ItemProperty -Path '{}' -Name IsReadOnly -Value $false".format(abc_path)
            subprocess.call(['powershell.exe', '-NoProfile', '-Command', cmd])

        bpy.ops.wm.alembic_export(
            filepath=abc_path,
            start=1,
            end=1,
            selected=True,
            flatten=False,
            uvs=True,
            normals=True,
            export_custom_properties=True,
            as_background_job=False,
            evaluation_mode='VIEWPORT'
        )
        print(f"Successfully exported ABC to: {abc_path}")
        
        # 4. 属性级软锁定
        if os.path.exists(abc_path):
            cmd = "Set-ItemProperty -Path '{}' -Name IsReadOnly -Value $true".format(abc_path)
            subprocess.call(['powershell.exe', '-NoProfile', '-Command', cmd])
            print(f"Set ABC file to Read-Only (PS): {abc_path}")
            
    except Exception as e:
        print(f"Export failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_export_abc()
