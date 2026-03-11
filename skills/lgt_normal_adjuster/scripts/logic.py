import bpy

class PPAS_OT_AdjustNormalStrength(bpy.types.Operator):
    """基于原始数值批量调整法线/凹凸强度"""
    bl_idname = "ppas.adjust_normal_strength"
    bl_label = "调整法线强度"
    bl_options = {'REGISTER', 'UNDO'}

    multiplier: bpy.props.FloatProperty(
        name="强度乘数",
        description="基于原始强度的倍率 (例如 1.2)",
        default=1.2,
        min=0.0
    )

    def execute(self, context):
        adjusted_count = 0
        
        for mat in bpy.data.materials:
            if not mat or not mat.use_nodes or not mat.node_tree:
                continue
                
            nodes = mat.node_tree.nodes
            for node in nodes:
                # 仅处理法线和凹凸节点
                if node.type in ['NORMAL_MAP', 'BUMP']:
                    try:
                        # 获取强度输入口 (Strength)
                        strength_input = node.inputs['Strength']
                        
                        # 1. 检查是否有记录原始数值的自定义属性
                        if "ppas_original_strength" not in node:
                            # 如果没有，则将当前值标记为原始值
                            node["ppas_original_strength"] = strength_input.default_value
                        
                        # 2. 从自定义属性中读取原始值进行计算
                        original_val = node["ppas_original_strength"]
                        new_val = original_val * self.multiplier
                        
                        # 3. 应用新数值
                        strength_input.default_value = new_val
                        adjusted_count += 1
                    except Exception as e:
                        print(f"  [Error] Failed to process node in '{mat.name}': {str(e)}")

        self.report({'INFO'}, f"法线调整完成：共处理 {adjusted_count} 个节点 (倍率: {self.multiplier:.2f})")
        return {'FINISHED'}

classes = (PPAS_OT_AdjustNormalStrength,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
