import bpy
import json
import re

CORE_HANDLER_NAME = "World_Layer_Driver_Func.py"
CORE_HANDLER_CODE = r"""
import bpy
import json

def get_active_layer_name(depsgraph):
    if depsgraph and hasattr(depsgraph, "view_layer"):
        return depsgraph.view_layer.name
    try: return bpy.context.view_layer.name
    except: return ""

def get_world_param(depsgraph, param_name, default_val):
    try:
        layer_name = get_active_layer_name(depsgraph)
        world = bpy.context.scene.world
        if not world: return default_val
        data_str = world.get("ppas_layer_params", "{}")
        data = json.loads(data_str)
        if layer_name in data and param_name in data[layer_name]:
            return float(data[layer_name][param_name])
        return default_val
    except:
        return default_val

def register():
    bpy.app.driver_namespace["get_world_param"] = get_world_param

if __name__ == "__main__":
    register()
"""

def setup_driver_handler():
    text = bpy.data.texts.get(CORE_HANDLER_NAME) or bpy.data.texts.new(CORE_HANDLER_NAME)
    text.clear(); text.write(CORE_HANDLER_CODE); text.use_module = True 
    ns = {"bpy": bpy}
    exec(CORE_HANDLER_CODE, ns)
    if 'register' in ns: ns['register']()

def ensure_world_drivers():
    world = bpy.context.scene.world
    if not world or not world.use_nodes: return False
    
    setup_driver_handler()
    
    nodes = world.node_tree.nodes
    hsv_node = next((n for n in nodes if n.type == 'HUE_SAT'), None)
    bg_node = next((n for n in nodes if n.type == 'BACKGROUND'), None)
    
    if not hsv_node or not bg_node: return False
    
    def add_driver(node, socket_name, default_val):
        path = node.inputs[socket_name].path_from_id("default_value")
        if not world.node_tree.animation_data or not world.node_tree.animation_data.drivers.find(path):
            d = node.inputs[socket_name].driver_add("default_value")
            d.driver.use_self = False
            d.driver.expression = f"get_world_param(depsgraph, '{socket_name}', {default_val})"
    
    add_driver(hsv_node, 'Hue', 0.5)
    add_driver(hsv_node, 'Saturation', 1.0)
    add_driver(hsv_node, 'Value', 1.0)
    add_driver(bg_node, 'Strength', 0.0)
    return True

def get_layer_param(param_name, default_val):
    world = bpy.context.scene.world
    if not world: return default_val
    layer = bpy.context.view_layer.name
    try:
        data = json.loads(world.get("ppas_layer_params", "{}"))
        return data.get(layer, {}).get(param_name, default_val)
    except: return default_val

def set_layer_param(param_name, value):
    world = bpy.context.scene.world
    if not world: return
    layer = bpy.context.view_layer.name
    try: data = json.loads(world.get("ppas_layer_params", "{}"))
    except: data = {}
    
    if layer not in data: data[layer] = {}
    data[layer][param_name] = value
    world["ppas_layer_params"] = json.dumps(data)
    
    ensure_world_drivers()
    if world.node_tree:
        world.node_tree.update_tag()

class PPAS_WorldLayerSettings(bpy.types.PropertyGroup):
    hue: bpy.props.FloatProperty(name="Hue", min=0.0, max=1.0,
        get=lambda self: get_layer_param('Hue', 0.5),
        set=lambda self, val: set_layer_param('Hue', val))
    sat: bpy.props.FloatProperty(name="Sat", min=0.0, max=2.0,
        get=lambda self: get_layer_param('Saturation', 1.0),
        set=lambda self, val: set_layer_param('Saturation', val))
    val: bpy.props.FloatProperty(name="Val", min=0.0, max=10.0,
        get=lambda self: get_layer_param('Value', 1.0),
        set=lambda self, val: set_layer_param('Value', val))
    strength: bpy.props.FloatProperty(name="Strength", min=0.0, max=100.0,
        get=lambda self: get_layer_param('Strength', 0.0),
        set=lambda self, val: set_layer_param('Strength', val))

class PPAS_OT_InitWorldLayerParams(bpy.types.Operator):
    """捕捉当前节点数值作为本层初始参数，并挂载底层驱动"""
    bl_idname = "ppas.init_world_layer_params"
    bl_label = "捕捉节点参数并激活分层控制"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        world = context.scene.world
        if not world or not world.use_nodes: 
            self.report({'ERROR'}, "未找到World节点，请先执行[一键设置渲染参数]")
            return {'CANCELLED'}
            
        nodes = world.node_tree.nodes
        hsv_node = next((n for n in nodes if n.type == 'HUE_SAT'), None)
        bg_node = next((n for n in nodes if n.type == 'BACKGROUND'), None)
        if not hsv_node or not bg_node: return {'CANCELLED'}
        
        layer = context.view_layer.name
        try: data = json.loads(world.get("ppas_layer_params", "{}"))
        except: data = {}
        if layer not in data: data[layer] = {}
        
        # 仅在未被驱动时捕获真实参数
        path_hue = hsv_node.inputs['Hue'].path_from_id("default_value")
        is_driven = world.node_tree.animation_data and world.node_tree.animation_data.drivers.find(path_hue)
        
        if not is_driven:
            data[layer]['Hue'] = hsv_node.inputs['Hue'].default_value
            data[layer]['Saturation'] = hsv_node.inputs['Saturation'].default_value
            data[layer]['Value'] = hsv_node.inputs['Value'].default_value
            data[layer]['Strength'] = bg_node.inputs['Strength'].default_value
            world["ppas_layer_params"] = json.dumps(data)
        
        ensure_world_drivers()
        self.report({'INFO'}, f"[{layer}] 环境光分层控制已激活")
        return {'FINISHED'}

classes = (PPAS_WorldLayerSettings, PPAS_OT_InitWorldLayerParams)

def register_extra():
    bpy.types.Scene.ppas_world_settings = bpy.props.PointerProperty(type=PPAS_WorldLayerSettings)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    register_extra()

def unregister_extra():
    if hasattr(bpy.types.Scene, "ppas_world_settings"):
        del bpy.types.Scene.ppas_world_settings

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    unregister_extra()
