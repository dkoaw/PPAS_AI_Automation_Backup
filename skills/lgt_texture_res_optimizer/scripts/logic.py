import bpy
import os
import mathutils

class TexResManager:
    @staticmethod
    def get_target_path(current_path, target_res):
        if not current_path: return None
        abs_path = bpy.path.abspath(current_path)
        norm_path = os.path.normpath(abs_path); parts = norm_path.split(os.sep)
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
        if not new_path or not os.path.exists(os.path.dirname(new_path.replace("<UDIM>", "1001"))): return False
        image.filepath = new_path; image.reload(); return True

class PPAS_OT_ManualTexRes(bpy.types.Operator):
    bl_idname = "ppas.manual_tex_res"; bl_label = "手动精度切换"
    resolution: bpy.props.StringProperty()
    def execute(self, context):
        count = 0; selected_images = set()
        for obj in context.selected_objects:
            if obj.type != 'MESH': continue
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image: selected_images.add(node.image)
        for img in selected_images:
            if TexResManager.switch_image_res(img, self.resolution): count += 1
        self.report({'INFO'}, f"已切换 {count} 张贴图至 {self.resolution}")
        return {'FINISHED'}

class PPAS_OT_AutoTexRes(bpy.types.Operator):
    bl_idname = "ppas.auto_tex_res"; bl_label = "自动精度切换"
    def execute(self, context): return {'FINISHED'}

classes = (PPAS_OT_ManualTexRes, PPAS_OT_AutoTexRes) # 确保 classes 包含全部
