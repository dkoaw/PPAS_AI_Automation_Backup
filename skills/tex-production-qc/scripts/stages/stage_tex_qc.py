# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import io
import json

def get_latest_file(directory, pattern):
    import glob
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files: return None
    return max(files, key=os.path.getmtime)

def get_previous_version(directory, current_basename):
    import glob
    import re
    match = re.search(r'_v(\d+)\.blend', current_basename)
    if not match: return None
    curr_v = int(match.group(1))
    
    pattern = current_basename.replace("_v" + match.group(1), "_v*")
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    
    v_files = []
    for f in files:
        m = re.search(r'_v(\d+)\.blend', f)
        if m:
            v = int(m.group(1))
            if v < curr_v:
                v_files.append((v, f))
    
    if not v_files: return None
    return max(v_files, key=lambda x: x[0])[1]

def run(res, project_name, blender_path, fixer_script, qc_script, screenshot_script, info_exporter, info_comparator):
    """
    Isolated Production texQC Stage (Mirrored Black Box)
    1. Atoms QC (23 items)
    2. Architecture Fingerprint Comparison (New vs Prev version)
    """
    print('[Stage: Production texQC] Checking ' + str(res.name))
    
    # 1. Source (Artist's Area)
    src_dir = os.path.join(r"X:\Project", project_name, r"work\assets", res.type, res.name, r"tex\texMaster")
    latest = get_latest_file(src_dir, "ysj_" + str(res.type) + "_" + str(res.name) + "_tex_texMaster_v*.blend")
    if not latest:
        print("  [texQC] ERROR: No file found in: " + src_dir)
        res.tex_qc_res = "FAIL"
        return

    # 2. Workspace (Mirrored QC Path)
    qc_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, r"tex\QC")
    if not os.path.exists(qc_dir): os.makedirs(qc_dir)
    else:
        for f in os.listdir(qc_dir):
            if f.endswith(".blend") or f.endswith(".json") or f.endswith(".png") or f.endswith(".md"):
                try: os.remove(os.path.join(qc_dir, f))
                except: pass
        
    dest_path = os.path.join(qc_dir, os.path.basename(latest))
    shutil.copy2(latest, dest_path)

    # 3. Fixer & Screenshots
    env = {str(k): str(v) for k, v in os.environ.items()}
    subprocess.call([blender_path, "-b", dest_path, "-P", fixer_script], env=env)
    fixed_filename = os.path.basename(dest_path).replace(".blend", "_fixed.blend")
    fixed_path = os.path.join(qc_dir, fixed_filename)
    if not os.path.exists(fixed_path):
        res.tex_qc_res = "FAIL"
        return

    env['BLENDER_SHOT_OUT'] = str(qc_dir); env['BLENDER_ASSET_NAME'] = str(res.name)
    subprocess.call([blender_path, fixed_path, "--python", screenshot_script], env=env)
    
    # 4. Atom QC
    qc_out = os.path.join(qc_dir, "tex_qc_out.json")
    env["QC_STEP_NAME"] = "tex"; env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([blender_path, "-b", fixed_path, "-P", qc_script], env=env)

    # 5. Architecture Comparison
    comparison_pass = True
    promo_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, r"tex\texMaster")
    prev_v_path = get_previous_version(promo_dir, os.path.basename(latest))
    
    if prev_v_path:
        curr_info = os.path.join(qc_dir, "curr_info.json")
        prev_info = os.path.join(qc_dir, "prev_info.json")
        comp_report = os.path.join(qc_dir, "version_compare_report.md")
        env["EXTRACT_INFO_OUT"] = str(curr_info)
        subprocess.call([blender_path, "-b", fixed_path, "-P", info_exporter], env=env)
        env["EXTRACT_INFO_OUT"] = str(prev_info)
        subprocess.call([blender_path, "-b", prev_v_path, "-P", info_exporter], env=env)
        if os.path.exists(curr_info) and os.path.exists(prev_info):
            subprocess.call(["python", info_comparator, curr_info, prev_info, comp_report])
            if os.path.exists(comp_report):
                with io.open(comp_report, 'r', encoding='utf-8') as f:
                    if u"结论：资产核心数据存在差异" in f.read():
                        comparison_pass = False

    # 6. Final Promotion (Mirror texMaster + Clean Naming)
    res.tex_qc_res = "FAIL"
    try:
        if os.path.exists(qc_out):
            with io.open(qc_out, 'r', encoding='utf-8') as f:
                failed = [i for i in json.load(f) if i.get("status") == "FAIL"]
                if not failed and comparison_pass:
                    res.tex_qc_res = "PASS"
                    if not os.path.exists(promo_dir): os.makedirs(promo_dir)
                    # Clean naming: remove _fixed
                    clean_dest = os.path.join(promo_dir, os.path.basename(dest_path))
                    shutil.copy2(fixed_path, clean_dest)
                    print("  [texQC] SUCCESS: Promoted to " + clean_dest)
    except Exception as e:
        print("  [texQC] Final Error: " + str(e))

    # 7. Cleanup temp blends
    try:
        if os.path.exists(dest_path): os.remove(dest_path)
        if os.path.exists(fixed_path): os.remove(fixed_path)
    except: pass
