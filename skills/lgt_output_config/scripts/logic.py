import bpy

class PPAS_OT_SetResolutionFPS(bpy.types.Operator):
    bl_idname = "ppas.set_resolution_fps"
    bl_label = "Set Resolution & FPS"
    
    res_enum: bpy.props.EnumProperty(
        name="Resolution",
        items=[
            ('4096x1716', "4096x1716", "4K Wide"),
            ('3072x3072', "3072x3072", "3K Square"),
            ('2048x858', "2048x858", "2K Wide"),
            ('1024x429', "1024x429", "1K Wide"),
        ],
        default='2048x858'
    )
    
    fps_enum: bpy.props.EnumProperty(
        name="FPS",
        items=[('24', "24", ""), ('25', "25", ""), ('30', "30", "")],
        default='24'
    )

    def invoke(self, ctx, evt):
        return ctx.window_manager.invoke_props_dialog(self)

    def execute(self, ctx):
        w, h = map(int, self.res_enum.split('x'))
        render = ctx.scene.render
        render.resolution_x = w
        render.resolution_y = h
        render.fps = int(self.fps_enum)
        render.resolution_percentage = 100  # 强制锁定 100%
        
        self.report({'INFO'}, f"Applied: {w}x{h} @ {self.fps_enum}fps (100% Scale)")
        return {'FINISHED'}

classes = (PPAS_OT_SetResolutionFPS,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
