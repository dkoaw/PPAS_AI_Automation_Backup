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
from file_ops import unicode  # For Python 2/3 compatibility

def run(res, project_name, blender_path, fixer_script, qc_script, screenshot_script, info_exporter):
    """ASCII Version - Step 1 Process"""
    print('[Stage: Step 1] Processing ' + res.name)
    src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"tex\texMaster")
    latest = file_ops.get_latest_file(src_dir, "ysj_" + res.type + "_" + res.name + "_tex_texMaster_v*.blend")
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
    file_ops.pre_clean_stale_files(fixed_path)

    env = {str(k): str(v) for k, v in os.environ.items()}
    subprocess.call([blender_path, "-b", dest_path, "-y", "-P", fixer_script], env=env)

    # --- [Post-Clean/Finalize] ---
    file_ops.post_clean_atomic_save(fixed_path)
    
    env['BLENDER_SHOT_OUT'] = str(s1_dir); env['BLENDER_ASSET_NAME'] = str(res.name)
    subprocess.call([blender_path, "-b", fixed_path, "-y", "--python", screenshot_script], env=env)
    
    qc_out = os.path.join(s1_dir, "qc_out.json")
    env["QC_STEP_NAME"] = "lib_qc_step1"; env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([blender_path, "-b", fixed_path, "-y", "-P", qc_script], env=env)
    
    try:
        with io.open(qc_out, 'r', encoding='utf-8') as f:
            data = json.load(f); failed = [i for i in data if i.get("status") == "FAIL"]
            
            # --- Generate Markdown Report ---
            import time
            md_path = os.path.join(s1_dir, res.name + "_QC_Report.md")
            md_lines = [u"# 资产 {} QC_step_1 质检报告".format(res.name)]
            md_lines.append(u"生成时间: " + unicode(time.strftime("%Y-%m-%d %H:%M:%S")))
            md_lines.append(u"\n## 质检结果: " + (u"✅ PASS" if not failed else u"❌ FAIL"))
            if failed:
                md_lines.append(u"\n### ❌ 错误项详情:")
                for item in failed:
                    md_lines.append(u"#### " + unicode(item.get("check", "Unknown")))
                    for issue in item.get("issues", []):
                        md_lines.append(u"  - " + unicode(issue))
            with io.open(md_path, 'w', encoding='utf-8') as mf:
                mf.write(u"\n".join(md_lines))
            # --------------------------------
            
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
