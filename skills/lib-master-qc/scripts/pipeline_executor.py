# -*- coding: utf-8 -*-
import os, sys, json, codecs, time, imp

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
TMP_DIR = r"X:\AI_Automation\.gemini\tmp"
STAGES_DIR = os.path.join(SKILLS_DIR, "lib-master-qc", "scripts", "stages")

BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
FIXER_SCRIPT = os.path.join(SKILLS_DIR, "character-asset-name-fixer", "scripts", "rename_fixer.py")
QC_SCRIPT = os.path.join(SKILLS_DIR, "blender-character-qc", "scripts", "qc_executor.py")
INFO_EXPORTER = os.path.join(SKILLS_DIR, "blender-asset-info-exporter", "scripts", "export_info.py")
SPREADSHEET_MGR = os.path.join(SKILLS_DIR, "asset-spreadsheet-manager", "scripts", "manage_spreadsheet.py")
SCREENSHOT_SCRIPT = os.path.join(SKILLS_DIR, "blender-screenshot", "scripts", "capture_shot.py")
COMPARATOR = os.path.join(SKILLS_DIR, "blender-asset-info-comparator", "scripts", "compare_asset_data.py")

class AssetResult:
    def __init__(self, asset_data):
        self.name = asset_data.get('Name') or asset_data.get(u'\u8d44\u4ea7\u540d\u79f0')
        self.type = asset_data.get('Type') or asset_data.get(u'\u8d44\u4ea7\u7c7b\u578b', 'chr')
        self.tex_status = asset_data.get('texMaster', '')
        self.rig_status = asset_data.get('rigMaster', '')
        self.lib_master_status = asset_data.get('libMaster', '')
        self.qc1_existing = asset_data.get('QC_step_1', '')
        self.librig_existing = asset_data.get('libRig', '')
        
        self.step1_res = "SKIP"
        self.qc1_fail_summary = []
        self.rig_res = "SKIP"
        self.screenshot_path = ""
        self.errors = []

def load_stage(module_name):
    logic_file = os.path.join(STAGES_DIR, module_name + ".py")
    return imp.load_source(module_name, logic_file)

def execute_pipeline(project_name, target_asset=None):
    try:
        data_sync = load_stage("stage_data_sync")
        raw_assets = data_sync.run(project_name, SPREADSHEET_MGR, TMP_DIR)
    except Exception as e:
        print("[ERROR] Data Sync failed: " + str(e))
        return

    if not raw_assets: return

    qc_step1 = load_stage("stage_qc_step1")
    rig_sync = load_stage("stage_rig_sync")
    reporting = load_stage("stage_reporting")

    results = []
    print("--- [Pipeline V2.0] Processing " + project_name + " ---")
    
    # ????????????????
    target_list = target_asset.split(",") if target_asset else []
    
    for asset_data in raw_assets:
        asset_type = asset_data.get('Type') or asset_data.get(u'\u8d44\u4ea7\u7c7b\u578b')
        if asset_type not in ['chr', 'prp', 'env', u'chr', u'prp', u'env']: continue
        
        name = asset_data.get('Name') or asset_data.get(u'\u8d44\u4ea7\u540d\u79f0')
        if target_list and name not in target_list: continue
        
        res = AssetResult(asset_data)
        results.append(res)
        
        try:
            if res.tex_status in ['pub', 'tmpub'] and res.qc1_existing != res.tex_status:
                qc_step1.run(res, project_name, BLENDER_PATH, FIXER_SCRIPT, QC_SCRIPT, SCREENSHOT_SCRIPT, INFO_EXPORTER)
            
            if ((res.step1_res == "PASS") or (res.qc1_existing == res.tex_status)) and \
               (res.rig_status in ['pub', 'tmpub']) and (res.librig_existing != res.rig_status):
                rig_sync.run(res, project_name, COMPARATOR, SKILLS_DIR, BLENDER_PATH)
                
        except Exception as e:
            res.errors.append(str(e))
            print("  [ERROR] " + str(name) + ": " + str(e))

    reporting.run(project_name, results, TMP_DIR)
    print("--- [Pipeline V2.0] All Phases Finished ---")

if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "ysj"
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    execute_pipeline(proj, tgt)
