# -*- coding: utf-8 -*-
import os
import subprocess
import codecs
import json

def run(project_name, spreadsheet_mgr, tmp_dir):
    """Sync SG to Excel and Extract to JSON (Python 2.7 Compatible)"""
    print('[Stage: Data Sync] Updating spreadsheet for ' + str(project_name))
    subprocess.call(["python", spreadsheet_mgr, project_name])
    subprocess.call(["python", os.path.join(tmp_dir, "read_sheet.py"), project_name])
    data_path = os.path.join(tmp_dir, "spreadsheet_data.json")
    if os.path.exists(data_path):
        with codecs.open(data_path, 'r', 'utf-8') as f:
            return json.load(f)
    return []
