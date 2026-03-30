# -*- coding: utf-8 -*-
import os
import subprocess
import codecs
import sys

# --- Skill Path Injection ---
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FILE_OPS_PATH = os.path.join(SKILLS_DIR, "pipeline-file-ops", "scripts")
if FILE_OPS_PATH not in sys.path:
    sys.path.insert(0, FILE_OPS_PATH)

import file_ops
from file_ops import unicode  # For Python 2/3 compatibility

def run(res, project_name, comparator_script, skills_dir, blender_path):
    """ASCII Version - libRig Fingerprint (Sync Physical File on PASS)"""
    print('[Stage: libRig] Comparing ' + res.name)
    
    rig_src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"rig\rigMaster")
    rig_inf = file_ops.get_latest_file(os.path.join(rig_src_dir, ".info"), "ysj_*.json")
    
    # --- FORCE RENEW BLENDER JSON (Avoid stale algorithm data) ---
    lib_blend = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1", project_name + "_" + res.type + "_" + res.name + "_lib_libMaster_fixed.blend")
    lib_inf = lib_blend.replace(".blend", ".json")
    if os.path.exists(lib_blend):
        info_exporter = os.path.join(skills_dir, "blender-asset-info-exporter", "scripts", "export_info.py")
        env = os.environ.copy()
        env["EXTRACT_INFO_OUT"] = str(lib_inf)
        subprocess.call([blender_path, "-b", lib_blend, "-y", "-P", info_exporter], env=env)
    
    if not (rig_inf and os.path.exists(lib_inf)):
        res.rig_res = "FAIL"
        return

    out_md = os.path.join(os.path.dirname(lib_inf), "lib_rig_diff.md")
    subprocess.call(["python", comparator_script, rig_inf, lib_inf, out_md])
    
    with codecs.open(out_md, 'r', 'utf-8') as f:
        content = f.read().upper()
        # 优先检查失败关键字
        if u'存在差异' in content or u'不一致' in content or 'MISMATCH' in content or 'DIFFERENCE' in content or u'缺少' in content:
            res.rig_res = "FAIL"
        elif 'MATCH PERFECT' in content or 'SUCCESS' in content or 'IDENTICAL' in content or u'一！致！' in content or u'完全一致' in content:
            res.rig_res = "PASS"
        else:
            res.rig_res = "FAIL"

        if res.rig_res == "PASS":
            # --- SYNC RIG FILE ONLY ON PASS (100% Source Match) ---
            rig_file = file_ops.get_latest_file(rig_src_dir, "ysj_*.m[ab]")
            if rig_file:
                rig_dst_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libRig")
                if not os.path.exists(rig_dst_dir): os.makedirs(rig_dst_dir)
                import shutil
                ext = os.path.splitext(rig_file)[1]
                dest_path = os.path.join(rig_dst_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libRig" + ext)
                shutil.copy2(rig_file, dest_path)
                
                # Save Sync Metadata
                import json, io
                meta_path = os.path.join(rig_dst_dir, "sync_version.json")
                meta = {"source_file": os.path.basename(rig_file), "source_mtime": os.path.getmtime(rig_file)}
                with io.open(meta_path, 'w', encoding='utf-8') as mf:
                    mf.write(unicode(json.dumps(meta, indent=4)))
        else:
            res.rig_res = "FAIL"
            
            # --- [KEY FIX] Write metadata even on FAIL ---
            # This prevents read_sheet.py from repeatedly flagging as 'stale'
            # (which would imply Rig was never processed, when it was, just failed)
            rig_file_for_meta = file_ops.get_latest_file(rig_src_dir, "ysj_*.m[ab]")
            if rig_file_for_meta:
                rig_dst_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libRig")
                if not os.path.exists(rig_dst_dir): os.makedirs(rig_dst_dir)
                import json, io
                meta_path = os.path.join(rig_dst_dir, "sync_version.json")
                meta = {"source_file": os.path.basename(rig_file_for_meta), "source_mtime": os.path.getmtime(rig_file_for_meta), "result": "FAIL"}
                with io.open(meta_path, 'w', encoding='utf-8') as mf:
                    mf.write(unicode(json.dumps(meta, indent=4)))
            
            abc_exp = os.path.join(skills_dir, "blender-export-abc", "scripts", "export_abc.py")
            subprocess.call([blender_path, "-b", lib_inf.replace(".json", ".blend"), "-y", "-P", abc_exp])
