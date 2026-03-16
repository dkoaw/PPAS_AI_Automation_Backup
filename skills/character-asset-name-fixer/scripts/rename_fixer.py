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
    script_dir = os.path.dirname(__file__)
    atoms_dir = os.path.join(script_dir, "atoms")
    
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

    # Save the fixed file
    fixed_path = bpy.data.filepath.replace(".blend", "_fixed.blend")
    bpy.ops.wm.save_as_mainfile(filepath=fixed_path)
    
    # Output report
    out_json = os.environ.get("QC_FIX_OUT_PATH", "qc_fix_out.json")
    with open(out_json, 'w') as f: 
        json.dump(report, f, indent=4)

if __name__ == "__main__": 
    main()
