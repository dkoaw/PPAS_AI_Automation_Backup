import bpy

class PPAS_PT_Lighting_Main(bpy.types.Panel):
    bl_label = "PPAS 灯光合成工具 v15.9 (Full)"
    bl_idname = "PPAS_PT_Lighting_Main"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'PPAS Lgt'

    def draw(self, context):
        l = self.layout; s = context.scene
        
        # --- 1. 显存审计 (Audit) - 独立置顶 ---
        b1 = l.box()
        b1.label(text="显存审计 (Audit)", icon='GRAPH')
        b1.operator("ppas.audit_textures", text="启动贴图显存审计 (Qt)", icon='ZOOM_ALL')

        # --- 2. 贴图精度优化 (Texture Res Optimizer) ---
        l.separator(); b3 = l.box(); b3.label(text="贴图精度优化 (Texture)", icon='IMAGE_DATA')
        cam = context.scene.camera
        if cam: b3.label(text=f"焦距: {cam.data.lens:.1f}mm (视觉补偿)", icon='VIEW_CAMERA')
        b3.operator("ppas.auto_tex_res", text="按距离自动优化贴图")
        row_tex = b3.row(align=True)
        row_tex.operator("ppas.manual_tex_res", text="1k").resolution = '1k'
        row_tex.operator("ppas.manual_tex_res", text="2k").resolution = '2k'
        row_tex.operator("ppas.manual_tex_res", text="4k").resolution = '4k'

        # --- 4. 细分精度优化 (Subdivision Optimizer) ---
        l.separator(); b4 = l.box(); b4.label(text="细分精度优化 (Subdiv)", icon='MOD_SUBSURF')
        b4.operator("ppas.auto_subdiv_res", text="按距离自动优化细分")
        row_sub = b4.row(align=True)
        op0 = row_sub.operator("ppas.batch_edit_subdivision", text="0"); op0.view_levels=0; op0.render_levels=0
        op1 = row_sub.operator("ppas.batch_edit_subdivision", text="1"); op1.view_levels=0; op1.render_levels=1
        op2 = row_sub.operator("ppas.batch_edit_subdivision", text="2"); op2.view_levels=1; op2.render_levels=2

        # --- 5. 材质与分层屏蔽 (Materials & Mute) ---
        l.separator(); b5 = l.box(); b5.label(text="材质与屏蔽 (Mute)", icon='NODE_MATERIAL')
        b5.operator("ppas.setup_sss_layer", text="一键创建 SSS 渲染层", icon='SHADING_RENDERED')
        b5.operator("ppas.adjust_normal_strength", text="批量调整法线强度", icon='MOD_NORMALEDIT')
        b5.operator("ppas.mute_emission_on_layer", text="当前层屏蔽自发光", icon='LIGHT_DATA')

        # --- 5.5. 环境光与分层设置 (World HDR Layer) ---
        l.separator(); bw = l.box(); bw.label(text="环境光分层设置 (World HDR)", icon='WORLD')
        bw.operator("ppas.init_world_layer_params", text="获取节点参数并激活分层", icon='DRIVER')
        
        # 增加防御性判断，防止因属性未注册导致面板绘制中断
        if hasattr(context.scene, "ppas_world_settings"):
            ws = context.scene.ppas_world_settings
            col_w = bw.column(align=True)
            col_w.prop(ws, "hue")
            col_w.prop(ws, "sat")
            col_w.prop(ws, "val")
            col_w.prop(ws, "strength")

        # --- 6. 层可见性控制 (Visibility Control) ---
        l.separator(); b6 = l.box(); b6.label(text="分层可见性 (Visibility)", icon='HIDE_OFF')
        row_vis = b6.row(align=True)
        row_vis.operator("ppas.hide_selected_on_layer", text="当前层隐藏选中", icon='HIDE_ON')
        row_vis.operator("ppas.show_active_on_layer", text="当前层强制显示", icon='HIDE_OFF')

        # --- 7. 通用与渲染输出 (Global & Render Output) ---
        l.separator(); b7 = l.box(); b7.label(text="渲染与输出 (Render & Global)", icon='RENDER_RESULT')
        b7.operator("ppas.set_all_global", text="一键设置渲染参数 (Cycles/Eevee)", icon='TOOL_SETTINGS')
        b7.operator("ppas.set_resolution_fps", text="设置分辨率与帧率", icon='OUTPUT')
        b7.operator("ppas.setup_output_nodes", text="一键生成合成输出节点", icon='NODE_COMPOSITING')
        b7.operator("ppas.generate_render_bat", text="生成本地分层渲染 BAT", icon='CONSOLE')

        # --- 8. 独立窗口工具 (Utilities) ---
        l.separator(); b8 = l.box(); b8.label(text="独立窗口管理工具 (Qt Tools)", icon='WINDOW')
        b8.operator("ppas.open_render_layer_manager", text="渲染层管理器 (空壳)", icon='RENDERLAYERS')
        b8.operator("ppas.open_texture_manager", text="贴图文件管理 (Qt)", icon='FILE_FOLDER')

        # --- 9. 云端同步 (Cloud Backup) ---
        l.separator(); b9 = l.box(); b9.label(text="云端同步 (Cloud Backup)", icon='URL')
        b9.operator("ppas.cloud_backup_sync", text="☁️ 同步全量资产至 GitHub")

classes = (PPAS_PT_Lighting_Main,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
