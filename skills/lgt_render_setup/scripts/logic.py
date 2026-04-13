import bpy
import math

def setup_world_hdr_nodes(scene):
    """清理并重构 World 环境光节点 (标准化 HDR 接入)"""
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world
        
    world.use_nodes = True
    
    # --- 防重复执行保护 ---
    # 如果已经执行过标准化设置，则跳过清空和重建，保护用户后续添加的层设置
    if world.get("ppas_hdr_setup_done"):
        print("World HDR nodes already setup. Skipping to protect existing layers.")
        return

    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # 1. 清空所有旧节点
    nodes.clear()
    
    # 2. 创建新节点
    node_tex_coord = nodes.new('ShaderNodeTexCoord')
    node_tex_coord.location = (-1000, 0)
    
    node_mapping = nodes.new('ShaderNodeMapping')
    node_mapping.vector_type = 'POINT'
    node_mapping.inputs['Rotation'].default_value[2] = math.radians(-120)  # Z 轴 -120 度
    node_mapping.location = (-800, 0)
    
    node_env_tex = nodes.new('ShaderNodeTexEnvironment')
    node_env_tex.location = (-500, 0)
    # 不自动加载图片，仅作为占位符待用户手动接入 white.hdr
    
    node_hsv = nodes.new('ShaderNodeHueSaturation')
    node_hsv.location = (-200, 0)
    
    node_bg = nodes.new('ShaderNodeBackground')
    node_bg.inputs['Strength'].default_value = 0.0  # 强度默认 0.0
    node_bg.location = (0, 0)
    
    node_output = nodes.new('ShaderNodeOutputWorld')
    node_output.location = (200, 0)
    
    # 3. 建立连线
    links.new(node_tex_coord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_env_tex.inputs['Vector'])
    links.new(node_env_tex.outputs['Color'], node_hsv.inputs['Color'])
    links.new(node_hsv.outputs['Color'], node_bg.inputs['Color'])
    links.new(node_bg.outputs['Background'], node_output.inputs['Surface'])

    # 4. 标记为已完成初始化
    world["ppas_hdr_setup_done"] = 1

def setup_cycles_settings(scene):
    c = scene.cycles
    
    # 1. 核心采样
    try:
        c.device = 'GPU'
        c.use_adaptive_sampling = True
        c.adaptive_threshold = 0.01
        c.samples = 256
        c.adaptive_min_samples = 0
        c.preview_adaptive_threshold = 0.1
        c.preview_samples = 128
        c.sampling_pattern = 'BLUE_NOISE'
        c.seed = 0
    except Exception as e: print(f"Cycles Sampling Error: {e}")
        
    # 2. 光路反弹与钳制
    try:
        c.max_bounces = 38
        c.diffuse_bounces = 2
        c.glossy_bounces = 2
        c.transmission_bounces = 20
        c.volume_bounces = 0
        c.transparent_max_bounces = 32
        c.sample_clamp_direct = 0.0
        c.sample_clamp_indirect = 10.0
        c.blur_glossy = 0.0
        c.caustics_reflective = False
        c.caustics_refractive = False
    except Exception as e: print(f"Cycles Light Paths Error: {e}")
        
    # 3. Fast GI
    try:
        c.use_fast_gi = False
    except Exception as e: print(f"Cycles Fast GI Error: {e}")
        
    # 4. 降噪细节 (Denoising)
    try:
        # Viewport Denoise
        scene.cycles.use_preview_denoising = True
        if hasattr(scene.cycles, "preview_denoiser"): scene.cycles.preview_denoiser = 'AUTOMATIC'
        if hasattr(scene.cycles, "preview_denoising_input_passes"): scene.cycles.preview_denoising_input_passes = 'RGB'
        if hasattr(scene.cycles, "preview_denoising_prefilter"): scene.cycles.preview_denoising_prefilter = 'FAST'
        if hasattr(scene.cycles, "preview_denoising_quality"): scene.cycles.preview_denoising_quality = 'BALANCED'
        if hasattr(scene.cycles, "preview_denoising_use_gpu"): scene.cycles.preview_denoising_use_gpu = True
        
        # Render Denoise
        scene.cycles.use_denoising = False
        if hasattr(scene.cycles, "denoiser"): scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        if hasattr(scene.cycles, "denoising_input_passes"): scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        if hasattr(scene.cycles, "denoising_prefilter"): scene.cycles.denoising_prefilter = 'ACCURATE'
        if hasattr(scene.cycles, "denoising_quality"): scene.cycles.denoising_quality = 'HIGH'
        if hasattr(scene.cycles, "denoising_use_gpu"): scene.cycles.denoising_use_gpu = True
    except Exception as e: print(f"Cycles Denoise Error: {e}")

def setup_eevee_settings(scene):
    e = scene.eevee; r = scene.render
    
    # 1. TAA
    try:
        e.taa_samples = 64
        e.use_taa_reprojection = False
        e.taa_render_samples = 128
    except Exception as ex: print(f"EEVEE TAA Error: {ex}")
    
    # 2. Shadows (截图精确校对版)
    try:
        e.use_shadow_jitter_viewport = True
        e.use_shadows = True
        e.shadow_ray_count = 1           # 截图为 1
        e.shadow_step_count = 6          # 截图为 6
        e.shadow_resolution_scale = 1.0  
        e.light_threshold = 0.01
    except Exception as ex: print(f"EEVEE Shadow Error: {ex}")

    # 3. Raytracing
    try:
        e.use_raytracing = True
        if hasattr(e, "ray_tracing_method"): e.ray_tracing_method = 'SCREEN'
        opts = e.ray_tracing_options
        opts.resolution_scale = '1'
        opts.screen_trace_quality = 0.75
        opts.use_denoise = True
        opts.denoise_spatial = True
        opts.denoise_temporal = True
        opts.denoise_bilateral = True
        opts.trace_max_roughness = 0.5
    except Exception as ex: print(f"EEVEE Raytracing Error: {ex}")

    # 4. Fast GI
    try:
        e.use_fast_gi = False
        if hasattr(e, "fast_gi_method"):
            e.fast_gi_method = 'GLOBAL_ILLUMINATION'
            e.fast_gi_resolution = '1'
            e.fast_gi_ray_count = 8
            e.fast_gi_step_count = 20
            e.fast_gi_quality = 0.25
            e.fast_gi_distance = 0.0
            e.fast_gi_thickness_near = 0.25
            e.fast_gi_thickness_far = 0.785398
            e.fast_gi_bias = 0.05
    except Exception as ex: print(f"EEVEE Fast GI Error: {ex}")

    # 5. Volumetrics
    try:
        e.volumetric_tile_size = '4'
        e.volumetric_samples = 128
        e.volumetric_sample_distribution = 0.8
        e.volumetric_ray_depth = 16
        e.use_volume_custom_range = True
        e.volumetric_start = 0.1
        e.volumetric_end = 100
        e.volumetric_shadow_samples = 32
    except Exception as ex: print(f"EEVEE Volumetrics Error: {ex}")

    # 6. Global & Film
    try:
        r.use_simplify = True
        r.simplify_subdivision = 3
        r.simplify_subdivision_render = 3
        r.filter_size = 1.5
        r.film_transparent = True
        r.use_high_quality_normals = True
        e.use_overscan = True
        e.overscan_size = 10.0
        r.compositor_device = 'GPU'
    except Exception as ex: print(f"EEVEE Global Error: {ex}")

    # 7. Color Management
    try:
        scene.display_settings.display_device = 'sRGB'
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
    except Exception as ex: print(f"EEVEE Color Mgt Error: {ex}")

def setup_light_collections(scene):
    """创建并构建特定的灯光 Collection 层级，防重复创建"""
    # 1. 确保顶级 Collection 'All_Light' 存在
    target_root_name = "All_Light"
    if target_root_name not in bpy.data.collections:
        all_light_coll = bpy.data.collections.new(target_root_name)
    else:
        all_light_coll = bpy.data.collections[target_root_name]
        
    # 链接到当期 Scene Collection
    if target_root_name not in scene.collection.children.keys():
        scene.collection.children.link(all_light_coll)

    # 2. 确保子 Collection
    sub_names = ["TreD_Light", "TwoD_Light", "Fog_Light", "Sss_Light"]
    for name in sub_names:
        if name not in bpy.data.collections:
            sub_coll = bpy.data.collections.new(name)
        else:
            sub_coll = bpy.data.collections[name]
            
        # 链接到 All_Light
        if name not in all_light_coll.children.keys():
            all_light_coll.children.link(sub_coll)
            # 如果它原本在场景根目录，解绑它以保持层级干净
            if name in scene.collection.children.keys():
                scene.collection.children.unlink(sub_coll)

class PPAS_OT_SetAllGlobal(bpy.types.Operator):
    bl_idname = "ppas.set_all_global"
    bl_label = "设置渲染参数"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 0. 防呆拦截：极简白名单策略，全管线只有名为 "Scene" 的原始工程场景才被允许设为主层
        if context.scene.name != "Scene":
            self.report({'ERROR'}, f"管线拦截防呆：非法的母场景来源 [{context.scene.name}]！根据严格管线规范，只有名为 'Scene' 的节点有权升格为主层。")
            return {'CANCELLED'}
                
        # 核心修正：必须物理切换引擎，否则 5.0.1 会吞掉属性赋值
        original_engine = context.scene.render.engine
        
        # 0. 确立该场景为管线法定的终极“母场景”
        context.scene["ppas_is_master"] = True
        
        # 1. 切换到 EEVEE 并设置
        context.scene.render.engine = 'BLENDER_EEVEE'
        setup_eevee_settings(context.scene)
        
        # 2. 切换到 CYCLES 并设置
        context.scene.render.engine = 'CYCLES'
        setup_cycles_settings(context.scene)
        
        # 3. 恢复引擎
        context.scene.render.engine = original_engine
        
        # 4. 设置环境光
        setup_world_hdr_nodes(context.scene)
        
        # 5. 设置全局灯光层级 (All_Light -> 子组)
        setup_light_collections(context.scene)
        
        # --- 终极强制刷新防止 5.0.1 吞数据 ---
        # --- 终极强制刷新防止 5.0.1 吞数据 ---
        try:
            if hasattr(context.scene.cycles, "preview_denoising_use_gpu"): context.scene.cycles.preview_denoising_use_gpu = True
            if hasattr(context.scene.cycles, "denoising_use_gpu"): context.scene.cycles.denoising_use_gpu = True
            
            # 【核心双重锁死】：在引擎切换造成的系统级乱序结束后，再次用纯 Python 物理写入一次关闭命令
            context.scene.cycles.use_denoising = False
            
            bpy.context.view_layer.update()
        except Exception as e:
            print(f"Update Override Error: {e}")
        
        self.report({'INFO'}, "参数同步完成，当前场景已被定为『绝对母场景』(Master)")
        return {'FINISHED'}

class PPAS_OT_SyncMasterParams(bpy.types.Operator):
    """(母场景控制) 以初始化过的母场景为准，将所有渲染参数（分辨率、引擎、采样等）强制统一下发给工程内的所有子层。跳过图层输出路径等专属配置。"""
    bl_idname = "ppas.sync_master_params"
    bl_label = "⏬ 以母场景参数全域同步"
    bl_options = {'REGISTER', 'UNDO'}

    def copy_rna_props(self, src, dest, skip_keys):
        for k in src.rna_type.properties.keys():
            if k in skip_keys or k == 'rna_type': continue
            try: setattr(dest, k, getattr(src, k))
            except AttributeError: pass

    def execute(self, context):
        # 优先寻找带有印记的母场景，若无则使用当前所处场景
        master = next((s for s in bpy.data.scenes if s.get("ppas_is_master")), context.scene)
        
        skip_render_props = {'filepath', 'views', 'layers', 'image_settings'}
        
        count = 0
        for scene in bpy.data.scenes:
            if scene == master: continue
            
            # ====== 核心免疫护城河级联触发区 ======
            # 根据每个子场景自己的属性宣告，抓取它的绝对特免防同步名单！
            raw_immune_keys = scene.get("ppas_protected_keys")
            immune_set = set(list(raw_immune_keys)) if raw_immune_keys else set()
            
            # 1. Render Basics
            render_skip = set(skip_render_props).union(immune_set)
            self.copy_rna_props(master.render, scene.render, render_skip)
            
            # 2. Cycles & EEVEE
            if hasattr(scene, 'cycles') and hasattr(master, 'cycles'):
                self.copy_rna_props(master.cycles, scene.cycles, immune_set)
            if hasattr(scene, 'eevee') and hasattr(master, 'eevee'):
                self.copy_rna_props(master.eevee, scene.eevee, immune_set)
                
            # 3. Color Management
            if hasattr(scene, 'display_settings') and hasattr(master, 'display_settings'):
                self.copy_rna_props(master.display_settings, scene.display_settings, immune_set)
            if hasattr(scene, 'view_settings') and hasattr(master, 'view_settings'):
                self.copy_rna_props(master.view_settings, scene.view_settings, immune_set)
            
            count += 1
            
        self.report({'INFO'}, f"管线纪律执行：成功使用母场景[{master.name}]覆盖了其余 {count} 个子场景的渲染参数！")
        return {'FINISHED'}

classes = (PPAS_OT_SetAllGlobal, PPAS_OT_SyncMasterParams) # 关键：必须显式导出 classes 元组
