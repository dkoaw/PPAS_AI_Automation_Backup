import sys
import os

# 确保能找到同级的 ppas_layer_core
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import ppas_layer_core

def execute():
    """
    执行【角色 Line 层】的核心逻辑
    - 渲染器：EEVEE 
    - Scene层级唯一：是 (Scene_line)
    """
    base_name = "Scene_line"
    engine = 'BLENDER_EEVEE'
    unique = True
    
    print(f"[Module Execute] 正在调用 EEVEE 引擎创建 {base_name} 渲染层...")
    
    # 1. 呼叫核心工厂，克隆清洗一条龙
    new_scene, new_vl = ppas_layer_core.create_layer_action_core(base_name, engine, unique)
    
    # 2. Line 层独有设置：比如直接关闭各种灯光显示，开启 Freestyle，只显示白模
    # new_scene.render.use_freestyle = True
    # 等等都可以加在这，跟角色 color 毫无耦合
    
    return new_scene, new_vl
