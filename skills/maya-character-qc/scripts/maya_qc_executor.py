# -*- coding: utf-8 -*-
import json
import os
import sys

# Support Python 2 (Maya 2020) and Python 3 (Maya 2022+)
try:
    import importlib.util
    USE_IMPORTLIB = True
except ImportError:
    import imp
    USE_IMPORTLIB = False

# Ensure Maya standalone is initialized
try:
    import maya.standalone
    maya.standalone.initialize(name='python')
except Exception as e:
    print("Warning: Maya standalone initialization failed: {}".format(e))

import maya.cmds as cmds

# ----------------- Configuration -----------------
SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
QC_ROOT = os.path.join(SKILLS_DIR, "maya-character-qc", "scripts")
CHECKS_DIR = os.path.join(QC_ROOT, "checks")
PROFILE_JSON = os.path.join(SKILLS_DIR, "blender-character-qc", "scripts", "qc_profiles.json")

def load_qc_profiles():
    try:
        with open(PROFILE_JSON, 'r') as f:
            return json.load(f)
    except Exception as e:
        print("[Maya QC Orchestrator] Warning: Cannot load qc_profiles.json - " + str(e))
        return {}

def extract_asset_name(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    for tag in ['chr', 'prp', 'env']:
        if tag in parts:
            idx = parts.index(tag)
            if idx + 1 < len(parts): return parts[idx + 1]
    PROJECTS = ['ysj', 'ssx']
    if parts[0].lower() in PROJECTS and len(parts) > 1:
        if parts[1].lower() in ['chr', 'prp', 'env'] and len(parts) > 2: return parts[2]
        return parts[1]
    return parts[0]

def run_check_atom(atom_name, asset_name, results):
    logic_file = os.path.join(CHECKS_DIR, "check_{}.py".format(atom_name))
    if not os.path.exists(logic_file):
        print("[Maya QC Orchestrator] Warning: Missing check module: {}".format(atom_name))
        return

    try:
        if USE_IMPORTLIB:
            spec = importlib.util.spec_from_file_location("maya_qc_atom_" + atom_name, logic_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            mod = imp.load_source("maya_qc_atom_" + atom_name, logic_file)
            
        if hasattr(mod, "run"):
            mod.run(results, asset_name)
    except Exception as e:
        print("[Maya QC Orchestrator] Error executing {}: {}".format(atom_name, e))
        results.append({"check": atom_name, "status": "ERROR", "issues": [str(e)]})

def run_full_qc(step_name, maya_file):
    profiles = load_qc_profiles()
    if step_name not in profiles:
        return [{"check": "Config Error", "status": "FAIL", "issues": ["Invalid step: {}".format(step_name)]}]

    # Load file
    try:
        cmds.file(maya_file, open=True, force=True)
    except Exception as e:
        return [{"check": "File Open", "status": "FAIL", "issues": ["Failed to open Maya file: {}".format(e)]}]

    asset_name = extract_asset_name(os.path.basename(maya_file))
    results = []

    print("--- [Maya QC Orchestrator] Starting QC ({}) for {} ---".format(step_name, asset_name))

    for atom in profiles[step_name]:
        try:
            run_check_atom(atom, asset_name, results)
            print("  [OK] Checked: {}".format(atom))
        except Exception as e:
            results.append({"check": atom, "status": "ERROR", "issues": [str(e)]})
            print("  [FAIL] {}: {}".format(atom, e))

    print("--- [Maya QC Orchestrator] Full QC Finished ---")
    return results

if __name__ == "__main__":
    try:
        step_name = os.environ.get("QC_STEP_NAME", "rig")
        out_path = os.environ.get("QC_OUT_PATH", "qc_out.json")
        maya_file = os.environ.get("MAYA_FILE_PATH")
        
        if not maya_file or not os.path.exists(maya_file):
            print("ERROR: MAYA_FILE_PATH environment variable not set or file does not exist.")
            sys.exit(1)

        qc_results = run_full_qc(step_name, maya_file)

        # Output JSON (using unicode to prevent ascii encode errors in python 2)
        import io
        with io.open(out_path, 'w', encoding='utf-8') as f:
            # json.dumps ensures ascii output by default in python 2, 
            # we use ensure_ascii=False so it outputs raw utf8 string.
            json_str = json.dumps(qc_results, ensure_ascii=False, indent=4)
            if sys.version_info[0] < 3 and isinstance(json_str, str):
                json_str = json_str.decode('utf-8')
            f.write(json_str)

        print("Maya QC completed. Results saved to {}".format(out_path))
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Graceful shutdown
        try:
            maya.standalone.uninitialize()
        except: pass
