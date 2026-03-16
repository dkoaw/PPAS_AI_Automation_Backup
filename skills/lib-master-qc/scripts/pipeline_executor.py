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
        self.name = (asset_data.get('Name') or asset_data.get(u'\u8d44\u4ea7\u540d\u79f0', u'')).strip()
        self.type = (asset_data.get('Type') or asset_data.get(u'\u8d44\u4ea7\u7c7b\u578b', u'chr')).strip()
        self.tex_status = asset_data.get('texMaster', '').strip()
        self.rig_status = asset_data.get('rigMaster', '').strip()
        self.lib_master_status = asset_data.get('libMaster', '')
        self.qc1_existing = asset_data.get('QC_step_1', '')
        self.librig_existing = asset_data.get('libRig', '')
        self.lgt_status = asset_data.get(u'\u706f\u5149\u6587\u4ef6\u5236\u4f5c', '')
        self.lgt_existing = self.lgt_status
        self.qc2_existing = asset_data.get('QC_step_2', '')
        
        # Freshness / Cascading Reset Flags
        self.is_dirty_tex = False
        self.is_dirty_lib = False
        self.force_reset_all = False
        self.force_reset_rig = False
        
        self.step1_res = ""
        self.qc1_fail_summary = []
        self.rig_res = "SKIP"
        self.qc2_res = "SKIP"
        self.screenshot_path = ""
        self.errors = []

def load_stage(module_name):
    logic_file = os.path.join(STAGES_DIR, module_name + ".py")
    return imp.load_source(module_name, logic_file)

def get_latest_filename(directory, pattern):
    import glob
    import re
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files: return None
    
    def sort_key(f):
        # Primary: Version number (_v001)
        match = re.search(r'_v(\d+)', os.path.basename(f))
        ver = int(match.group(1)) if match else 0
        # Secondary: Modification time
        mtime = os.path.getmtime(f)
        return (ver, mtime)
        
    latest_file = max(files, key=sort_key)
    return os.path.basename(latest_file)

def is_stale(res, project_name, stage="QC_step_1"):
    """Check if the physical source version/time is different from our synced version."""
    if stage == "QC_step_1":
        src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"tex\texMaster")
        pattern = "ysj_" + str(res.type) + "_" + str(res.name) + "_tex_texMaster_v*.blend"
    elif stage == "libRig":
        src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"rig\rigMaster")
        pattern = "ysj_*.m[ab]"
    else:
        return False

    # 1. Get Latest Source Filename and Mtime
    src_file = get_latest_filename(src_dir, pattern)
    if not src_file: return False # No source, can't be stale
    
    src_full_path = os.path.join(src_dir, src_file)
    src_mtime = os.path.getmtime(src_full_path)
    
    # 2. Get Last Synced Info from Metadata
    s1_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, stage)
    meta_path = os.path.join(s1_dir, "sync_version.json")
    
    if not os.path.exists(meta_path): return True # No metadata, force sync
    
    try:
        import io, json
        with io.open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            last_file = meta.get("source_file")
            last_mtime = meta.get("source_mtime", 0)
            
            # 3. Dual Check: Version String OR Content Timestamp
            return (src_file != last_file) or (src_mtime > (last_mtime + 2))
    except:
        return True

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
    qc_step2 = load_stage("stage_qc_step2")
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
        
        # --- [NEW] Freshness Detection & Cascading Logic ---
        res.is_dirty_tex = is_stale(res, project_name, "QC_step_1")
        res.is_dirty_lib = is_stale(res, project_name, "libRig")
        
        if res.is_dirty_tex:
            res.force_reset_all = True # Tex update -> Reset everything downstream
        elif res.is_dirty_lib:
            res.force_reset_rig = True # Only LibMaster update -> Reset Rig
            
        try:
            # --- Phase: QC1 (Trigger if Status mismatch OR Tex is Dirty) ---
            should_run_qc1 = (res.tex_status in ['pub', 'tmpub']) and (res.qc1_existing != res.tex_status or res.is_dirty_tex)
            
            if should_run_qc1:
                qc_step1.run(res, project_name, BLENDER_PATH, FIXER_SCRIPT, QC_SCRIPT, SCREENSHOT_SCRIPT, INFO_EXPORTER)
            
            # --- Phase: libRig (Trigger if Status mismatch OR Rig is Dirty OR Tex forced reset) ---
            should_run_rig = (res.rig_status in ['pub', 'tmpub']) and \
                             (res.librig_existing != res.rig_status or res.is_dirty_lib or res.force_reset_all)
            
            if ((res.step1_res == "PASS") or (res.qc1_existing == res.tex_status)) and should_run_rig:
                rig_sync.run(res, project_name, COMPARATOR, SKILLS_DIR, BLENDER_PATH)
            
            # --- Phase: QC2 (Full Check) ---
            qc_step2.run(res, project_name, BLENDER_PATH, QC_SCRIPT)
                
        except Exception as e:
            res.errors.append(str(e))
            print("  [ERROR] " + str(name) + ": " + str(e))

    reporting.run(project_name, results, TMP_DIR)
    print("--- [Pipeline V2.0] All Phases Finished ---")

if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "ysj"
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    execute_pipeline(proj, tgt)
