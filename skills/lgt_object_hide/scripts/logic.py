import bpy
import re

CORE_HANDLER_NAME = "Visibility_Driver_Func_Robust_V6.py"
CORE_HANDLER_CODE = r"""
import bpy

def get_active_layer_name(depsgraph):
    if depsgraph and hasattr(depsgraph, "view_layer"):
        return depsgraph.view_layer.name
    try: return bpy.context.view_layer.name
    except: return ""

def is_layer_hidden(depsgraph, obj):
    try:
        layer_name = get_active_layer_name(depsgraph)
        if not layer_name: return 0.0
        hidden_list_str = obj.get("hidden_layer_list", "")
        if not hidden_list_str: return 0.0
        layers = [l.strip() for l in hidden_list_str.split(",") if l.strip()]
        return 1.0 if (layer_name.strip() in layers) else 0.0
    except: return 0.0

def register():
    bpy.app.driver_namespace["is_layer_hidden"] = is_layer_hidden
    bpy.app.driver_namespace["get_active_layer_name"] = get_active_layer_name

if __name__ == "__main__": register()
"""

class PPAS_OT_HideSelectedOnLayer(bpy.types.Operator):
    """层设置选中物体隐藏 (V6 Robust - 含动画迁移)"""
    bl_idname = "ppas.hide_selected_on_layer"
    bl_label = "层隐藏/显示切换"
    bl_options = {'REGISTER', 'UNDO'}

    def migrate_animation(self, obj, prop_name, target_prop_name):
        """将关键帧迁移至自定义属性，支持 5.0 ChannelBags"""
        if not obj.animation_data or not obj.animation_data.action:
            obj[target_prop_name] = getattr(obj, prop_name)
            return

        action = obj.animation_data.action
        def scan_curves(curves):
            for fc in curves:
                if fc.data_path == prop_name:
                    fc.data_path = f'["{target_prop_name}"]'
                    fc.update()

        if hasattr(action, "fcurves"): scan_curves(action.fcurves)
        if hasattr(action, "layers"):
            for layer in action.layers:
                for strip in getattr(layer, "strips", []):
                    if hasattr(strip, "channelbags"):
                        for bag in strip.channelbags: scan_curves(bag.fcurves)
                    elif hasattr(strip, "fcurves"): scan_curves(strip.fcurves)
        obj[target_prop_name] = getattr(obj, prop_name)

    def execute(self, context):
        # 1. 注册核心驱动逻辑
        text = bpy.data.texts.get(CORE_HANDLER_NAME) or bpy.data.texts.new(CORE_HANDLER_NAME)
        text.clear(); text.write(CORE_HANDLER_CODE); text.use_module = True 
        ns = {"bpy": bpy}
        exec(CORE_HANDLER_CODE, ns)
        if 'register' in ns: ns['register']()

        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "未选中资产")
            return {'CANCELLED'}

        current_layer = context.view_layer.name
        msg = "隐藏"
        
        for obj in selected:
            prop_name = "hidden_layer_list"
            current_val = obj.get(prop_name, "")
            layers = set(l.strip() for l in str(current_val).split(",") if l.strip())
            
            if current_layer in layers:
                layers.remove(current_layer)
                msg = "显示"
            else:
                layers.add(current_layer)
                msg = "隐藏"
                
            obj[prop_name] = ",".join(sorted(list(layers)))
            
            for vis_prop in ["hide_viewport", "hide_render"]:
                orig_prop = f"original_{vis_prop}"
                existing_d = None
                if obj.animation_data and obj.animation_data.drivers:
                    existing_d = obj.animation_data.drivers.find(vis_prop)
                
                if not existing_d or "is_layer_hidden" not in existing_d.driver.expression:
                    self.migrate_animation(obj, vis_prop, orig_prop)
                    d = obj.driver_add(vis_prop)
                else:
                    d = existing_d
                
                d.driver.use_self = True
                d.driver.expression = f"max(is_layer_hidden(depsgraph, self), self.get('{orig_prop}', 0))"
            
            obj.update_tag()

        self.report({'INFO'}, f"资产已在 '{current_layer}' 层设为 {msg}")
        return {'FINISHED'}

classes = (PPAS_OT_HideSelectedOnLayer,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
