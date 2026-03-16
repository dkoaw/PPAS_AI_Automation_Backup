# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import io
import json

def run(res, project_name, blender_path, qc_script):
    """
    Logic for Full QC (QC_step_2) - In-place Copy & Fix with Conditional Status
    """
    valid_states = ['pub', 'tmpub']
    
    # 1. Type Check: Only chr
    if res.type not in ['chr', u'chr']:
        res.qc2_res = "SKIP"
        return

    # 2. Condition Check
    # QC1 must be up-to-date
    qc1_ok = (res.step1_res == "PASS" or res.qc1_existing == res.tex_status) and res.tex_status in valid_states
    # Rig must be up-to-date
    rig_ok = (res.rig_res == "PASS" or res.librig_existing == res.rig_status) and res.rig_status in valid_states
    # LGT must be published
    lgt_ok = res.lgt_status in valid_states
    
    if not (qc1_ok and rig_ok and lgt_ok):
        res.qc2_res = "SKIP"
        return

    # Determine Target Status (SOP: Only both pub -> pub, otherwise tmpub)
    target_status = 'pub' if (res.tex_status == 'pub' and res.lgt_status == 'pub') else 'tmpub'
    res.qc2_target_status = target_status

    # Check if we already finished this version with this status
    if res.qc2_existing == target_status:
        res.qc2_res = "SKIP"
        return

    # 3. File Handling (SOP)
    base_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_2")
    src_name = "{}_{}_{}_lib_libMaster.blend".format(project_name, res.type, res.name)
    src_path = os.path.join(base_dir, src_name)
    
    if not os.path.exists(src_path):
        print("  [QC_step_2] ERROR: Source file missing: " + src_path)
        res.qc2_res = "SKIP"
        return

    fix_path = src_path.replace(".blend", "_fix.blend")
    # --- [Pre-Clean] Remove stale output files before each run ---
    if os.path.exists(fix_path):
        os.remove(fix_path)
    try:
        shutil.copy2(src_path, fix_path)
        print("  [QC_step_2] Copied to: " + os.path.basename(fix_path))
    except Exception as e:
        print("  [QC_step_2] File copy failed: " + str(e))
        res.qc2_res = "SKIP"
        return

    # 4. Execute QC
    qc_out = os.path.join(base_dir, "qc2_out.json")
    # Delete stale QC output so we never read last run's result on failure
    if os.path.exists(qc_out):
        os.remove(qc_out)
    env = {str(k): str(v) for k, v in os.environ.items()}
    env["QC_STEP_NAME"] = "lib_qc_step2"
    env["QC_OUT_PATH"] = str(qc_out)
    
    subprocess.call([blender_path, "-b", fix_path, "-P", qc_script], env=env)
    
    # 5. Result Extraction
    try:
        if os.path.exists(qc_out):
            with io.open(qc_out, 'r', encoding='utf-8') as f:
                data = json.load(f)
                failed = [i for i in data if i.get("status") == "FAIL"]
                if not failed:
                    res.qc2_res = "PASS"
                    print("  [QC_step_2] PASS -> Target Status: " + target_status)
                else:
                    res.qc2_res = "FAIL"
                    print("  [QC_step_2] FAIL: " + str(len(failed)) + " issues found")
        else:
            print("  [QC_step_2] ERROR: QC output missing")
            res.qc2_res = "SKIP"
    except Exception as e:
        print("  [QC_step_2] Result extraction error: " + str(e))
        res.qc2_res = "SKIP"
