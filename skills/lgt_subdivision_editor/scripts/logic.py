import bpy

# 全局材质缓存
_MAT_NORMAL_CACHE = {}

def check_mat_has_normal(mat):
    if mat is None: return False
    if mat.name in _MAT_NORMAL_CACHE: return _MAT_NORMAL_CACHE[mat.name]
    
    has_normal = False
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'NORMAL_MAP':
                has_normal = True
                break
    _MAT_NORMAL_CACHE[mat.name] = has_normal
    return has_normal

def has_normal_map_fast(obj):
    if not obj or not obj.material_slots: return False
    for slot in obj.material_slots:
        if check_mat_has_normal(slot.material): return True
    return False

class PPAS_OT_BatchSubdivisionEditor(bpy.types.Operator):
    """批量编辑选中物体的细分修改器参数 (V4.1 高性能版)"""
    bl_idname = "ppas.batch_edit_subdivision"
    bl_label = "批量编辑细分"
    bl_options = {'REGISTER', 'UNDO'}

    # 默认值通过面板传入
    view_levels: bpy.props.IntProperty(name="视图细分", default=1, min=0, max=6)
    render_levels: bpy.props.IntProperty(name="渲染细分", default=2, min=0, max=6)
    auto_optimize_normal: bpy.props.BoolProperty(name="针对法线自动优化", default=True)

    def invoke(self, context, event):
        # 核心：如果是通过面板按钮（已传参）直接点击，不弹窗
        return self.execute(context)

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "未选中任何物体")
            return {'CANCELLED'}

        _MAT_NORMAL_CACHE.clear()
        count = 0
        subdiv_count = 0
        
        for obj in selected:
            if obj.type != 'MESH': continue
            
            found_normal = has_normal_map_fast(obj) if self.auto_optimize_normal else False
            
            for mod in obj.modifiers:
                if mod.type == 'SUBSURF':
                    subdiv_count += 1
                    mod.levels = self.view_levels
                    mod.render_levels = self.render_levels
                    
                    if found_normal:
                        if hasattr(mod, "use_custom_normals"): mod.use_custom_normals = True
                        mod.use_limit_surface = True
                        if hasattr(obj.data, "use_auto_smooth"): obj.data.use_auto_smooth = True
                    count += 1

        self.report({'INFO'}, f"处理完成: 更新了 {count} 个物体 ({subdiv_count} 个修改器)")
        return {'FINISHED'}

classes = (PPAS_OT_BatchSubdivisionEditor,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
