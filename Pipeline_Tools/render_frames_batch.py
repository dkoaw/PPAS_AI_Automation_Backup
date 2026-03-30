import bpy
import sys

# 1. 重新注册隐藏驱动器 (防止命令行下驱动失效)
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

# 2. 解析参数并执行多帧渲染
argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    if len(args) >= 2:
        target_vl = args[0]
        frames_str = args[1]
        frames = [int(x.strip()) for x in frames_str.split(",") if x.strip().isdigit()]
        
        print(f"\n======================================")
        print(f"  Target View Layer: {target_vl}")
        print(f"  Rendering Frames: {frames}")
        print(f"======================================\n")

        # 物理隔离 View Layer
        for vl in bpy.context.scene.view_layers:
            vl.use = (vl.name == target_vl)
            
        # 逐帧渲染 (使用 animation=True 保证输出文件名带帧号后缀)
        for f in frames:
            bpy.context.scene.frame_start = f
            bpy.context.scene.frame_end = f
            print(f"--- Rendering Frame {f} ---")
            bpy.ops.render.render(animation=True)
