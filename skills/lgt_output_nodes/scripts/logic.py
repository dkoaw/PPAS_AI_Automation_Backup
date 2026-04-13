import bpy
import os

class PPAS_OT_SetupOutputNodes(bpy.types.Operator):
    """一键配置合成器输出节点 (V15 精准对齐版)"""
    bl_idname = "ppas.setup_output_nodes"
    bl_label = "设置输出节点"
    bl_options = {'REGISTER', 'UNDO'}

    def global_purge(self):
        for scene in bpy.data.scenes:
            if hasattr(scene, "compositing_node_group"):
                scene.compositing_node_group = None
        for ng in list(bpy.data.node_groups):
            if ng.type == 'COMPOSITING':
                try: bpy.data.node_groups.remove(ng, do_unlink=True)
                except: pass

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, "请先保存文件！")
            return {'CANCELLED'}
            
        blend_dir = os.path.dirname(blend_path)
        blend_name = os.path.splitext(os.path.basename(blend_path))[0]
        
        self.global_purge()

        for scene in bpy.data.scenes:
            # 排除 scene母
            if scene.get("ppas_is_master") is not None or " [母]" in scene.name:
                continue

            scene.use_nodes = True
            tree = bpy.data.node_groups.new(scene.name + "_Comp", 'CompositorNodeTree')
            if hasattr(scene, "compositing_node_group"):
                scene.compositing_node_group = tree
                
            nodes = tree.nodes
            links = tree.links
            nodes.clear()
            
            for i, vl in enumerate(scene.view_layers):
                target_dir = os.path.join(blend_dir, "renderout_image", blend_name, scene.name, vl.name)
                try: os.makedirs(target_dir, exist_ok=True)
                except: pass
                
                # Render Layers Node
                rl_node = nodes.new('CompositorNodeRLayers')
                rl_node.scene = scene
                rl_node.layer = vl.name
                rl_node.location = (0, -i * 1000)
                
                # Check for Denoising
                denoise_node = None
                main_image = rl_node.outputs.get('Image')
                has_albedo = rl_node.outputs.get('Denoising Albedo')
                has_normal = rl_node.outputs.get('Denoising Normal')
                
                # 由于全局参数去掉了内建降噪，所以Noisy Image不存在，直接抓取原始Image与降噪数据
                if scene.render.engine == 'CYCLES' and has_albedo and has_albedo.enabled and has_normal and has_normal.enabled:
                    denoise_node = nodes.new('CompositorNodeDenoise')
                    denoise_node.location = (300, -i * 1000)
                    
                    # Blender API 跨版本兼容性修复 (Blender 4.0+ / 5.0 改为了输入 socket 而不是属性)
                    if hasattr(denoise_node, "use_hdr"):
                        try: denoise_node.use_hdr = True
                        except: pass
                    if "HDR" in denoise_node.inputs:
                        try: denoise_node.inputs["HDR"].default_value = 1.0 # 勾选 Checkbox
                        except: pass
                        try: denoise_node.inputs["HDR"].default_value = True
                        except: pass
                    
                    if main_image:
                        links.new(main_image, denoise_node.inputs['Image'])
                    links.new(has_albedo, denoise_node.inputs['Albedo'])
                    links.new(has_normal, denoise_node.inputs['Normal'])
                
                # File Output Node
                out_node = nodes.new('CompositorNodeOutputFile')
                # 调整排版以腾出降噪节点空间
                out_node.location = (600 if not denoise_node else 700, -i * 1000)
                
                # Format Specs
                try: out_node.format.file_format = 'OPEN_EXR_MULTILAYER'
                except: out_node.format.file_format = 'OPENEXR_MULTILAYER'
                out_node.format.color_depth = '32'
                out_node.format.exr_codec = 'ZIP'
                
                if hasattr(out_node, "save_as_render"): out_node.save_as_render = True
                if hasattr(out_node, "directory"): out_node.directory = target_dir
                else: out_node.base_path = target_dir
                if hasattr(out_node, "file_name"): out_node.file_name = f"{vl.name}."
                
                # Precision Mapping
                if hasattr(out_node, "file_output_items"):
                    out_node.file_output_items.clear()
                    connected_idx = 0
                    for rl_out in rl_node.outputs:
                        if rl_out.name == 'Alpha' or not rl_out.enabled:
                            continue
                            
                        # 如果启用了合成器降噪，则不输出原始降噪数据，并将主图替换为降噪节点的结果
                        if denoise_node:
                            if rl_out.name in ['Image', 'Noisy Image', 'Denoising Normal', 'Denoising Albedo', 'Denoising Depth']:
                                if rl_out.name == 'Image' or rl_out.name == 'Noisy Image':
                                    # 仅注册一次 Image 通道
                                    if 'Image' not in [item.name for item in out_node.file_output_items]:
                                        out_node.file_output_items.new('RGBA', name='Image')
                                        links.new(denoise_node.outputs['Image'], out_node.inputs[connected_idx])
                                        connected_idx += 1
                                continue

                        stype = 'RGBA'
                        if rl_out.type == 'VALUE': stype = 'FLOAT'
                        elif rl_out.type == 'VECTOR': stype = 'VECTOR'
                        
                        try:
                            # 过滤重复名字
                            if rl_out.name not in [item.name for item in out_node.file_output_items]:
                                out_node.file_output_items.new(stype, name=rl_out.name)
                                links.new(rl_out, out_node.inputs[connected_idx])
                                connected_idx += 1
                        except: pass

        self.report({'INFO'}, "输出节点配置完成 (V15 精准版)")
        return {'FINISHED'}

classes = (PPAS_OT_SetupOutputNodes,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
