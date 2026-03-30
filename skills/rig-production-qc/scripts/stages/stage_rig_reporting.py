# -*- coding: utf-8 -*-
import os, time, codecs, subprocess

def run(project_name, results, spreadsheet_path):
    """
    Reporting for Rig QC Pipeline.
    Writes back to the specialized Rig QC Spreadsheet.
    """
    print('[Stage: Rig QC Reporting] Finalizing...')

    ups = []
    rpt = [u'# Rig Auto QC Report', u'Time: ' + unicode(time.strftime('%Y-%m-%d %H:%M:%S')) + u'\n']

    active_results = [r for r in results if r.rig_qc_res != "SKIP"]
    if not active_results:
        rpt.append(u'No assets required Rig QC in this run.')
    else:
        for res in active_results:
            rpt.append(u'## Asset: ' + unicode(res.name))
            
            rig_qc_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, "rig", "QC")
            rig_report_path = os.path.join(rig_qc_dir, "{}_RIG_QC_Report.md".format(res.name))

            if res.rig_qc_res == "PASS":
                ups.append((res.name, "rigQC", "fin"))
                rpt.append(u'### rigQC: ✅ PASS (Mirrored & Cleaned)')
            else:
                ups.append((res.name, "rigQC", "rtk"))
                rpt.append(u'### rigQC: ❌ FAIL (Retake required)')
            
            if os.path.exists(rig_report_path):
                rpt.append(u'  * 📄 Rig QC Report: [Click to Open](file:///' + rig_report_path.replace("\\", "/") + u') | `' + rig_report_path + u'`')

            rpt.append(u'---')

    # Batch Writeback
    if ups:
        update_script = os.path.join(os.path.dirname(__file__), "..", "batch_update_rig.py")
        payload = u";".join([unicode(a) + u"|" + unicode(c) + u"|" + unicode(v) for a, c, v in ups])
        cmd = ["python", update_script.encode('gbk'), project_name.encode('gbk'), payload.encode('gbk')]
        subprocess.call(cmd)

    # Output total report
    report_file = "rig_qc_final_" + time.strftime("%Y_%m_%d_%H%M%S") + ".md"
    p = os.path.join(r"X:\AI_Automation\Project", project_name, "report", report_file)
    if not os.path.exists(os.path.dirname(p)): os.makedirs(os.path.dirname(p))
    with codecs.open(p, 'w', 'utf-8') as f: f.write(u"\n".join(rpt))
    
    # Auto Open
    subprocess.call('start "" "X:\\AI_Automation\\.gemini\\env_core\\Notepad_Portable\\notepad++.exe" "{}"'.format(p), shell=True)