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
    try:
        c.device = 'GPU'; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01; c.samples = 256
        c.preview_adaptive_threshold = 0.1; c.preview_samples = 128
        c.sampling_pattern = 'BLUE_NOISE'; c.seed = 0
        c.max_bounces = 38; c.diffuse_bounces = 2; c.glossy_bounces = 2
        c.transmission_bounces = 20; c.volume_bounces = 0; c.transparent_max_bounces = 32
        c.sample_clamp_direct = 0.0; c.sample_clamp_indirect = 10.0
        c.blur_glossy = 0.0; c.caustics_reflective = False; c.caustics_refractive = False
        c.use_fast_gi = False
        
        # --- 降噪设置修正 (Denoising) ---
        c.use_preview_denoising = True   # 开启视口降噪 (应用户要求修正)
        
        c.use_denoising = True           # 开启渲染降噪
        if hasattr(c, "denoiser"):
            c.denoiser = 'OPENIMAGEDENOISE'
        if hasattr(c, "denoising_use_gpu"):
            c.denoising_use_gpu = True   # 开启 GPU 加速
    except: pass

def setup_eevee_settings(scene):
    e = scene.eevee; r = scene.render
    
    # 1. TAA
    try:
        e.taa_samples = 64
        e.use_taa_reprojection = False
        e.taa_render_samples = 128
    except Exception as ex: print(f"EEVEE TAA Error: {ex}")
    
    # 2. Shadows
    try:
        e.use_shadow_jitter_viewport = True
        e.use_shadows = True
        e.shadow_ray_count = 2
        e.shadow_step_count = 10
        e.shadow_resolution_scale = 1.0  # 核心修复：必须是 Float
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

class PPAS_OT_SetAllGlobal(bpy.types.Operator):
    bl_idname = "ppas.set_all_global"
    bl_label = "设置渲染参数"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 核心修正：必须物理切换引擎，否则 5.0.1 会吞掉属性赋值
        original_engine = context.scene.render.engine
        
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
        
        self.report({'INFO'}, "渲染参数及 World 节点网同步完成 (强干预版)")
        return {'FINISHED'}

classes = (PPAS_OT_SetAllGlobal,) # 关键：必须显式导出 classes 元组
