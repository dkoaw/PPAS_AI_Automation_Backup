import bpy
import json
import traceback

class HDRBlenderCore:
    """
    环境底层驱动总栈 (Blender Core Driver-Based Weaver)
    [核心逻辑]：不再暴力重组节点，而是与右侧『激活单层环境光控制』并轨，
    通过修改 World 的 ppas_layer_params 字典并挂载驱动器来实现分层控制。
    """

    SLOT_NAME = "ppas_hdr_data_slot"
    MASTER_SCENE_PREFIX = "Scene"
    HDR_LAYER_TAG = "hdr"

    @staticmethod
    def get_true_context_keys():
        """突破 PyQt 焦点劫持，强行获取真正的当前渲染层，返回 (scn_name, vl_name) 双键"""
        wm = bpy.data.window_managers[0] if bpy.data.window_managers else None
        if wm and wm.windows:
            for win in wm.windows:
                # 获取正在激活的或主窗口的 view_layer
                if win.screen and win.scene and win.view_layer:
                    return win.scene.name, win.view_layer.name
        try: return bpy.context.window.scene.name, bpy.context.window.view_layer.name
        except:
            try: return bpy.context.scene.name, bpy.context.view_layer.name
            except: return "Scene", "ViewLayer"

    CORE_HANDLER_NAME = "PPAS_HDR_Farm_Guard.py"
    CORE_HANDLER_CODE = r"""import bpy
import json

def get_eval_context(depsgraph):
    if depsgraph:
        return depsgraph.scene.name, depsgraph.view_layer.name
    wm = bpy.data.window_managers[0] if bpy.data.window_managers else None
    if wm and wm.windows:
        for win in wm.windows:
            if win.screen and win.scene and win.view_layer:
                return win.scene.name, win.view_layer.name
    try: return bpy.context.window.scene.name, bpy.context.window.view_layer.name
    except:
        try: return bpy.context.scene.name, bpy.context.view_layer.name
        except: return "Scene", "ViewLayer"

_last_hdr_sig = None

def get_world_param(depsgraph, param_name, default_value=0.0):
    try:
        scn_name, vl_name = get_eval_context(depsgraph)
        world = bpy.data.scenes[scn_name].world if scn_name in bpy.data.scenes else bpy.context.scene.world
        data_str = world.get("ppas_layer_params", "{}")
        all_params = json.loads(data_str)
        key = f"{scn_name}::{vl_name}"
        
        # 1. 找到私有配置，直接使用
        if key in all_params:
            return all_params[key].get(param_name, default_value)
            
        # 2. 智能母体继承判定：如果在 hdr 层且尚未被配置，向祖先 Scene 要数据
        if "hdr" in scn_name.lower() or "hdr" in vl_name.lower():
            master_scn_name = "Scene"
            for s in bpy.data.scenes:
                if "ppas_is_master" in s:
                    master_scn_name = s.name
                    break
            fb_key = f"{master_scn_name}::ViewLayer"
            if fb_key in all_params:
                return all_params[fb_key].get(param_name, default_value)
                
        # 3. 被抛弃的层（非HDR且私有无配置），强行归零隔离
        return 0.0 if param_name == "Strength" else default_value
    except: pass
    return default_value

def auto_sync_context_hdr(*args):
    global _last_hdr_sig
    try:
        scn_name, vl_name = get_eval_context(None)
        sig = f"{scn_name}::{vl_name}"
        
        world = bpy.data.scenes[scn_name].world if scn_name in bpy.data.scenes else bpy.context.scene.world
        # 即使非HDR也要被处理黑洞化，所以不 return，必须跑下去
        if not world or not world.use_nodes: return
        
        data_str = world.get("ppas_layer_params", "{}")
        all_params = json.loads(data_str)
        
        path = ""
        # 寻找应该用哪张图的逻辑与驱动对齐
        if sig in all_params:
            path = all_params[sig].get("path", "")
        elif "hdr" in scn_name.lower() or "hdr" in vl_name.lower():
            master_scn_name = "Scene"
            for s in bpy.data.scenes:
                if "ppas_is_master" in s:
                    master_scn_name = s.name
                    break
            fb_key = f"{master_scn_name}::ViewLayer"
            if fb_key in all_params:
                path = all_params[fb_key].get("path", "")
                
        # 检测路径和层状态进行物理图片更新
        if sig != _last_hdr_sig or world.get("_last_hdr_path", "") != path:
            nodes = world.node_tree.nodes
            env_node = next((n for n in nodes if n.type == 'TEX_ENVIRONMENT'), None)
            if env_node:
                if path:
                    try:
                        img = bpy.data.images.load(path, check_existing=True)
                        if env_node.image != img:
                            env_node.image = img
                    except: pass
                else:
                    env_node.image = None
            
            world["_last_hdr_path"] = path
            _last_hdr_sig = sig
    except: pass

if not hasattr(bpy, "_ppas_hdr_msgbus_owner"):
    bpy._ppas_hdr_msgbus_owner = object()
_msgbus_owner = bpy._ppas_hdr_msgbus_owner

def register():
    bpy.msgbus.clear_by_owner(_msgbus_owner)
    
    # 全局监听视图层、场景的切换
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Window, "view_layer"),
        owner=_msgbus_owner,
        args=(),
        notify=auto_sync_context_hdr,
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Window, "scene"),
        owner=_msgbus_owner,
        args=(),
        notify=auto_sync_context_hdr,
    )

def unregister():
    bpy.msgbus.clear_by_owner(_msgbus_owner)
"""

    @staticmethod
    def is_context_authorized():
        scn_name, vl_name = HDRBlenderCore.get_true_context_keys()
        scn = bpy.data.scenes.get(scn_name)

        if not scn: return False, "无法获取场景上下文"

        # 1. 如果是 Scene 主层，必须拥有 ppas_is_master 标记
        if scn.name == HDRBlenderCore.MASTER_SCENE_PREFIX and vl_name == "ViewLayer":
            if "ppas_is_master" not in scn:
                return False, "当前为主场景，但未完成母场景(Master Scene)的全局标记，请先前往全局设置指定为主层。"
            return True, ""
        
        # 2. 如果是派生的 HDR 特定图层，则无条件放行（因为克隆时系统主动剥离了它的 master 基因，防范它造反）
        if HDRBlenderCore.HDR_LAYER_TAG in scn_name.lower() or HDRBlenderCore.HDR_LAYER_TAG in vl_name.lower():
            return True, ""

        # 3. 其它所有常规分层，全部铁腕拦截
        return False, f"未授权层 ({scn_name}::{vl_name})：只有主层的 ViewLayer 或包含 '{HDRBlenderCore.HDR_LAYER_TAG}' 等特定命名的渲染层才允许独立入库配置 HDR。"

    @staticmethod
    def snapshot_to_sandboox(config_data_dict):
        vl = bpy.context.view_layer
        scn = bpy.context.scene
        pack_string = json.dumps(config_data_dict)
        vl[HDRBlenderCore.SLOT_NAME] = pack_string
        scn[HDRBlenderCore.SLOT_NAME] = pack_string

    @staticmethod
    def read_from_sandbox():
        world = bpy.context.scene.world
        if not world: return None
        scn_name, vl_name = HDRBlenderCore.get_true_context_keys()
        key = f"{scn_name}::{vl_name}"
        
        try:
            all_params = json.loads(world.get("ppas_layer_params", "{}"))
            p = None
            
            # 1. 尝试寻找私有配置
            if key in all_params:
                p = all_params[key]
            # 2. 如果是合法的子级 HDR 层，且没有私有配置，则查找母体过继基因
            elif HDRBlenderCore.HDR_LAYER_TAG in scn_name.lower() or HDRBlenderCore.HDR_LAYER_TAG in vl_name.lower():
                master_scn_name = "Scene"
                for s in bpy.data.scenes:
                    if "ppas_is_master" in s:
                        master_scn_name = s.name
                        break
                fb_key = f"{master_scn_name}::ViewLayer"
                if fb_key in all_params:
                    p = all_params[fb_key]
                    
            if p is not None:
                return {
                    "path": p.get("path", ""),
                    "r_x": p.get("Rotation_X", 0.0),
                    "r_y": p.get("Rotation_Y", 0.0),
                    "r_z": p.get("Rotation_Z", 0.0),
                    "purity": p.get("Saturation", 1.0),
                    "power": p.get("Strength", 1.0),
                    "val": p.get("Value", 1.0),
                    "no_img_mode": False
                }
        except: pass
        
        # 3. 如果都没有，或者处于黑洞区，强制回发清零配置
        return {
            "path": "",
            "r_x": 0.0, "r_y": 0.0, "r_z": 0.0,
            "purity": 1.0, "power": 0.0, "val": 1.0,
            "no_img_mode": False
        }

    @staticmethod
    def ensure_advanced_drivers():
        world = bpy.context.scene.world
        if not world or not world.use_nodes: return
        
        nodes = world.node_tree.nodes
        map_node = next((n for n in nodes if n.type == 'MAPPING'), None)
        hsv_node = next((n for n in nodes if n.type == 'HUE_SAT'), None)
        bg_node = next((n for n in nodes if n.type == 'BACKGROUND'), None)

        def add_driver(node, socket_name, param_name, default_val):
            try:
                path = node.inputs[socket_name].path_from_id("default_value")
                if not world.node_tree.animation_data or not world.node_tree.animation_data.drivers.find(path):
                    d = node.inputs[socket_name].driver_add("default_value")
                    d.driver.expression = f"get_world_param(depsgraph, '{param_name}', {default_val})"
            except: pass

        if map_node:
            for i, axis in enumerate(['X', 'Y', 'Z']):
                try:
                    path = map_node.inputs[2].path_from_id("default_value")
                    # index 用于 Vector 数组 (0=X, 1=Y, 2=Z)
                    if not world.node_tree.animation_data or not world.node_tree.animation_data.drivers.find(path, index=i):
                        d = map_node.inputs[2].driver_add("default_value", i)
                        d.driver.expression = f"get_world_param(depsgraph, 'Rotation_{axis}', 0.0)"
                except:
                    pass

        if hsv_node:
            add_driver(hsv_node, 'Saturation', 'Saturation', 1.0)
            add_driver(hsv_node, 'Value', 'Value', 1.0)
        
        if bg_node:
            # 核心安全罩：如果在无记录且非HDR层，驱动直接计算为 0，防止视口被污染
            add_driver(bg_node, 'Strength', 'Strength', 0.0)

    @staticmethod
    def setup_farm_guard():
        text = bpy.data.texts.get(HDRBlenderCore.CORE_HANDLER_NAME)
        if not text:
            text = bpy.data.texts.new(HDRBlenderCore.CORE_HANDLER_NAME)
        text.clear()
        text.write(HDRBlenderCore.CORE_HANDLER_CODE)
        text.use_module = True 
        
        try:
            mod = text.as_module()
            if hasattr(mod, 'register'):
                mod.register()
        except: pass

    @staticmethod
    def inject_topology_and_update(pack_data=None):
        is_legal, msg = HDRBlenderCore.is_context_authorized()
        if not is_legal: return False, msg

        if pack_data is None:
            pack_data = HDRBlenderCore.read_from_sandbox()
        if not pack_data: return False, "暂无数据"

        world = bpy.context.scene.world
        if not world: return False, "无 World"
        
        scn_name, vl_name = HDRBlenderCore.get_true_context_keys()
        key = f"{scn_name}::{vl_name}"
        
        try:
            all_params = json.loads(world.get("ppas_layer_params", "{}"))
        except:
            all_params = {}
            
        all_params[key] = {
            "path": pack_data.get("path", ""),
            "Rotation_X": pack_data.get("r_x", 0.0),
            "Rotation_Y": pack_data.get("r_y", 0.0),
            "Rotation_Z": pack_data.get("r_z", 0.0),
            "Saturation": pack_data.get("purity", 1.0),
            "Value": pack_data.get("val", 1.0),
            "Strength": pack_data.get("power", 1.0),
        }
        
        world["ppas_layer_params"] = json.dumps(all_params)
        
        nodes = world.node_tree.nodes
        env_node = next((n for n in nodes if n.type == 'TEX_ENVIRONMENT'), None)
        if not env_node:
            try:
                env_node = nodes.new('ShaderNodeTexEnvironment')
                bg_node = next((n for n in nodes if n.type == 'BACKGROUND'), None)
                if bg_node: world.node_tree.links.new(env_node.outputs[0], bg_node.inputs[0])
            except: pass 
            
        HDRBlenderCore.ensure_advanced_drivers()
        HDRBlenderCore.setup_farm_guard()
        
        if env_node:
            path = pack_data.get("path", "")
            if path:
                try:
                    img = bpy.data.images.load(path, check_existing=True)
                    env_node.image = img
                except: pass
            else:
                env_node.image = None

        if not hasattr(bpy.app, "driver_namespace") or "get_world_param" not in bpy.app.driver_namespace:
            txt = bpy.data.texts.get(HDRBlenderCore.CORE_HANDLER_NAME)
            if txt:
                try:
                    mod = txt.as_module()
                    bpy.app.driver_namespace["get_world_param"] = mod.get_world_param
                except: pass
                
        return True, "环境控制已同步至分层主控"

    @staticmethod
    def pass_master_genes(target_scene_name):
        return True, "过继完成"

if __name__ == "__main__":
    pass
