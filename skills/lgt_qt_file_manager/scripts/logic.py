import bpy
import sys
import os

def show_qt_mgr():
    # 模拟外部调用逻辑
    print("Calling external PySide6 Texture Manager...")

class PPAS_OT_OpenTextureManager(bpy.types.Operator):
    bl_idname = "ppas.open_texture_manager"; bl_label = "贴图文件管理 (Qt)"
    def execute(self, context):
        try:
            import PPAS_Texture_Manager_Qt_Fixed_v4 as tm
            tm.show_qt_dialog()
        except:
            self.report({'ERROR'}, "外部管理脚本丢失 (V4 Missing)")
        return {'FINISHED'}

classes = (PPAS_OT_OpenTextureManager,) # 确保包含
