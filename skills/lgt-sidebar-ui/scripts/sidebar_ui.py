import bpy
import os
import sys
import importlib
from bpy.app.handlers import persistent

try:
    from PySide6 import QtWidgets
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False

class PPAS_PT_Lighting_Main(bpy.types.Panel):
    bl_label = "PPAS 管线工具 V14.7"
    bl_idname = "PPAS_PT_Lighting_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PPAS Lgt'
    
    def draw(self, context):
        l = self.layout; s = context.scene
        b = l.box(); r = b.row(); r.alignment='CENTER'
        p = getattr(s, "ppas_project_name", "")
        if p in ["未保存","非管线路径"]: r.alert=True
        r.label(text=f"工程: {p}", icon='WORLD_DATA')
        row = b.row(align=True); row.operator("ppas.refresh_project_info", text="刷新状态", icon='FILE_REFRESH')
        if HAS_PYSIDE: row.operator("ppas.audit_textures", text="贴图审计", icon='GRAPH')
        
        l.separator(); bq = l.box(); bq.label(text="精度优化 (Texture)", icon='IMAGE_DATA')
        cam = context.scene.camera
        if cam: bq.label(text=f"焦距: {cam.data.lens:.1f}mm (视觉补偿)", icon='VIEW_CAMERA')
        bq.label(text="自动 (Auto):"); bq.operator("ppas.auto_tex_res", text="按视觉距离自动优化")
        bq.separator(); bq.label(text="手动 (Manual):"); r = bq.row(align=True)
        r.operator("ppas.manual_tex_res", text="1k").resolution='1k'
        r.operator("ppas.manual_tex_res", text="2k").resolution='2k'
        r.operator("ppas.manual_tex_res", text="4k").resolution='4k'
        
        l.separator(); bg = l.box(); bg.label(text="通用 (Global)", icon='TOOL_SETTINGS')
        bg.operator("ppas.set_all_global", text="一键设置渲染参数")
        bg.operator("ppas.set_resolution_fps", text="设置分辨率/帧率")
        if HAS_PYSIDE: bg.operator("ppas.open_texture_manager", text="贴图文件管理 (Qt)")
        else: bg.label(text="需 PySide6", icon='ERROR')

# Dynamic Registration Logic
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OTHER_SKILLS = [
    "lgt-project-info", "lgt-texture-audit", "lgt-texture-res-optimizer",
    "lgt-render-setup", "lgt-output-config", "lgt-qt-file-manager"
]

registered_modules = []

def register_other_skills():
    global registered_modules
    registered_modules.clear()
    
    for skill_name in OTHER_SKILLS:
        skill_path = os.path.join(SKILLS_DIR, skill_name, "scripts")
        if not os.path.exists(skill_path):
            print(f"[Warning] Skill path not found: {skill_path}")
            continue
            
        if skill_path not in sys.path:
            sys.path.append(skill_path)
            
        for file in os.listdir(skill_path):
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]
                try:
                    module = importlib.import_module(module_name)
                    importlib.reload(module)
                    if hasattr(module, "register"):
                        module.register()
                        registered_modules.append(module)
                        print(f"[Info] Registered skill module: {module_name}")
                except Exception as e:
                    print(f"[Error] Failed to register {module_name}: {e}")

def unregister_other_skills():
    global registered_modules
    for module in reversed(registered_modules):
        try:
            if hasattr(module, "unregister"):
                module.unregister()
        except Exception as e:
            print(f"[Error] Failed to unregister {module.__name__}: {e}")
    registered_modules.clear()

@persistent
def load_post_handler(dummy):
    # This assumes project_info module is available or has been registered
    try:
        from project_info import update_project_info
        bpy.app.timers.register(lambda: update_project_info(bpy.context.scene) or None, first_interval=0.1)
    except ImportError:
        pass

def register():
    bpy.types.Scene.ppas_project_name = bpy.props.StringProperty(name="Project Name", default="")
    bpy.utils.register_class(PPAS_PT_Lighting_Main)
    register_other_skills()
    if load_post_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post_handler)

def unregister():
    unregister_other_skills()
    bpy.utils.unregister_class(PPAS_PT_Lighting_Main)
    if load_post_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_handler)
    if hasattr(bpy.types.Scene, "ppas_project_name"):
        del bpy.types.Scene.ppas_project_name

if __name__ == "__main__":
    register()
