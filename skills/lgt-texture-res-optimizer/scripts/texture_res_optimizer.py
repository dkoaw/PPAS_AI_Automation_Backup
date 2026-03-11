import bpy
import os
import math
import mathutils

class TexResManager:
    @staticmethod
    def get_target_path(current_path, target_res):
        if not current_path: return None
        abs_path = bpy.path.abspath(current_path)
        norm_path = os.path.normpath(abs_path)
        parts = norm_path.split(os.sep)
        target_name = "master"
        if target_res == '2k': target_name = "master_2k"
        elif target_res == '1k': target_name = "master_1k"
        res_folders = ["master", "master_1k", "master_2k"]
        found_idx = -1
        for i, part in enumerate(parts):
            if part.lower() in res_folders: found_idx = i; break
        if found_idx == -1: return None
        if parts[found_idx].lower() == target_name: return None
        parts[found_idx] = target_name
        return os.sep.join(parts)

    @staticmethod
    def switch_image_res(image, target_res):
        if image.source not in ['FILE', 'TILED', 'SEQUENCE']: return False
        new_path = TexResManager.get_target_path(image.filepath, target_res)
        if not new_path: return False
        if not os.path.exists(new_path):
            if '<UDIM>' in new_path:
                if not os.path.isdir(os.path.dirname(new_path)): return False
            elif '#' in new_path:
                 if not os.path.isdir(os.path.dirname(new_path)): return False
            else: return False
        print(f"[TexRes] Switch {image.name} -> {target_res}")
        image.filepath = new_path; image.reload(); return True

    @staticmethod
    def get_evaluated_distance(obj, camera, depsgraph):
        if not camera: return 0.0
        try:
            eval_obj = obj.evaluated_get(depsgraph); eval_cam = camera.evaluated_get(depsgraph)
            cam_loc = eval_cam.matrix_world.translation
            if eval_obj.bound_box:
                bbox_corners = [mathutils.Vector(b) for b in eval_obj.bound_box]
                center_local = sum(bbox_corners, mathutils.Vector()) / 8.0
                center_world = eval_obj.matrix_world @ center_local
                return (center_world - cam_loc).length
            return (eval_obj.matrix_world.translation - cam_loc).length
        except: return (obj.location - camera.location).length

def optimize_textures_by_distance(context, close_limit, far_limit):
    cam = context.scene.camera; 
    if not cam: return 0
    depsgraph = context.evaluated_depsgraph_get()
    current_focal = cam.data.lens; 
    if current_focal < 1.0: current_focal = 1.0
    focal_factor = 50.0 / current_focal
    img_min_dist = {}
    for obj in context.visible_objects:
        if obj.type != 'MESH': continue
        phys_dist = TexResManager.get_evaluated_distance(obj, cam, depsgraph)
        eff_dist = phys_dist * focal_factor
        for slot in obj.material_slots:
            if slot.material and slot.material.use_nodes:
                # Blender 5.0 compatibility: slot.material.node_tree is still used for material nodes
                for node in slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        img = node.image
                        if img not in img_min_dist: img_min_dist[img] = eff_dist
                        else:
                            if eff_dist < img_min_dist[img]: img_min_dist[img] = eff_dist
    count = 0
    for img, dist in img_min_dist.items():
        target = '2k' 
        if dist < close_limit: target = '4k'
        elif dist > far_limit: target = '1k'
        if TexResManager.switch_image_res(img, target): count += 1
    return count

def set_selected_textures_res(context, target_res):
    count = 0; selected_images = set()
    for obj in context.selected_objects:
        if obj.type != 'MESH': continue
        for slot in obj.material_slots:
            if slot.material and slot.material.use_nodes:
                for node in slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image: selected_images.add(node.image)
    for img in selected_images:
        if TexResManager.switch_image_res(img, target_res): count += 1
    return count

class PPAS_OT_AutoTexRes(bpy.types.Operator):
    bl_idname = "ppas.auto_tex_res"; bl_label = "自动切换贴图精度"
    close_threshold: bpy.props.FloatProperty(name="视觉近景(m)", default=3.0)
    far_threshold: bpy.props.FloatProperty(name="视觉远景(m)", default=10.0)
    def execute(self, ctx):
        c = optimize_textures_by_distance(ctx, self.close_threshold, self.far_threshold)
        self.report({'INFO'}, f"优化了 {c} 张贴图"); return {'FINISHED'}
    def invoke(self, ctx, evt): return ctx.window_manager.invoke_props_dialog(self)

class PPAS_OT_ManualTexRes(bpy.types.Operator):
    bl_idname = "ppas.manual_tex_res"; bl_label = "切换"
    resolution: bpy.props.EnumProperty(items=[('4k',"4K",""),('2k',"2K",""),('1k',"1K","")])
    def execute(self, ctx):
        c = set_selected_textures_res(ctx, self.resolution); self.report({'INFO'}, f"切换了 {c} 张"); return {'FINISHED'}

classes = (PPAS_OT_AutoTexRes, PPAS_OT_ManualTexRes)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
