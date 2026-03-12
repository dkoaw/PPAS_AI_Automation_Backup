# -*- coding: utf-8 -*-
import bpy, json, os, sys, importlib.util

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
if SKILLS_DIR not in sys.path: sys.path.append(SKILLS_DIR)

# 严格执行时序：结构 -> 组名(先) -> 模型名(后) -> 曲线 -> 全局同步(最后)
PIPELINE = [
    ("utils", "fixer_core_utils"),
    ("builder", "fixer_structure_builder"),
    ("groups", "fixer_group_processor"),
    ("meshes", "fixer_mesh_processor"),
    ("curves", "fixer_curve_handler"),
    ("sync", "fixer_final_sync")
]

def run_atomic(nickname, folder, asset_name, report):
    logic_file = os.path.join(SKILLS_DIR, folder, "scripts", "atomic_logic.py")
    spec = importlib.util.spec_from_file_location(f"mod_{nickname}", logic_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "run"): mod.run(asset_name, report)

def main():
    import fixer_core_utils.scripts.atomic_logic as cu
    asset_name = cu.extract_asset_name(os.path.basename(bpy.data.filepath))
    report = {"asset_name": asset_name, "fixed": [], "manual_fix_needed": [], "missing_textures": []}
    
    print(f"--- [Strict Rebuild V16.1] Orchestrating for {asset_name} ---")
    for nick, folder in PIPELINE:
        try:
            run_atomic(nick, folder, asset_name, report)
            print(f"  [OK] {folder}")
        except Exception as e:
            print(f"  [FAIL] {folder}: {e}")
            
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath.replace(".blend", "_fixed.blend"))
    out_json = os.environ.get("QC_FIX_OUT_PATH", "qc_fix_out.json")
    with open(out_json, 'w') as f: json.dump(report, f, indent=4)

if __name__ == "__main__": main()
