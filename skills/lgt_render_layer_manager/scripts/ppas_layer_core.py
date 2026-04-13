import bpy

def get_master_scene():
    """获取标记母场景，如果没有找到侧阻断渲染栈，返回 None"""
    return next((s for s in bpy.data.scenes if s.get("ppas_is_master")), None)

def create_layer_action_core(base_name, engine, unique=False):
    """
    渲染层核心算法与引擎状态锁
    :param base_name: 分层基名，例如 "Scene_color"
    :param engine: 渲染引擎标识符，比如 'BLENDER_EEVEE'
    :param unique: 是否强制全局只有唯一场景
    :return: (new_scene, new_vl) 新生成的Scene与ViewLayer对象
    """
    master = get_master_scene()
    if master is None:
        raise ValueError("NO_MASTER_SCENE: 找不到任何被设定为母场景的主层！请先打在某个场景点击 [全局设置] 设定主层。")

    scene_existed = False
    
    # 修复 PyQt5/PySide6 下，挂失焦点导致的 bpy.context.window 为 None 的情况
    # 直接剥离 context，使用最高权限的绝对物理路由
    active_window = bpy.context.window or bpy.data.window_managers[0].windows[0]
    
    if unique and bpy.data.scenes.get(base_name):
        scene_existed = True
        new_scene = bpy.data.scenes[base_name]
        active_window.scene = new_scene
    else:
        # 核心防呆：必须从 Master 母场景作为源进行复制
        active_window.scene = master
        
        # 终极修复：解决外部 Qt 触发内置算子引起的 context poll error
        # 直接强行灌入系统物理窗口级别的 context 覆写 (适用 Blender 3.2+ 管线标准)
        with bpy.context.temp_override(window=active_window):
            bpy.ops.scene.new(type='LINK_COPY')
            
        new_scene = active_window.scene
        
        # 核心防呆：剥离从母层克隆带来的母层记号遗传
        if new_scene.get("ppas_is_master") is not None:
            del new_scene["ppas_is_master"]
            
        if unique:
            new_scene.name = base_name
        else:
            idx = 1
            while bpy.data.scenes.get(f"{base_name}_{idx:02d}"): idx += 1
            new_scene.name = f"{base_name}_{idx:02d}"
            
        # 强制锁定分层引擎
        new_scene.render.engine = engine
        
    # --- 渲染层 (View Layers) 动态自增流水线 ---
    max_idx = 0
    for vl in new_scene.view_layers:
        if vl.name.startswith(f"{base_name}_"):
            try:
                num = int(vl.name.split("_")[-1])
                if num > max_idx:
                    max_idx = num
            except ValueError:
                pass
                
    next_idx = max_idx + 1
    new_vl_name = f"{base_name}_{next_idx:03d}"
    
    # 创建新的渲染层并赋予序号
    new_vl = new_scene.view_layers.new(new_vl_name)
    
    # 首次建档大扫除：清空由 LINK_COPY 带来的旧朝冗余视图层
    if not scene_existed:
        for vl in list(new_scene.view_layers):
            if vl != new_vl:
                new_scene.view_layers.remove(vl)
    
    # 尝试更新用户视野焦点
    try:
        active_window.view_layer = new_vl
    except Exception:
        pass
        
    # === 新增需求：创建任何层时，自动隐藏 特定套件 及其所有子集 ===
    objs_to_hide = []
    for obj in new_scene.objects:
        if "_hiddenMesh_Grp" in obj.name or "_staticCurve_Grp" in obj.name:
            if obj not in objs_to_hide:
                objs_to_hide.append(obj)
            
            # 递归获取它的所有子物体
            def get_all_children(parent):
                for child in parent.children:
                    if child not in objs_to_hide:
                        objs_to_hide.append(child)
                    get_all_children(child)
                    
            get_all_children(obj)
            
    if objs_to_hide and hasattr(bpy.ops.ppas, 'hide_selected_on_layer'):
        # 尝试剥除旧的选择状态以防干扰
        try:
            for obj in new_scene.objects: obj.select_set(False)
            for obj in objs_to_hide: obj.select_set(True)
        except Exception:
            pass # 即使在隐藏/锁定状态无法 select，下方的 temp_override selected_objects 依然可以直接压入上下文
            
        with bpy.context.temp_override(window=active_window, scene=new_scene, view_layer=new_vl, selected_objects=objs_to_hide):
            try:
                bpy.ops.ppas.hide_selected_on_layer()
                print(f"[Layer Core] 全署全局拦截：成功在 {new_vl.name} 执行核心渲染屏蔽 (隐藏节点数: {len(objs_to_hide)})。")
            except Exception as e:
                print(f"[Layer Core] 全署全局拦截警告：_hiddenMesh_Grp 渲染器隐藏异常 (可能由于之前已覆盖): {e}")

            # 独立执行视口隐藏，绝不允许被上方算子的潜在报错阻断！
            try:
                for obj in objs_to_hide:
                    obj.hide_set(True, view_layer=new_vl)
                print(f"[Layer Core] 全署全局拦截：成功在 {new_vl.name} 强制闭合 {len(objs_to_hide)} 个组员的视口小眼睛。")
            except Exception as e:
                print(f"[Layer Core] 小眼睛闭合脱轨: {e}")
        
    return new_scene, new_vl
