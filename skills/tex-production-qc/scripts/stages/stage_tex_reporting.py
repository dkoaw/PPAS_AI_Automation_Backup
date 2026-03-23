# -*- coding: utf-8 -*-
import os, time, codecs, subprocess

def run(project_name, run_type, results, spreadsheet_path):
    """
    Reporting for Tex & UV Production Pipeline.
    Writes back to the specialized Tex Management Spreadsheet.
    """
    print('[Stage: {} Reporting] Finalizing...'.format(run_type.upper()))
    
    ups = []
    rpt = [u'# {} Production QC Report'.format(run_type.upper()), u'Time: ' + unicode(time.strftime('%Y-%m-%d %H:%M:%S')) + u'\n']
    
    active_results = [r for r in results if r.qc_res != "SKIP"]
    if not active_results:
        rpt.append(u'No assets required QC in this run.')
    else:
        for res in active_results:
            rpt.append(u'## Asset: ' + unicode(res.name))
            
            qc_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets", res.type, res.name, run_type, "QC")
            report_path = os.path.join(qc_dir, "{}_{}_QC_Report.md".format(res.name, run_type.upper()))
            
            if res.qc_res == "PASS":
                # Write back 'fin' to appropriate column
                ups.append((res.name, run_type + "QC", "fin"))
                rpt.append(u'### Status: ✅ PASS (Mirrored & Cleaned)')
            elif res.qc_res == "NO_FILE":
                # Write back 'mis' (missing) to appropriate column
                ups.append((res.name, run_type + "QC", "mis"))
                rpt.append(u'### Status: ⚠️ NO FILE (Source missing)')
            else:
                # Write back 'rtk' to appropriate column
                ups.append((res.name, run_type + "QC", "rtk"))
                rpt.append(u'### Status: ❌ FAIL (Retake required)')
            
            if os.path.exists(report_path):
                rpt.append(u'  * 📄 {} QC Report: [Click to Open](file:///'.format(run_type.upper()) + report_path.replace("\\", "/") + u') | `' + report_path + u'`')
            
            # Find and append the _fixed.blend path
            import glob
            fixed_files = glob.glob(os.path.join(qc_dir, "*_fixed.blend"))
            if fixed_files:
                fixed_file = fixed_files[0]
                rpt.append(u'  * 📦 Cleaned File: `' + fixed_file + u'`')
                
            # Find and append the outliner screenshot
            img_files = glob.glob(os.path.join(qc_dir, "*_outliner*.png"))
            if img_files:
                # Get the most recently modified one in case there are fallbacks
                img_file = sorted(img_files, key=os.path.getmtime)[-1]
                rpt.append(u'\n#### Outliner Screenshot')
                rpt.append(u'<img src="file:///' + img_file.replace("\\", "/") + u'" width="450">\n')

            if getattr(res, "comparison_warning", ""):
                rpt.append(u'\n' + res.comparison_warning + u'\n')
                
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
