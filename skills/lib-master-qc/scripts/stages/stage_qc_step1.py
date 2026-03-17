# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import io
import json
import sys

try:
    unicode = unicode
except NameError:
    unicode = str

def get_latest_file(directory, pattern):
    import glob
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files: return None
    return max(files, key=os.path.getmtime)

def pre_clean_stale_files(fixed_path):
    if os.path.exists(fixed_path):
        try: os.remove(fixed_path)
        except: pass

def post_clean_atomic_save(fixed_path):
    if not os.path.exists(fixed_path):
        pass # Handle in main logic

def run(res, project_name, blender_path, fixer_script, qc_script, screenshot_script, info_exporter):
    """ASCII Version - Step 1 Process"""
    print('[Stage: Step 1] Processing ' + res.name)
    src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"tex\texMaster")
    latest = get_latest_file(src_dir, "ysj_" + res.type + "_" + res.name + "_tex_texMaster_v*.blend")
    if not latest:
        res.step1_res = "FAIL"; res.step1_msg = "Source missing"; return

    s1_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1")
    if not os.path.exists(s1_dir): os.makedirs(s1_dir)
    dest_path = os.path.join(s1_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libMaster.blend")
    
    # --- [AUTO-RECOVERY] ---
    # If the main file is missing but a .blend@ backup exists, restore it.
    if not os.path.exists(dest_path) and os.path.exists(dest_path + "@"):
        try: os.rename(dest_path + "@", dest_path)
        except: pass
    
    shutil.copy2(latest, dest_path)
    
    # Save Sync Metadata
    meta_path = os.path.join(s1_dir, "sync_version.json")
    meta = {"source_file": os.path.basename(latest), "source_mtime": os.path.getmtime(latest)}
    with io.open(meta_path, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(meta, indent=4)))

    # --- [Pre-Clean] ---
    fixed_path = dest_path.replace(".blend", "_fixed.blend")
    pre_clean_stale_files(fixed_path)

    env = {str(k): str(v) for k, v in os.environ.items()}
    subprocess.call([blender_path, "-b", dest_path, "-y", "-P", fixer_script], env=env)

    # --- [Post-Clean/Finalize] ---
    post_clean_atomic_save(fixed_path)
    
    env['BLENDER_SHOT_OUT'] = str(s1_dir); env['BLENDER_ASSET_NAME'] = str(res.name)
    subprocess.call([blender_path, "-b", fixed_path, "-y", "--python", screenshot_script], env=env)
    
    qc_out = os.path.join(s1_dir, "qc_out.json")
    env["QC_STEP_NAME"] = "lib_qc_step1"; env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([blender_path, "-b", fixed_path, "-y", "-P", qc_script], env=env)
    
    try:
        with io.open(qc_out, 'r', encoding='utf-8') as f:
            data = json.load(f); failed = [i for i in data if i.get("status") == "FAIL"]
            if not failed:
                res.step1_res = "PASS"
                # --- NEW: Step 2 Sync Logic (100% Source Match) ---
                base_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name)
                s2_dir = os.path.join(base_dir, "QC_step_2")
                if not os.path.exists(s2_dir): os.makedirs(s2_dir)
                dest_s2 = os.path.join(s2_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libMaster.blend")
                shutil.copy2(fixed_path, dest_s2)
                
                # Export Fingerprint Info
                env["EXTRACT_INFO_OUT"] = str(fixed_path.replace(".blend", ".json"))
                subprocess.call([blender_path, "-b", fixed_path, "-y", "-P", info_exporter], env=env)
            else:
                res.step1_res = "FAIL"
                res.qc1_fail_summary = [i['check'] + " (" + ", ".join(i['issues']) + ")" for i in failed]
    except: res.step1_res = "FAIL"
