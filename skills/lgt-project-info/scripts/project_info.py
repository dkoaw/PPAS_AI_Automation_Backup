import bpy
import os

def get_project_from_path():
    filepath = bpy.data.filepath
    if not filepath: return "未保存"
    norm_path = os.path.normpath(filepath); parts = norm_path.split(os.sep); project_idx = -1
    for i, part in enumerate(parts):
        if part.lower() == "project": project_idx = i; break
    if project_idx != -1 and project_idx + 1 < len(parts): return parts[project_idx + 1]
    return "非管线路径"

def update_project_info(scene):
    if not scene: return
    scene.ppas_project_name = get_project_from_path()

class PPAS_OT_RefreshProject(bpy.types.Operator):
    bl_idname = "ppas.refresh_project_info"; bl_label = "刷新"
    def execute(self, ctx): update_project_info(ctx.scene); return {'FINISHED'}

classes = (PPAS_OT_RefreshProject,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
