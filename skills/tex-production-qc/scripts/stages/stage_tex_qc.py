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

def run(res, project_name, run_type, blender_path, fixer_script, qc_script, screenshot_script, info_exporter, info_comparator):
    """
    Isolated Production QC Stage (Mirrored Black Box)
    Handles both 'uv' and 'tex' run_types.
    """
    print('[Stage: Production {} QC] Checking {}'.format(run_type.upper(), str(res.name)))

    # 1. Source (Artist's Area)
    master_folder = run_type + "Master"
    src_dir = os.path.join(r"S:\Project", project_name, r"work\assets", res.type, res.name, run_type, master_folder)
    latest = get_latest_file(src_dir, "ysj_" + str(res.type) + "_" + str(res.name) + "_" + run_type + "_" + master_folder + "_v*.blend")
    if not latest:
        print("  [QC] ERROR: No file found in: " + src_dir)
        res.qc_res = "NO_FILE"
        res.comparison_warning = u"\n\n⚠️ **提示**: 未能找到 {} 环节的源文件！".format(run_type.upper())
        return

    # 2. Workspace (Mirrored QC Path)
    qc_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, run_type, r"QC")
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
        res.qc_res = "FAIL"
        return

    env['BLENDER_SHOT_OUT'] = str(qc_dir); env['BLENDER_ASSET_NAME'] = str(res.name)
    subprocess.call([blender_path, fixed_path, "-y", "--python", screenshot_script], env=env)

    # 4. Atom QC
    qc_out = os.path.join(qc_dir, run_type + "_qc_out.json")
    env["QC_STEP_NAME"] = str(run_type); env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([blender_path, "-b", fixed_path, "-P", qc_script], env=env)

    # 5. Architecture Comparison (Only for tex against rigMaster JSON)
    comparison_warning = ""
    if run_type == "tex":
        # Only check X drive (pub) for submitted rig info
        rig_info_dir_pub = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"rig\rigMaster\.info")
        latest_rig_json = get_latest_file(rig_info_dir_pub, "ysj_*.json")
        
        if latest_rig_json:
            curr_info = os.path.join(qc_dir, "curr_info.json")
            comp_report = os.path.join(qc_dir, "version_compare_report.md")
            
            env["EXTRACT_INFO_OUT"] = str(curr_info)
            subprocess.call([blender_path, "-b", fixed_path, "-P", info_exporter], env=env)
            
            if os.path.exists(curr_info) and os.path.exists(latest_rig_json):
                subprocess.call(["python", info_comparator, curr_info, latest_rig_json, comp_report])
                if os.path.exists(comp_report):
                    with io.open(comp_report, 'r', encoding='utf-8') as f:
                        comp_txt = f.read()
                        comparison_warning = comp_txt
        else:
            comparison_warning = u"\n\n⚠️ **警告**: 未能在上游找到对应的 Rig 绑定指纹 (JSON) 文件，无法进行拓扑比对！"
            
    res.comparison_warning = comparison_warning

    # 6. Result Evaluation & Report Generation
    res.qc_res = "FAIL"
    try:
        if os.path.exists(qc_out):
            with io.open(qc_out, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    data = json.loads(content)
                else:
                    data = []
                
                failed = [i for i in data if i.get("status") == "FAIL"]
                warnings = [i for i in data if i.get("status") == "WARNING"]

                # Markdown Report
                import time
                md_path = os.path.join(qc_dir, "{}_{}_QC_Report.md".format(res.name, run_type.upper()))
                md_lines = [u"# 资产 {} {} 质检报告".format(res.name, run_type.upper())]
                md_lines.append(u"生成时间: " + unicode(time.strftime("%Y-%m-%d %H:%M:%S")))      
                md_lines.append(u"\n## 质检结果: " + (u"✅ PASS" if not failed else u"❌ FAIL"))   
                
                if failed:
                    md_lines.append(u"\n### ❌ 错误项详情 (阻断流程):")
                    for item in failed:
                        md_lines.append(u"#### " + unicode(item.get("check", "Unknown")))
                        for issue in item.get("issues", []):
                            md_lines.append(u"  - " + unicode(issue))

                if warnings:
                    md_lines.append(u"\n### ⚠️ 提醒项详情 (不影响质检结果):")
                    for item in warnings:
                        md_lines.append(u"#### " + unicode(item.get("check", "Unknown")))
                        for issue in item.get("issues", []):
                            md_lines.append(u"  - " + unicode(issue))
                            
                with io.open(md_path, 'w', encoding='utf-8') as mf:
                    mf.write(u"\n".join(md_lines))

                if not failed:
                    res.qc_res = "PASS"
                    print("  [" + run_type.upper() + " QC] SUCCESS: " + res.name)
    except Exception as e:
        print("  [" + run_type.upper() + " QC] Final Error: " + str(e))

    # 7. Cleanup temp blends
    try:
        pass
        # Commented out so you can inspect the files:
        # if os.path.exists(dest_path): os.remove(dest_path)
        # if os.path.exists(fixed_path): os.remove(fixed_path)
    except: pass
