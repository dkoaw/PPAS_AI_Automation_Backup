# -*- coding: utf-8 -*-
import os
import time
import codecs
import subprocess
import glob

def run(project_name, results, tmp_dir):
    """ASCII Version - Aggregate Reports (Strict 1:1 Logic)"""
    print('[Stage: Reporting] Finalizing ' + str(project_name))
    
    ups = []
    rpt = [u'# lib Auto QC Report', u'Time: ' + unicode(time.strftime('%Y-%m-%d %H:%M:%S')) + u'\n']
    
    active_results = [r for r in results if r.step1_res != "SKIP" or r.rig_res != "SKIP" or r.qc2_res != "SKIP"]
    if not active_results: active_results = results

    if not active_results:
        rpt.append(u'No assets were processed in this run.')
    else:
        for res in active_results:
            rpt.append(u'## Asset: ' + unicode(res.name))
            
            s1_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1")
            qc1_report_path = os.path.join(s1_dir, res.name + "_QC_Report.md")
            rig_diff_path = os.path.join(s1_dir, "lib_rig_diff.md")
            s2_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_2")
            qc2_report_path = os.path.join(s2_dir, res.name + "_QC_Report.md")
            
            # --- QC1 Status ---
            if res.step1_res == "PASS":
                ups.append((res.name, "QC_step_1", res.tex_status))
                rpt.append(u'### QC1: ✅ PASS')
            elif res.step1_res == "FAIL":
                ups.append((res.name, "QC_step_1", "rtk"))
                rpt.append(u'### QC1: ❌ FAIL')
                for msg in res.qc1_fail_summary:
                    rpt.append(u'  * ' + unicode(msg))
            else:
                status = res.qc1_existing if res.qc1_existing else "wtg"
                rpt.append(u'### QC1: ℹ️ SKIP (Already ' + unicode(status) + u')')
            
            if os.path.exists(qc1_report_path):
                rpt.append(u'  * 📄 QC1 Report: [Click to Open](file:///' + qc1_report_path.replace("\\", "/") + u') | `' + qc1_report_path + u'`')
            
            # --- Rig Sync Status ---
            if res.rig_res == "PASS": 
                ups.append((res.name, "libRig", res.rig_status))
                rpt.append(u'### libRig: ✅ PASS')
            elif res.rig_res == "FAIL": 
                ups.append((res.name, "libRig", "rtk"))
                rpt.append(u'### libRig: ⚠️ FAIL (ABC Exported)')
            else:
                if res.type in ['env', u'env']:
                    rpt.append(u'### libRig: ⚪ N/A (Static Environment)')
                else:
                    if res.rig_status in ['pub', 'tmpub']:
                        rpt.append(u'### libRig: ✅ Done (Already ' + unicode(res.librig_existing) + u')')
                    else:
                        rpt.append(u'### libRig: ⏳ WAIT (Waiting for Rig Release)')

            if os.path.exists(rig_diff_path):
                rpt.append(u'  * 📄 Rig Diff Report: [Click to Open](file:///' + rig_diff_path.replace("\\", "/") + u') | `' + rig_diff_path + u'`')

            # --- QC2 Status ---
            if res.qc2_res == "PASS":
                ups.append((res.name, "QC_step_2", res.qc2_target_status))
                ups.append((res.name, "libMaster", "apr"))
                rpt.append(u'### QC2: ✅ PASS (Ready for Final Release -> libMaster: apr)')
                
                # Physical File Promotion (chr)
                src_fixed = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_2", project_name + "_" + res.type + "_" + res.name + "_lib_libMaster_fix.blend")
                work_libmaster_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libMaster")
                if not os.path.exists(work_libmaster_dir): os.makedirs(work_libmaster_dir)
                final_dest = os.path.join(work_libmaster_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libMaster.blend")
                if os.path.exists(src_fixed):
                    import shutil
                    shutil.copy2(src_fixed, final_dest)
                    rpt.append(u'  * 📦 Promoted clean master file to work/libMaster')
                    
            elif res.qc2_res == "SKIP":
                status = res.qc2_existing if res.qc2_existing else "wtg"
                rpt.append(u'### QC2: ℹ️ SKIP (Already ' + unicode(status) + u' or Conditions not met)')
                
                # [Self-Healing]
                if res.type in ['chr', u'chr'] and status in ['pub', 'tmpub']:
                    src_fixed = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_2", project_name + "_" + res.type + "_" + res.name + "_lib_libMaster_fix.blend")
                    work_libmaster_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libMaster")
                    final_dest = os.path.join(work_libmaster_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libMaster.blend")
                    if not os.path.exists(final_dest) and os.path.exists(src_fixed):
                        import shutil
                        if not os.path.exists(work_libmaster_dir): os.makedirs(work_libmaster_dir)
                        shutil.copy2(src_fixed, final_dest)
                        rpt.append(u'  * 📦 [Self-Heal] Promoted missing master file')
            
            if os.path.exists(qc2_report_path):
                rpt.append(u'  * 📄 QC2 Report: [Click to Open](file:///' + qc2_report_path.replace("\\", "/") + u') | `' + qc2_report_path + u'`')

            # --- Promotion Rule: prp ---
            if res.type in ['prp', u'prp'] and res.lib_master_status != 'apr':
                qc1_done = (res.step1_res == "PASS" or res.qc1_existing == res.tex_status) and res.tex_status in ['pub', 'tmpub']
                librig_done = (res.rig_res == "PASS" or res.librig_existing == res.rig_status) and res.rig_status in ['pub', 'tmpub']
                if qc1_done and librig_done:
                    ups.append((res.name, "libMaster", "apr"))
                    rpt.append(u'### libMaster: ✅ Auto-APR (QC1 & Rig Sync Finished)')
                    
                    src_fixed = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1", project_name + "_" + res.type + "_" + res.name + "_lib_libMaster_fixed.blend")
                    work_libmaster_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libMaster")
                    final_dest = os.path.join(work_libmaster_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libMaster.blend")
                    if os.path.exists(src_fixed):
                        import shutil
                        if not os.path.exists(work_libmaster_dir): os.makedirs(work_libmaster_dir)
                        shutil.copy2(src_fixed, final_dest)
                        rpt.append(u'  * 📦 Promoted clean master file to work/libMaster')
            elif res.type in ['prp', u'prp'] and res.lib_master_status == 'apr':
                src_fixed = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1", project_name + "_" + res.type + "_" + res.name + "_lib_libMaster_fixed.blend")
                work_libmaster_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "libMaster")
                final_dest = os.path.join(work_libmaster_dir, project_name + "_" + res.type + "_" + res.name + "_lib_libMaster.blend")
                if not os.path.exists(final_dest) and os.path.exists(src_fixed):
                    import shutil
                    if not os.path.exists(work_libmaster_dir): os.makedirs(work_libmaster_dir)
                    shutil.copy2(src_fixed, final_dest)
                    rpt.append(u'  * 📦 [Self-Heal] Promoted missing master file (prp)')

            # --- Screenshots ---
            s1_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1")
            imgs = glob.glob(os.path.join(s1_dir, res.name + "_outliner*.png"))
            if imgs:
                latest_img = max(imgs, key=os.path.getmtime)
                uri = u"file:///" + unicode(latest_img.replace("\\", "/"))
                rpt.append(u"\n#### Outliner Screenshot\n" + u'<img src="' + uri + u'" width="450">')

            rpt.append(u'\n---')
        
    if ups:
        bs = os.path.join(tmp_dir, "batch_update_cells.py")
        payload = u";".join([unicode(a) + u"|" + unicode(c) + u"|" + unicode(v) for a, c, v in ups])
        subprocess.call(["python", bs, str(project_name), payload.encode('utf-8')])

    report_file = "lib_qc_final_" + time.strftime("%Y_%m_%d_%H%M%S") + ".md"
    p = os.path.join(r"X:\AI_Automation\Project", project_name, "report", report_file)
    if not os.path.exists(os.path.dirname(p)): os.makedirs(os.path.dirname(p))
    with codecs.open(p, 'w', 'utf-8') as f: f.write(u"\n".join(rpt))
    subprocess.call('start notepad++ "' + p + '"', shell=True)
