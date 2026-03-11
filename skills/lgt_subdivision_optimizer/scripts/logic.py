import bpy
import mathutils

def get_evaluated_distance(obj, camera, depsgraph):
    """计算物体到相机的评估距离 (含 BBox 中心点校正)"""
    if not camera: return 0.0
    try:
        eval_obj = obj.evaluated_get(depsgraph)
        eval_cam = camera.evaluated_get(depsgraph)
        cam_loc = eval_cam.matrix_world.translation
        if eval_obj.bound_box:
            bbox_corners = [mathutils.Vector(b) for b in eval_obj.bound_box]
            center_local = sum(bbox_corners, mathutils.Vector()) / 8.0
            center_world = eval_obj.matrix_world @ center_local
            return (center_world - cam_loc).length
        return (eval_obj.matrix_world.translation - cam_loc).length
    except:
        return (obj.location - camera.location).length

class PPAS_OT_AutoSubdivRes(bpy.types.Operator):
    """基于视觉距离自动设置细分级别 (近2-1, 中1-0, 远0-0)"""
    bl_idname = "ppas.auto_subdiv_res"
    bl_label = "按视觉距离自动优化细分"
    bl_options = {'REGISTER', 'UNDO'}

    close_threshold: bpy.props.FloatProperty(name="近景阈值", default=3.0)
    far_threshold: bpy.props.FloatProperty(name="远景阈值", default=10.0)

    def execute(self, context):
        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "场景中没有摄像机，无法计算距离！")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        current_focal = cam.data.lens
        focal_factor = 50.0 / max(1.0, current_focal)
        
        count = 0
        subdiv_count = 0

        # 遍历可见物体
        for obj in context.visible_objects:
            if obj.type != 'MESH': continue
            
            # 计算焦距补偿后的有效距离
            phys_dist = get_evaluated_distance(obj, cam, depsgraph)
            eff_dist = phys_dist * focal_factor
            
            # 判定档位
            if eff_dist < self.close_threshold:
                v_level, r_level = 1, 2  # 近景
            elif eff_dist < self.threshold_mid_to_far(): # 这里逻辑需要对齐 3-10m
                v_level, r_level = 0, 1  # 中景
            else:
                v_level, r_level = 0, 0  # 远景

            # 应用修改
            for mod in obj.modifiers:
                if mod.type == 'SUBSURF':
                    mod.levels = v_level
                    mod.render_levels = r_level
                    subdiv_count += 1
            count += 1

        self.report({'INFO'}, f"细分自动优化完成: 处理了 {count} 个物体 ({subdiv_count} 个修改器)")
        return {'FINISHED'}

    def threshold_mid_to_far(self):
        return self.far_threshold

classes = (PPAS_OT_AutoSubdivRes,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
