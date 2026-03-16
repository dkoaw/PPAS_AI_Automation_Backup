# -*- coding: utf-8 -*-
import os
import subprocess
import codecs

def get_latest_file(directory, pattern):
    import glob
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files: return None
    return max(files, key=os.path.getmtime)

def run(res, project_name, comparator_script, skills_dir, blender_path):
    """ASCII Version - libRig Fingerprint (Sync Physical File on PASS)"""
    print('[Stage: libRig] Comparing ' + str(res.name))
    
    rig_src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"rig\rigMaster")
    rig_inf = get_latest_file(os.path.join(rig_src_dir, ".info"), "ysj_*.json")
    
    # --- FORCE RENEW BLENDER JSON (Avoid stale algorithm data) ---
    lib_blend = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1", str(project_name) + "_" + str(res.type) + "_" + str(res.name) + "_lib_libMaster_fixed.blend")
    lib_inf = lib_blend.replace(".blend", ".json")
    if os.path.exists(lib_blend):
        info_exporter = os.path.join(skills_dir, "blender-asset-info-exporter", "scripts", "export_info.py")
        env = os.environ.copy()
        env["EXTRACT_INFO_OUT"] = str(lib_inf)
        subprocess.call([blender_path, "-b", lib_blend, "-P", info_exporter], env=env)
    
    if not (rig_inf and os.path.exists(lib_inf)):
        res.rig_res = "FAIL"
        return

    out_md = os.path.join(os.path.dirname(lib_inf), "lib_rig_diff.md")
    subprocess.call(["python", comparator_script, rig_inf, lib_inf, out_md])
    
    with codecs.open(out_md, 'r', 'utf-8') as f:
        content = f.read().upper()
        # 兼容英文和中文的成功标志
        if 'MATCH PERFECT' in content or 'SUCCESS' in content or 'IDENTICAL' in content or u'一！致！' in content or u'完全一致' in content:
            res.rig_res = "PASS"
            
            # --- SYNC RIG FILE ONLY ON PASS (100% Source Match) ---
            rig_file = get_latest_file(rig_src_dir, "ysj_*.m[ab]")
            if rig_file:
                rig_dst_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libRig")
                if not os.path.exists(rig_dst_dir): os.makedirs(rig_dst_dir)
                import shutil
                ext = os.path.splitext(rig_file)[1]
                shutil.copy2(rig_file, os.path.join(rig_dst_dir, str(project_name) + "_" + str(res.type) + "_" + str(res.name) + "_lib_libRig" + ext))
        else:
            res.rig_res = "FAIL"
            abc_exp = os.path.join(skills_dir, "blender-export-abc", "scripts", "export_abc.py")
            subprocess.call([blender_path, "-b", lib_inf.replace(".json", ".blend"), "-P", abc_exp])
