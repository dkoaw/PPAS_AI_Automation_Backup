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
    
    # Filter only assets that were part of this run (either processed or targeted)
    active_results = [r for r in results if r.step1_res != "SKIP" or r.rig_res != "SKIP"]
    
    if not active_results:
        # Fallback: if targeted but everything was already done
        active_results = results

    if not active_results:
        rpt.append(u'No assets were processed in this run.')
    else:
        for res in active_results:
            rpt.append(u'## Asset: ' + unicode(res.name))
            
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
                # Show existing status if skipped
                status = res.qc1_existing if res.qc1_existing else "wtg"
                rpt.append(u'### QC1: ℹ️ SKIP (Already ' + unicode(status) + u')')

            # --- Rig Sync Status ---
            # --- Rig Sync Status (Context Aware) ---
            if res.rig_res == "PASS": 
                ups.append((res.name, "libRig", res.rig_status))
                rpt.append(u'### libRig: ✅ PASS')
            elif res.rig_res == "FAIL": 
                ups.append((res.name, "libRig", "rtk"))
                rpt.append(u'### libRig: ⚠️ FAIL (ABC Exported)')
            else:
                # Based on user's definition: chr/prp are dynamic, env is static
                if res.type in ['env', u'env']:
                    rpt.append(u'### libRig: ⚪ N/A (Static Environment)')
                else:
                    if res.rig_status in ['pub', 'tmpub']:
                        rpt.append(u'### libRig: ✅ Done (Already ' + unicode(res.librig_existing) + u')')
                    else:
                        rpt.append(u'### libRig: ⏳ WAIT (Waiting for Rig Release)')

            # --- Screenshot Finder (Self-healing) ---
            s1_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1")
            imgs = glob.glob(os.path.join(s1_dir, res.name + "_outliner*.png"))
            if imgs:
                latest_img = max(imgs, key=os.path.getmtime)
                uri = u"file:///" + unicode(latest_img.replace("\\", "/"))
                rpt.append(u"\n#### Outliner Screenshot")
                rpt.append(u'<img src="' + uri + u'" width="450">')
            
            rpt.append(u'\n---')
        
    # --- Batch Writeback ---
    if ups:
        # Note: batch_update_cells.py is now robust and glob-based, no need to regenerate here.
        bs = os.path.join(tmp_dir, "batch_update_cells.py")
        payload = u";".join([unicode(a) + u"|" + unicode(c) + u"|" + unicode(v) for a, c, v in ups])
        subprocess.call(["python", bs, str(project_name), payload.encode('utf-8')])

    # --- Save and Launch ---
    report_file = "lib_qc_final_" + time.strftime("%Y_%m_%d_%H%M%S") + ".md"
    p = os.path.join(r"X:\AI_Automation\Project", project_name, "report", report_file)
    if not os.path.exists(os.path.dirname(p)): os.makedirs(os.path.dirname(p))
    
    with codecs.open(p, 'w', 'utf-8') as f:
        f.write(u"\n".join(rpt))
    
    subprocess.call('start notepad++ "' + p + '"', shell=True)
