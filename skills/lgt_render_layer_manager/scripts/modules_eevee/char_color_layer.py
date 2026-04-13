import sys
import os
import bpy

# 确保能找到同级的 ppas_layer_core
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import ppas_layer_core

def execute():
    """
    执行【角色 Color 层】的核心逻辑
    - 渲染器：EEVEE (依据最新管线需求全局默认)
    - Scene层级唯一：是 (Scene_color)
    - 渲染层级递增：是 (Scene_color_001, 002...)
    """
    base_name = "chr_color"
    engine = 'BLENDER_EEVEE'
    unique = True
    
    print(f"[Module Execute] 正在调用 EEVEE 引擎创建 {base_name} 渲染层...")
    
    # 1. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 2. 隔离化的本层独占设置区 (根据诉求移除 Shadows 和 Raytracing)
    new_scene.eevee.use_shadows = False
    new_scene.eevee.use_raytracing = False
    
    # 3. 追加全域同步级别的「免死金牌」免疫护城河标识
    # 当母场景未来点击全域同步时，这两个参数绝对不会被母场景的开启状态覆盖掉
    new_scene["ppas_protected_keys"] = ["use_shadows", "use_raytracing"]
    
    # 4. ViewLayer 层级独占勾选 (这些属性本身并不受 sync_master_params 干扰，无需免死金牌)
    new_vl.use_pass_z = True
    new_vl.use_pass_cryptomatte_object = True
    new_vl.use_pass_cryptomatte_material = True
    
    # 5. 自动运用【管线专属：层隐藏技能】把所有灯光在本层杀除
    lights_to_hide = [obj for obj in new_scene.objects if obj.type == 'LIGHT']
    if lights_to_hide and hasattr(bpy.ops.ppas, 'hide_selected_on_layer'):
        # 必须给算子准备一个无懈可击的安全上下文
        active_window = bpy.data.window_managers[0].windows[0]
        # 修改对象选择状态
        for obj in new_scene.objects: obj.select_set(False)
        for obj in lights_to_hide: obj.select_set(True)
        # 挂载上下文后执行专属隐藏技能
        with bpy.context.temp_override(window=active_window, scene=new_scene, view_layer=new_vl, selected_objects=lights_to_hide):
            try:
                bpy.ops.ppas.hide_selected_on_layer()
                print(f"[Module Execute] 成功在 {new_vl.name} 隐藏了 {len(lights_to_hide)} 盏灯光。")
            except Exception as e:
                print(f"[Module Execute] 灯光自动隐藏失败: {e}")
                
    # 6. 自动关闭 All_Light 集合 (排除该集合下的所有对象)
    def exclude_collection(layer_coll, target_name):
        if layer_coll.name == target_name:
            layer_coll.exclude = True
            return True
        for child in layer_coll.children:
            if exclude_collection(child, target_name):
                return True
        return False
        
    if exclude_collection(new_vl.layer_collection, "All_Light"):
        print(f"[Module Execute] 成功在 {new_vl.name} 排除 (Exclude) 了 All_Light 集合。")
                
    return new_scene, new_vl
