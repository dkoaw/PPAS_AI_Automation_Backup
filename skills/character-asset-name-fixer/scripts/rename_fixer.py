# -*- coding: utf-8 -*-
import bpy, json, os, sys, importlib.util

PIPELINE = [
    ("builder", "structure_builder"),
    ("groups", "group_processor"),
    ("meshes", "mesh_processor"),
    ("curves", "curve_handler"),
    ("sync", "final_sync")
]

def main():
    # Skills 目录动态查找 (兼容桌面、工程等多种运行路径)
    skills_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    atoms_dir = os.path.join(skills_dir, "blender-fixer-atoms", "scripts")
    
    # 物理注入 atoms 路径，允许子模块直接 import core_utils
    if atoms_dir not in sys.path: 
        sys.path.insert(0, atoms_dir)

    import core_utils
    
    filename = os.path.basename(bpy.data.filepath)
    asset_name = core_utils.extract_asset_name(filename)
    
    report = {
        "asset_name": asset_name, 
        "fixed": [], 
        "manual_fix_needed": [], 
        "missing_textures": []
    }

    print(f"--- [Internal Atom Fixer V2.1] Orchestrating for {asset_name} ---")
    
    for nick, mod_name in PIPELINE:
        try:
            logic_file = os.path.join(atoms_dir, f"{mod_name}.py")
            spec = importlib.util.spec_from_file_location(mod_name, logic_file)       
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "run"): 
                mod.run(asset_name, report)
            print(f"  [OK] {mod_name}")
        except Exception as e:
            print(f"  [FAIL] {mod_name}: {e}")

    # Generate the _fixed absolute path securely
    if bpy.data.filepath:
        fixed_path = os.path.abspath(bpy.data.filepath.replace(".blend", "_fixed.blend"))
    else:
        fixed_path = os.path.abspath(filename.replace(".blend", "_fixed.blend"))
    
    # 注入 pipeline-file-ops 路径以使用通用文件操作
    ops_dir = os.path.join(skills_dir, "pipeline-file-ops", "scripts")
    if ops_dir not in sys.path:
        sys.path.insert(0, ops_dir)
    import file_ops

    # 使用共享原子组件进行前置清理
    file_ops.pre_clean_stale_files(fixed_path)

    # Save to a temporary unique path first to avoid ANY Blender file lock or backup logic
    temp_path = fixed_path + ".tmp"
    if os.path.exists(temp_path):
        try: os.remove(temp_path)
        except: pass
        
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    # Use save_as_mainfile to dump the current memory state to the temp path
    bpy.ops.wm.save_as_mainfile(filepath=temp_path, copy=True, check_existing=False)
    
    # OS-level move is atomic and bypasses all Blender's @ backup logic
    import shutil
    shutil.move(temp_path, fixed_path)
    
    # 可选: 使用共享组件进行后置验证
    file_ops.post_clean_atomic_save(fixed_path)
    
    # Output report
    out_json = os.environ.get("QC_FIX_OUT_PATH", "qc_fix_out.json")
    with open(out_json, 'w') as f: 
        json.dump(report, f, indent=4)

if __name__ == "__main__": 
    main()
