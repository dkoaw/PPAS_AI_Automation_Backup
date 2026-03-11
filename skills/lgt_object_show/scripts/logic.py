import bpy

class PPAS_OT_ShowActiveOnLayer(bpy.types.Operator):
    """强行在当前层显示活跃物体 (清除黑名单 + 强制刷新)"""
    bl_idname = "ppas.show_active_on_layer"
    bl_label = "当前层强制显示"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'WARNING'}, "没有活跃物体")
            return {'CANCELLED'}

        current_layer = context.view_layer.name.strip()
        prop_name = "hidden_layer_list"
        current_str = obj.get(prop_name, "")
        
        if current_str:
            layers = [l.strip() for l in current_str.split(",") if l.strip()]
            
            if current_layer in layers:
                layers.remove(current_layer)
                obj[prop_name] = ",".join(layers)
                
                # --- 核心：强制更新序列 ---
                # 1. 标记数据变更
                obj.update_tag()
                
                # 2. 强制触发驱动器重计算 (通过 Mute 切换)
                if obj.animation_data and obj.animation_data.drivers:
                    for d in obj.animation_data.drivers:
                        if d.data_path in ["hide_viewport", "hide_render"]:
                            d.mute = not d.mute 
                            d.mute = not d.mute
                
                # 3. 场景图更新
                context.view_layer.update()
                
                # 4. 全局 UI 重绘
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
                
                self.report({'INFO'}, f"成功: 物体 '{obj.name}' 已在当前层恢复显示")
            else:
                self.report({'INFO'}, f"物体 '{obj.name}' 本就不在隐藏名单中")
        else:
            self.report({'INFO'}, "该物体没有隐藏列表属性")

        return {'FINISHED'}

classes = (PPAS_OT_ShowActiveOnLayer,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
