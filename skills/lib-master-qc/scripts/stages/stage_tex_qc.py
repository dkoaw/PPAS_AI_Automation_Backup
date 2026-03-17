# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import io
import json
import sys

# --- Skill Path Injection ---
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FILE_OPS_PATH = os.path.join(SKILLS_DIR, "pipeline-file-ops", "scripts")
if FILE_OPS_PATH not in sys.path:
    sys.path.insert(0, FILE_OPS_PATH)

import file_ops

def run(res, project_name, blender_path, fixer_script, qc_script, screenshot_script, info_exporter, info_comparator):
    """
    Production texQC Stage Logic (Mirrored Black Box Principle)
    Includes:
    1. Fixer (Atomic Fixes)
    2. Screenshots
    3. Automated Atom QC (23 items)
    4. Architectural Fingerprint Comparison (New vs Prev version)
    """
    print('[Stage: Production texQC] Checking ' + str(res.name))
    
    # --- 1. Source Detection ---
    src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"tex\texMaster")
    latest = file_ops.get_latest_file(src_dir, "ysj_" + res.type + "_" + res.name + "_tex_texMaster_v*.blend")
    if not latest:
        print("  [texQC] ERROR: No work file found in: " + src_dir)
        return

    # --- 2. Workspace Setup ---
    qc_internal_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, r"tex\QC")
    if not os.path.exists(qc_internal_dir): os.makedirs(qc_internal_dir)
    else:
        for f in os.listdir(qc_internal_dir):
            if f.endswith(".blend") or f.endswith(".json") or f.endswith(".png") or f.endswith(".md"):
                try: os.remove(os.path.join(qc_internal_dir, f))
                except: pass
        
    dest_path = os.path.join(qc_internal_dir, os.path.basename(latest))
    shutil.copy2(latest, dest_path)
    
    # --- 3. Run Fixer & Generate _fixed.blend ---
    # --- [Pre-Clean] ---
    fixed_path = dest_path.replace(".blend", "_fixed.blend")
    file_ops.pre_clean_stale_files(fixed_path)
    
    env = {str(k): str(v) for k, v in os.environ.items()}
    subprocess.call([blender_path, "-b", dest_path, "-y", "-P", fixer_script], env=env)
    
    # Post-Clean/Finalize
    file_ops.post_clean_atomic_save(fixed_path)
    
    if not os.path.exists(fixed_path):
        print("  [texQC] ERROR: Fixer failed.")
        return

    # --- 4. Screenshots ---
    env['BLENDER_SHOT_OUT'] = str(qc_internal_dir); env['BLENDER_ASSET_NAME'] = str(res.name)
    subprocess.call([blender_path, fixed_path, "-y", "--python", screenshot_script], env=env)
    
    # --- 5. Automated Atom QC (tex profile) ---
    qc_out = os.path.join(qc_internal_dir, "tex_qc_out.json")
    env["QC_STEP_NAME"] = "tex"; env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([blender_path, "-b", fixed_path, "-y", "-P", qc_script], env=env)

    # --- 6. [NEW] Architectural Comparison (New vs Prev) ---
    comparison_pass = True
    promo_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, r"tex\texMaster")
    curr_v_name = os.path.basename(latest)
    prev_v_path = file_ops.get_previous_version(src_dir, curr_v_name)
    
    if prev_v_path:
        print("  [texQC] Running architectural comparison vs: " + os.path.basename(prev_v_path))
        curr_info = os.path.join(qc_internal_dir, "curr_info.json")
        prev_info = os.path.join(qc_internal_dir, "prev_info.json")
        comp_report = os.path.join(qc_internal_dir, "version_compare_report.md")
        
        # Export Current
        env["EXTRACT_INFO_OUT"] = str(curr_info)
        subprocess.call([blender_path, "-b", fixed_path, "-y", "-P", info_exporter], env=env)
        
        # Export Previous
        env["EXTRACT_INFO_OUT"] = str(prev_info)
        subprocess.call([blender_path, "-b", prev_v_path, "-y", "-P", info_exporter], env=env)
        
        # Compare
        if os.path.exists(curr_info) and os.path.exists(prev_info):
            subprocess.call(["python", info_comparator, curr_info, prev_info, comp_report])
            if os.path.exists(comp_report):
                with io.open(comp_report, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if u"结论：资产核心数据存在差异" in content:
                        print("  [texQC] WARNING: Architectural discrepancies found between versions!")
                        comparison_pass = False # Optional: strict or warning? User likes "Black Box" control.
                    else:
                        print("  [texQC] PASS: Architectural consistency verified.")
    else:
        print("  [texQC] No previous version found in mirrored space. Skipping comparison.")

    # --- 7. Final Promotion ---
    try:
        if os.path.exists(qc_out):
            with io.open(qc_out, 'r', encoding='utf-8') as f:
                data = json.load(f); failed = [i for i in data if i.get("status") == "FAIL"]
                if not failed and comparison_pass:
                    print("  [texQC] FINAL PASS: Promoting to mirrored texMaster.")
                    if not os.path.exists(promo_dir): os.makedirs(promo_dir)
                    final_dest = os.path.join(promo_dir, os.path.basename(dest_path))
                    shutil.copy2(fixed_path, final_dest)
                    print("  [texQC] SUCCESS: Cleaned file promoted to: " + final_dest)
                elif not comparison_pass:
                    print("  [texQC] BLOCKED: Architectural comparison failed. Check 'version_compare_report.md' in QC folder.")
                else:
                    print("  [texQC] FAIL: Atom QC failed.")
        else: print("  [texQC] ERROR: QC output missing")
    except Exception as e: print("  [texQC] Final error: " + str(e))

    # --- 8. Cleanup ---
    try:
        if os.path.exists(dest_path): os.remove(dest_path)
        if os.path.exists(fixed_path): os.remove(fixed_path)
    except: pass
