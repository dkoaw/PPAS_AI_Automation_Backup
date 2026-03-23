# -*- coding: utf-8 -*-
import os, sys, json, codecs, time, imp, subprocess, io

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
TMP_DIR = r"X:\AI_Automation\.gemini\tmp"
TEX_SKILL_DIR = os.path.join(SKILLS_DIR, "tex-production-qc")
STAGES_DIR = os.path.join(TEX_SKILL_DIR, "scripts", "stages")

BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
FIXER_SCRIPT = os.path.join(SKILLS_DIR, "character-asset-name-fixer", "scripts", "rename_fixer.py")
QC_SCRIPT = os.path.join(SKILLS_DIR, "blender-character-qc", "scripts", "qc_executor.py")
INFO_EXPORTER = os.path.join(SKILLS_DIR, "blender-asset-info-exporter", "scripts", "export_info.py")
SCREENSHOT_SCRIPT = os.path.join(SKILLS_DIR, "blender-screenshot", "scripts", "capture_shot.py")
COMPARATOR = os.path.join(SKILLS_DIR, "blender-asset-info-comparator", "scripts", "compare_asset_data.py")
TEX_SPREADSHEET_MGR = os.path.join(TEX_SKILL_DIR, "scripts", "manage_tex_spreadsheet.py")
class AssetResult:
    def __init__(self, asset_data):
        name = ""
        for k, v in asset_data.items():
            if k and (u"名称" in k or u"囆" in k):
                name = v
                break
        self.name = (name or "").strip()

        atype = ""
        for k, v in asset_data.items():
            if k and (u"类型" in k or u"璇" in k):
                atype = v
                break
        self.type = (atype or "chr").strip()

        self.tex_status = (asset_data.get(u"texMaster") or "").strip().lower()
        self.texqc_existing = (asset_data.get(u"texQC") or "").strip().lower()
        self.qc_res = "SKIP"
        self.errors = []

def execute_tex_pipeline(project_name, run_type="tex", target_asset=None):
    # 1. Sync Table from SG
    print("--- [Tex & UV Production Pipeline] Syncing Spreadsheet ---")
    subprocess.call(["python", TEX_SPREADSHEET_MGR, project_name])

    # 2. Read Spreadsheet Data
    spreadsheet_path = os.path.join("X:/AI_Automation/Project", project_name, "work", "spreadsheet", u"{}_Tex制作管理表.xlsx".format(project_name))

    import openpyxl
    wb = openpyxl.load_workbook(spreadsheet_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = [unicode(h) for h in rows[0]]
    raw_assets = []
    for r in rows[1:]:
        raw_assets.append({headers[i]: r[i] for i in range(len(headers))})

    # 3. Load Stage
    logic_file = os.path.join(STAGES_DIR, "stage_tex_qc.py")
    tex_qc_stage = imp.load_source("stage_tex_qc", logic_file)

    results = []
    target_list = target_asset.split(",") if target_asset else []

    print("--- [Tex & UV Production Pipeline] Processing {} for {} ---".format(run_type.upper(), project_name))
    for asset_data in raw_assets:
        name = ""
        for k, v in asset_data.items():
            if k and (u"名称" in k or u"囆" in k):
                name = v
                break

        if not name: continue
        if target_list and name not in target_list: continue

        res = AssetResult(asset_data)
        results.append(res)

        # Trigger Condition: No prerequisites. If selected, run QC.
        try:
            tex_qc_stage.run(res, project_name, run_type, BLENDER_PATH, FIXER_SCRIPT, QC_SCRIPT, SCREENSHOT_SCRIPT, INFO_EXPORTER, COMPARATOR)
        except Exception as e:
            res.errors.append(str(e))
            print("  [ERROR] " + str(name) + ": " + str(e))

    # 4. Reporting & Writeback
    reporting_logic = os.path.join(STAGES_DIR, "stage_tex_reporting.py")
    tex_reporting = imp.load_source("stage_tex_reporting", reporting_logic)
    tex_reporting.run(project_name, run_type, results, spreadsheet_path)

    print("--- [Tex & UV Production Pipeline] Finished ---")

if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "ysj"
    run_type = sys.argv[2] if len(sys.argv) > 2 else "tex"
    tgt = sys.argv[3] if len(sys.argv) > 3 else None
    execute_tex_pipeline(proj, run_type, tgt)
