# -*- coding: utf-8 -*-
import bpy
import json
import os
import sys
import importlib.util

# ----------------- 核心配置 -----------------
SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
QC_ROOT = os.path.join(SKILLS_DIR, "blender-character-qc", "scripts")
CHECKS_DIR = os.path.join(QC_ROOT, "checks")

# 环节对应的质检项原子清单
QC_PROFILES = {
    "tex": [
        "cameras", "lights", "unused_images", "unused_materials", "unused_meshes",
        "extra_scripts", "empty_groups", "ngons", "transform_reset", "illegal_nodes",
        "subdivision", "uv_negative", "uv_cross_udim", "uv_overlap", "uv_inverted",
        "uv_layer_naming", "uv_layer_count", "asset_prefix", "mesh_parent_logic",
        "data_sync", "hierarchy_nesting", "group_validity", "facial_nodes",
        "texture_consistency"
    ],
    "lib": [
        "cameras", "lights", "unused_images", "unused_materials", "unused_meshes",
        "extra_scripts", "empty_groups", "ngons", "transform_reset", "illegal_nodes",
        "subdivision", "uv_negative", "uv_layer_naming", "asset_prefix",
        "data_sync", "hierarchy_nesting", "group_validity", "rig_fingerprint"
    ]
}

def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    if 'chr' in parts:
        idx = parts.index('chr')
        if idx + 1 < len(parts): return parts[idx + 1]
    return parts[0]

def run_check_atom(atom_name, asset_name, results):
    """动态加载并运行单个质检原子脚本"""
    logic_file = os.path.join(CHECKS_DIR, f"check_{atom_name}.py")
    if not os.path.exists(logic_file):
        print(f"[QC Orchestrator] Warning: Missing check module: {atom_name}")
        return
        
    spec = importlib.util.spec_from_file_location(f"qc_atom_{atom_name}", logic_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "run"):
        mod.run(results, asset_name)

def run_full_qc(step_name):
    if step_name not in QC_PROFILES:
        return [{"check": "Config Error", "status": "FAIL", "issues": [f"Invalid step: {step_name}"]}]
        
    asset_name = extract_asset_name(os.path.basename(bpy.data.filepath))
    results = []
    
    print(f"--- [QC Orchestrator] Starting QC ({step_name}) for {asset_name} ---")
    
    # 按清单调度原子质检项
    for atom in QC_PROFILES[step_name]:
        try:
            run_check_atom(atom, asset_name, results)
            print(f"  [OK] Checked: {atom}")
        except Exception as e:
            results.append({"check": atom, "status": "ERROR", "issues": [str(e)]})
            print(f"  [FAIL] {atom}: {e}")
            
    print(f"--- [QC Orchestrator] Full QC Finished ---")
    return results

if __name__ == "__main__":
    try:
        step_name = os.environ.get("QC_STEP_NAME", "tex")
        qc_results = run_full_qc(step_name)
        
        out_path = os.environ.get("QC_OUT_PATH", "qc_out.json")
        with open(out_path, 'w') as f:
            json.dump(qc_results, f, ensure_ascii=False, indent=4)
            
        print(f"QC completed. Results saved to {out_path}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
