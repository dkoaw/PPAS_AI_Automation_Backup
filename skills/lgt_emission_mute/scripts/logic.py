import bpy
import re

class PPAS_OT_MuteEmissionOnLayer(bpy.types.Operator):
    """将当前层加入自发光屏蔽黑名单 (V3 累加修复版)"""
    bl_idname = "ppas.mute_emission_on_layer"
    bl_label = "屏蔽当前层自发光"
    bl_options = {'REGISTER', 'UNDO'}

    def setup_driver_handler(self):
        CORE_HANDLER_CODE = r"""
import bpy
def get_current_layer_name(depsgraph):
    if hasattr(depsgraph, "view_layer"): return depsgraph.view_layer.name
    try: return bpy.context.view_layer.name
    except: return ""
def register():
    bpy.app.driver_namespace["get_current_layer_name"] = get_current_layer_name
if __name__ == "__main__": register()
"""
        tname = "Global_Emission_Driver_Simple.py"
        text = bpy.data.texts.get(tname) or bpy.data.texts.new(tname)
        text.clear()
        text.write(CORE_HANDLER_CODE)
        text.use_module = True 
        try:
            exec(CORE_HANDLER_CODE, {"bpy": bpy})
            bpy.app.driver_namespace["get_current_layer_name"] = bpy.app.driver_namespace.get("get_current_layer_name")
        except: pass

    def get_or_create_controller(self):
        group_name = "Global_Emission_Controller"
        ng = bpy.data.node_groups.get(group_name) or bpy.data.node_groups.new(group_name, 'ShaderNodeTree')
        
        val_node = next((n for n in ng.nodes if n.type == 'VALUE' and n.label == "Mute Logic"), None)
        if not val_node:
            ng.nodes.clear()
            if hasattr(ng, 'interface'):
                ng.interface.clear()
                ng.interface.new_socket("Multiplier", in_out='OUTPUT', socket_type='NodeSocketFloat')
            else:
                ng.outputs.clear()
                ng.outputs.new('NodeSocketFloat', "Multiplier")
            val_node = ng.nodes.new('ShaderNodeValue')
            val_node.label = "Mute Logic"
            val_node.name = "Value"
            out_node = ng.nodes.new('NodeGroupOutput')
            ng.links.new(val_node.outputs[0], out_node.inputs[0])
        return ng, val_node

    def execute(self, context):
        self.setup_driver_handler()
        ng, val_node = self.get_or_create_controller()
        
        current_layer = context.view_layer.name
        muted_layers = set()
        
        # 从现有驱动器读取已屏蔽列表
        if ng.animation_data and ng.animation_data.drivers:
            path = val_node.outputs[0].path_from_id("default_value")
            driver = ng.animation_data.drivers.find(path)
            if driver:
                expr = driver.driver.expression
                match = re.search(r"in\s*(\[.*?\])", expr)
                if match:
                    try: muted_layers.update(eval(match.group(1)))
                    except: pass
            
        muted_layers.add(current_layer)
        target_list = sorted(list(muted_layers))
        new_expr = f"0 if get_current_layer_name(depsgraph) in {target_list} else 1"
        
        d = val_node.outputs[0].driver_add("default_value")
        d.driver.use_self = True
        d.driver.expression = new_expr

        processed_trees = set()
        def process_tree(node_tree):
            if not node_tree or node_tree in processed_trees: return
            processed_trees.add(node_tree)
            for node in node_tree.nodes:
                if node.type == 'GROUP' and node.node_tree:
                    process_tree(node.node_tree)
                
                target_socket = None
                if node.type == 'BSDF_PRINCIPLED':
                    target_socket = node.inputs.get("Emission Strength") or node.inputs.get("Strength")
                elif node.type == 'EMISSION':
                    target_socket = node.inputs.get("Strength")
                if not target_socket: continue
                
                mute_node = next((n for n in node_tree.nodes if n.label == "Emission_Mute_Mult" and n.outputs[0].is_linked and n.outputs[0].links[0].to_socket == target_socket), None)
                
                if mute_node:
                    is_wired = any(l.from_node.type == 'GROUP' and l.from_node.node_tree == ng for l in mute_node.inputs[1].links)
                    if not is_wired:
                        ctrl_node = next((n for n in node_tree.nodes if n.type == 'GROUP' and n.node_tree == ng), None) or node_tree.nodes.new('ShaderNodeGroup')
                        ctrl_node.node_tree = ng
                        node_tree.links.new(ctrl_node.outputs[0], mute_node.inputs[1])
                    continue

                ctrl_node = node_tree.nodes.new('ShaderNodeGroup')
                ctrl_node.node_tree = ng
                mult_node = node_tree.nodes.new('ShaderNodeMath')
                mult_node.operation = 'MULTIPLY'
                mult_node.label = "Emission_Mute_Mult"
                if target_socket.is_linked:
                    orig_link = target_socket.links[0]
                    node_tree.links.new(orig_link.from_socket, mult_node.inputs[0])
                else:
                    mult_node.inputs[0].default_value = target_socket.default_value
                node_tree.links.new(ctrl_node.outputs[0], mult_node.inputs[1])
                node_tree.links.new(mult_node.outputs[0], target_socket)

        for mat in bpy.data.materials:
            if mat.use_nodes and mat.node_tree: process_tree(mat.node_tree)
            
        self.report({'INFO'}, f"自发光屏蔽完成: 已加入黑名单 {target_list}")
        return {'FINISHED'}

classes = (PPAS_OT_MuteEmissionOnLayer,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
