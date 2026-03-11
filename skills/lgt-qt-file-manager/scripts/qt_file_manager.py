import bpy
import sys

try:
    from PySide6 import QtWidgets
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False

def show_qt_mgr():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    # Note: This assumes PPAS_Texture_Manager_Qt_Fixed_v4 is in the path
    try:
        import PPAS_Texture_Manager_Qt_Fixed_v4 as tm
        tm.show_qt_dialog()
    except ImportError:
        print("[Error] PPAS_Texture_Manager_Qt_Fixed_v4 not found in path.")

class PPAS_OT_OpenTextureManager(bpy.types.Operator):
    bl_idname = "ppas.open_texture_manager"; bl_label = "打开贴图管理器"
    def execute(self, ctx):
        if not HAS_PYSIDE: 
            self.report({'ERROR'}, "PySide6 not installed")
            return {'CANCELLED'}
        try: 
            show_qt_mgr()
        except Exception as e: 
            self.report({'ERROR'}, f"Failed to open: {str(e)}")
        return {'FINISHED'}

classes = (PPAS_OT_OpenTextureManager,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
