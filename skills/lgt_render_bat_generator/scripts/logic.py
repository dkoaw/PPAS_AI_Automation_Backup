import bpy
import os
import subprocess

class PPAS_OT_GenerateRenderBat(bpy.types.Operator):
    """生成单层渲染批处理文件 (V4.1 Robust)"""
    bl_idname = "ppas.generate_render_bat"
    bl_label = "生成渲染批处理"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, "请先保存文件！")
            return {'CANCELLED'}
        
        file_dir = os.path.dirname(blend_path)
        file_name = os.path.basename(blend_path)
        base_name = os.path.splitext(file_name)[0]
        bat_path = os.path.join(file_dir, base_name + "_render.bat")
        blender_exe = bpy.app.binary_path
        
        # 1. 注入管理逻辑脚本块
        script_name = "render_manager.py"
        manager_logic = """import bpy
import sys
def get_active_layer_name(depsgraph):
    if depsgraph and hasattr(depsgraph, "view_layer"): return depsgraph.view_layer.name
    try: return bpy.context.view_layer.name
    except: return ""
def is_layer_hidden(depsgraph, obj):
    try:
        ln = get_active_layer_name(depsgraph)
        hls = obj.get("hidden_layer_list", "")
        if not hls or not ln: return 0.0
        return 1.0 if (ln.strip() in [l.strip() for l in hls.split(",") if l.strip()]) else 0.0
    except: return 0.0
bpy.app.driver_namespace["is_layer_hidden"] = is_layer_hidden
argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    if args:
        target_vl = args[0]
        for vl in bpy.context.scene.view_layers:
            vl.use = (vl.name == target_vl)
        bpy.ops.render.render(animation=True)
"""
        text_block = bpy.data.texts.get(script_name) or bpy.data.texts.new(script_name)
        text_block.from_string(manager_logic)
        
        # 2. 构建 BAT 内容 (GBK 编码以适配 Windows CMD)
        lines = [
            "@echo off",
            f'set BLENDER="{blender_exe}"',
            f'set FILE="{blend_path}"',
            f"set START={context.scene.frame_start}",
            f"set END={context.scene.frame_end}",
            "",
            "echo ===========================================",
            f"echo BATCH RENDER: {file_name}",
            "echo ===========================================",
            ""
        ]
        
        for scene in bpy.data.scenes:
            # 护城河排异：绝对不允许母场景 (Master) 被编入渲染阵列，防止渲染出无效的无光底图
            if scene.get("ppas_is_master") is not None or " [母]" in scene.name:
                continue
                
            lines.append(f'echo --- Scene: {scene.name} ---')
            for vl in scene.view_layers:
                # 使用 --python-text 确保在后台模式下立即执行注入的逻辑
                cmd = f'%BLENDER% -b %FILE% -y -S "{scene.name}" -s %START% -e %END% --python-text "{script_name}" -- "{vl.name}"'
                lines.append(f'echo Rendering {vl.name}...')
                lines.append(cmd)
                lines.append("")
        
        lines.extend(["echo DONE", "pause"])
        
        try:
            with open(bat_path, "w", encoding="gbk") as f:
                f.write("\n".join(lines))
            
            self.report({'INFO'}, f"BAT 生成成功: {os.path.basename(bat_path)}")
            
            # 自动使用 Notepad++ 打开
            npp_exe = r"C:\Program Files\Notepad++\notepad++.exe"
            if os.path.exists(npp_exe):
                subprocess.Popen([npp_exe, bat_path])
            else:
                os.startfile(bat_path)
                
        except Exception as e:
            self.report({'ERROR'}, f"写入失败: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

classes = (PPAS_OT_GenerateRenderBat,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
