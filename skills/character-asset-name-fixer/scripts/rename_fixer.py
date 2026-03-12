# -*- coding: utf-8 -*-
import bpy, json, os, sys, importlib.util

def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    if 'chr' in parts:
        idx = parts.index('chr')
        if idx + 1 < len(parts): return parts[idx + 1]
    return parts[0]

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
    # 核心修正：物理注入 atoms 路径，允许子模块直接 import core_utils
    if atoms_dir not in sys.path: sys.path.insert(0, atoms_dir)
    
    asset_name = extract_asset_name(os.path.basename(bpy.data.filepath))
    report = {"asset_name": asset_name, "fixed": [], "manual_fix_needed": [], "missing_textures": []}
    
    print(f"--- [Internal Atom Fixer V2] Orchestrating for {asset_name} ---")
    for nick, mod_name in PIPELINE:
        try:
            logic_file = os.path.join(atoms_dir, f"{mod_name}.py")
            spec = importlib.util.spec_from_file_location(mod_name, logic_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "run"): mod.run(asset_name, report)
            print(f"  [OK] {mod_name}")
        except Exception as e:
            print(f"  [FAIL] {mod_name}: {e}")
            
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath.replace(".blend", "_fixed.blend"))
    out_json = os.environ.get("QC_FIX_OUT_PATH", "qc_fix_out.json")
    with open(out_json, 'w') as f: json.dump(report, f, indent=4)

if __name__ == "__main__": main()
