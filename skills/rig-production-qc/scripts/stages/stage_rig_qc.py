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

def run(res, project_name, mayapy_path, maya_fixer_script, maya_qc_script):
    """
    Logic for Maya Rig QC (Isolated Sandbox)
    """
    print('[Stage: Rig QC] Processing ' + res.name)

    src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"rig\rigMaster")
    latest_file = get_latest_file(src_dir, "ysj_*.m[ab]")
    
    if not latest_file:
        print("  [Rig QC] ERROR: No Maya file found in " + src_dir)
        res.rig_qc_res = "FAIL"
        return

    # 1. Sandbox setup
    qc_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, "rig", "QC")
    if not os.path.exists(qc_dir): 
        os.makedirs(qc_dir)
    else:
        for f in os.listdir(qc_dir):
            if f.endswith(".ma") or f.endswith(".mb") or f.endswith(".json") or f.endswith(".md"):
                try: os.remove(os.path.join(qc_dir, f))
                except: pass
                
    sandbox_path = os.path.join(qc_dir, os.path.basename(latest_file))
    shutil.copy2(latest_file, sandbox_path)

    # 2. Maya Fixer Stage is REMOVED
    # print("  [Rig QC] Running Maya Fixer...")
    # env = {str(k): str(v) for k, v in os.environ.items()}
    # env["MAYA_FILE_PATH"] = str(sandbox_path)
    # subprocess.call([mayapy_path, maya_fixer_script], env=env)

    # fixed_filename = os.path.basename(sandbox_path).replace(".ma", "_fixed.ma").replace(".mb", "_fixed.mb")
    # fixed_path = os.path.join(qc_dir, fixed_filename)

    # Use the original downloaded file for QC
    fixed_path = sandbox_path

    if not os.path.exists(fixed_path):
        print("  [Rig QC] ERROR: File missing.")
        res.rig_qc_res = "FAIL"
        return

    # 3. Maya QC Stage (Atoms checking)    print("  [Rig QC] Running Maya QC Atoms...")
    qc_out = os.path.join(qc_dir, "rig_qc_out.json")
    env["MAYA_FILE_PATH"] = str(fixed_path)
    env["QC_STEP_NAME"] = "rig"
    env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([mayapy_path, maya_qc_script], env=env)

    # 4. Result Extraction & Report Generation
    final_res = "FAIL"
    try:
        if os.path.exists(qc_out):
            with io.open(qc_out, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    data = json.loads(content)
                else:
                    data = []

                failed = [i for i in data if i.get("status") == "FAIL"]

                # Markdown Report
                import time
                md_path = os.path.join(qc_dir, "{}_RIG_QC_Report.md".format(res.name))
                md_lines = [u"# 资产 {} Rig 质检报告".format(res.name)]
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

                if not failed:
                    final_res = "PASS"
                    # Clean mirror: if pass, mirror to local AI_Automation pub folder (Optional)      
                    print("  [Rig QC] SUCCESS: " + res.name)
        else:
            print("  [Rig QC] ERROR: qc_out.json not found!")
    except Exception as e:
        print("  [Rig QC] Final extraction error: " + str(e))
        import traceback
        traceback.print_exc()

    res.rig_qc_res = final_res

    # 5. Cleanup
    try:
        if os.path.exists(sandbox_path): os.remove(sandbox_path)
        # Keep fixed path for now for debugging if needed, or remove later.
        # if os.path.exists(fixed_path): os.remove(fixed_path)
    except: pass
