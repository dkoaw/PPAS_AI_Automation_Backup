# -*- coding: utf-8 -*-
import os, time, codecs, subprocess

def run(project_name, results, spreadsheet_path):
    """
    Reporting for Tex Production Pipeline.
    Writes back to the specialized Tex Management Spreadsheet.
    """
    print('[Stage: Tex Reporting] Finalizing...')
    
    ups = []
    rpt = [u'# Tex Production QC Report', u'Time: ' + unicode(time.strftime('%Y-%m-%d %H:%M:%S')) + u'\n']
    
    active_results = [r for r in results if r.tex_qc_res != "SKIP"]
    if not active_results:
        rpt.append(u'No assets required QC in this run.')
    else:
        for res in active_results:
            rpt.append(u'## Asset: ' + unicode(res.name))
            if res.tex_qc_res == "PASS":
                # Write back 'fin' to 'texQC' column
                ups.append((res.name, "texQC", "fin"))
                rpt.append(u'### Status: ✅ PASS (Mirrored & Cleaned)')
            else:
                # Write back 'rtk' to 'texQC' column
                ups.append((res.name, "texQC", "rtk"))
                rpt.append(u'### Status: ❌ FAIL (Retake required)')
            rpt.append(u'---')

    # Batch Writeback to the CHOSEN spreadsheet
    if ups:
        update_script = os.path.join(os.path.dirname(__file__), "..", "batch_update_tex.py")
        payload = u";".join([unicode(a) + u"|" + unicode(c) + u"|" + unicode(v) for a, c, v in ups])
        # Use gbk for Windows subprocess arguments
        cmd = ["python", update_script.encode('gbk'), spreadsheet_path.encode('gbk'), payload.encode('gbk')]
        subprocess.call(cmd)

    # Save Report
    report_file = "tex_prod_qc_" + time.strftime("%Y_%m_%d_%H%M%S") + ".md"
    report_path = os.path.join(r"X:\AI_Automation\Project", project_name, "report", report_file)
    if not os.path.exists(os.path.dirname(report_path)): os.makedirs(os.path.dirname(report_path))
    
    with codecs.open(report_path, 'w', 'utf-8') as f:
        f.write(u"\n".join(rpt))
    
    print("Report saved: " + report_path)
    subprocess.call('start notepad++ "' + report_path + '"', shell=True)
