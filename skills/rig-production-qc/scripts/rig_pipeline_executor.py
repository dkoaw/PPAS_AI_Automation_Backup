# -*- coding: utf-8 -*-
import os, sys, imp, subprocess

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
RIG_SKILL_DIR = os.path.join(SKILLS_DIR, "rig-production-qc")
STAGES_DIR = os.path.join(RIG_SKILL_DIR, "scripts", "stages")

MAYAPY_PATH = r"C:\Program Files\Autodesk\Maya2025\bin\mayapy.exe"
MAYA_FIXER = os.path.join(SKILLS_DIR, "maya-asset-name-fixer", "scripts", "maya_fixer.py")
MAYA_QC = os.path.join(SKILLS_DIR, "maya-character-qc", "scripts", "maya_qc_executor.py")
SPREADSHEET_MGR = os.path.join(RIG_SKILL_DIR, "scripts", "manage_rig_spreadsheet.py")

class AssetResult:
    def __init__(self, asset_data):
        self.name = (asset_data.get(u"资产名称") or "").strip()
        self.type = (asset_data.get(u"资产类型") or "chr").strip()
        self.rig_status = (asset_data.get(u"rigMaster") or "").strip().lower()
        self.rigqc_existing = (asset_data.get(u"rigQC") or "").strip().lower()
        self.rig_qc_res = "SKIP"
        self.errors = []

def execute_pipeline(project_name, target_asset=None):
    print("--- [Rig Production Pipeline] Syncing Spreadsheet ---")
    subprocess.call(["python", SPREADSHEET_MGR, project_name])
    
    spreadsheet_path = os.path.join("X:/AI_Automation/Project", project_name, "work", "spreadsheet", u"{}_Rig制作管理表.xlsx".format(project_name))
    
    import openpyxl
    wb = openpyxl.load_workbook(spreadsheet_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = [unicode(h) for h in rows[0]]
    raw_assets = []
    for r in rows[1:]:
        raw_assets.append({headers[i]: r[i] for i in range(len(headers))})
    
    qc_stage_file = os.path.join(STAGES_DIR, "stage_rig_qc.py")
    qc_stage = imp.load_source("stage_rig_qc", qc_stage_file)
    
    results = []
    target_list = target_asset.split(",") if target_asset else []
    
    print("--- [Rig Production Pipeline] Processing " + project_name + " ---")
    for asset_data in raw_assets:
        name = asset_data.get(u"资产名称")
        if target_list and name not in target_list: continue
        
        res = AssetResult(asset_data)
        results.append(res)
        
        # User requested: No prerequisites. If checked in UI (in target_list), execute it.
        try:
            qc_stage.run(res, project_name, MAYAPY_PATH, MAYA_FIXER, MAYA_QC)
        except Exception as e:
            res.errors.append("RigQC Error: " + str(e))
            print("  [ERROR] " + str(name) + " (Rig QC): " + str(e))

    # Reporting Stage
    reporting_file = os.path.join(STAGES_DIR, "stage_rig_reporting.py")
    reporting_stage = imp.load_source("stage_rig_reporting", reporting_file)
    reporting_stage.run(project_name, results, spreadsheet_path)
    
    print("--- [Rig Production Pipeline] Finished ---")

if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "ysj"
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    execute_pipeline(proj, tgt)
