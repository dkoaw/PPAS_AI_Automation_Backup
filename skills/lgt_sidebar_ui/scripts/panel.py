import bpy

class PPAS_PT_Lighting_Main(bpy.types.Panel):
    bl_label = "PPAS 灯光合成工具 v16.0 (Append-Only)"
    bl_idname = "PPAS_PT_Lighting_Main"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'PPAS Lgt'

    def draw(self, context):
        l = self.layout; s = context.scene
        
        # --- 0. 核心装配 (SSS Creation) --- 
        # 强制放在最显眼的位置，移除 hasattr 判断
        b_sss = l.box()
        b_sss.label(text="核心装配 (SSS Layers)", icon='SHADING_RENDERED')
        b_sss.operator("ppas.setup_sss_layer", text="一键创建 SSS 渲染层", icon='ADD')

        # --- 1. 显存审计 (Audit) ---
        l.separator(); b1 = l.box(); b1.label(text="显存审计 (Audit)", icon='GRAPH')
        if hasattr(bpy.ops.ppas, "audit_textures"):
            b1.operator("ppas.audit_textures", text="启动贴图显存审计 (Qt)", icon='ZOOM_ALL')
        else:
            b1.label(text="[MISSING] 审计模块", icon='ERROR')

        # --- 2. 贴图精度优化 (Texture) ---
        l.separator(); b2 = l.box(); b2.label(text="贴图精度优化 (Texture)", icon='IMAGE_DATA')
        cam = context.scene.camera
        if cam: b2.label(text=f"焦距: {cam.data.lens:.1f}mm (视觉补偿)", icon='VIEW_CAMERA')
        if hasattr(bpy.ops.ppas, "auto_tex_res"):
            b2.operator("ppas.auto_tex_res", text="按距离自动优化贴图")
            row_tex = b2.row(align=True)
            row_tex.operator("ppas.manual_tex_res", text="1k").resolution = '1k'
            row_tex.operator("ppas.manual_tex_res", text="2k").resolution = '2k'
            row_tex.operator("ppas.manual_tex_res", text="4k").resolution = '4k'

        # --- 3. 细分精度优化 (Subdiv) ---
        l.separator(); b3 = l.box(); b3.label(text="细分精度优化 (Subdiv)", icon='MOD_SUBSURF')
        if hasattr(bpy.ops.ppas, "auto_subdiv_res"):
            b3.operator("ppas.auto_subdiv_res", text="按距离自动优化细分")
            row_sub = b3.row(align=True)
            op0 = row_sub.operator("ppas.batch_edit_subdivision", text="0"); op0.view_levels=0; op0.render_levels=0
            op1 = row_sub.operator("ppas.batch_edit_subdivision", text="1"); op1.view_levels=0; op1.render_levels=1
            op2 = row_sub.operator("ppas.batch_edit_subdivision", text="2"); op2.view_levels=1; op2.render_levels=2

        # --- 4. 材质强度与屏蔽 ---
        l.separator(); b4 = l.box(); b4.label(text="材质与屏蔽 (Mute & Mats)", icon='NODE_MATERIAL')
        if hasattr(bpy.ops.ppas, "adjust_normal_strength"):
            b4.operator("ppas.adjust_normal_strength", text="批量调整法线强度", icon='MOD_NORMALEDIT')
        if hasattr(bpy.ops.ppas, "mute_emission_on_layer"):
            b4.operator("ppas.mute_emission_on_layer", text="当前层屏蔽自发光", icon='LIGHT_DATA')

        # --- 5. 环境光分层 (World HDR) ---
        l.separator(); b5 = l.box(); b5.label(text="环境光分层设置 (World HDR)", icon='WORLD')
        if hasattr(bpy.ops.ppas, "init_world_layer_params"):
            b5.operator("ppas.init_world_layer_params", text="激活单层环境光控制", icon='DRIVER')

        # --- 6. 分层可见性 (Visibility) ---
        l.separator(); b6 = l.box(); b6.label(text="分层可见性 (Visibility)", icon='HIDE_OFF')
        if hasattr(bpy.ops.ppas, "hide_selected_on_layer"):
            row_vis = b6.row(align=True)
            row_vis.operator("ppas.hide_selected_on_layer", text="当前层隐藏选中", icon='HIDE_ON')
            row_vis.operator("ppas.show_active_on_layer", text="当前层强制显示", icon='HIDE_OFF')

        # --- 7. 渲染与输出 (Render & Output) ---
        l.separator(); b7 = l.box(); b7.label(text="渲染与输出 (Render & Output)", icon='RENDER_RESULT')
        
        if hasattr(bpy.ops.ppas, "sync_master_params"):
            b7.operator("ppas.sync_master_params", text="⏬ 当前参数全域强制同步 (跟随始祖)", icon='FILE_REFRESH')
            
        if hasattr(bpy.ops.ppas, "set_all_global"):
            b7.operator("ppas.set_all_global", text="全局设置", icon='TOOL_SETTINGS')
        if hasattr(bpy.ops.ppas, "set_resolution_fps"):
            b7.operator("ppas.set_resolution_fps", text="设置分辨率与帧率", icon='OUTPUT')
        if hasattr(bpy.ops.ppas, "setup_output_nodes"):
            b7.operator("ppas.setup_output_nodes", text="一键配置合成器输出", icon='NODE_COMPOSITING')
        if hasattr(bpy.ops.ppas, "generate_render_bat"):
            b7.operator("ppas.generate_render_bat", text="生成本地分层渲染 BAT", icon='CONSOLE')

        # --- 8. 独立窗口工具 (Qt Tools) ---
        l.separator(); b8 = l.box(); b8.label(text="独立窗口工具 (Qt Panels)", icon='WINDOW')
        if hasattr(bpy.ops.ppas, "open_render_layer_manager"):
            b8.operator("ppas.open_render_layer_manager", text="独立渲染层管理器 (Qt)", icon='RENDERLAYERS')
        if hasattr(bpy.ops.ppas, "open_texture_manager"):
            b8.operator("ppas.open_texture_manager", text="贴图资产整理工具 (Qt)", icon='FILE_FOLDER')

        # --- 9. 云端备份 (Cloud Backup) ---
        l.separator(); b9 = l.box(); b9.label(text="资产同步 (Cloud Backup)", icon='URL')
        if hasattr(bpy.ops.ppas, "cloud_backup_sync"):
            b9.operator("ppas.cloud_backup_sync", text="☁️ 同步全量资产至 GitHub")

classes = (PPAS_PT_Lighting_Main,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
