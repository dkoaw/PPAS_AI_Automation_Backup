import bpy

def setup_cycles_settings(context):
    scene = context.scene; context.scene.render.engine = 'CYCLES'; c = scene.cycles
    try: c.device = 'GPU'; c.samples = 256; c.adaptive_threshold = 0.01; c.use_denoising = True; c.max_bounces = 38
    except: pass

def setup_eevee_settings(context):
    scene = context.scene; context.scene.render.engine = 'BLENDER_EEVEE'
    try: 
        # Blender 4.2+ Eevee Next changes some property names
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 256
        elif hasattr(scene.eevee, "render_samples"):
            scene.eevee.render_samples = 256
    except: pass

class PPAS_OT_SetAllGlobal(bpy.types.Operator):
    bl_idname = "ppas.set_all_global"; bl_label = "设置渲染参数"
    def execute(self, ctx):
        c=ctx.scene.render.engine; setup_eevee_settings(ctx); setup_cycles_settings(ctx); ctx.scene.render.engine=c; return {'FINISHED'}

classes = (PPAS_OT_SetAllGlobal,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
