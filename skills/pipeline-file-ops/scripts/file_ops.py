# -*- coding: utf-8 -*-
import os
import glob
import shutil

# --- Python 2/3 Compatibility ---
try:
    unicode = unicode
except NameError:
    unicode = str

def get_latest_file(directory, pattern):
    """
    Search for the latest modified file matching the pattern in the directory.
    """
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def pre_clean_stale_files(filepath):
    """
    Physically remove the file and its common Blender backup variants.
    """
    targets = [filepath, filepath + "@", filepath.replace(".blend", ".blend1")]
    for t in targets:
        if os.path.exists(t):
            try:
                os.remove(t)
            except Exception as e:
                print("[file_ops] WARN: Failed to remove %s: %s" % (t, e))

def post_clean_atomic_save(filepath):
    """
    Placeholder for future verification logic to ensure a file was saved correctly.
    """
    if not os.path.exists(filepath):
        print("[file_ops] ERROR: Expected file missing after save: %s" % filepath)
        return False
    return True

def get_previous_version(directory, current_basename):
    """
    Find the predecessor version of a file (e.g. looks for v001 if current is v002).
    """
    import re
    # Extract version from current: e.g. v002
    match = re.search(r'_v(\d+)\.blend', current_basename)
    if not match: return None
    curr_v = int(match.group(1))
    
    # Search for all versions
    pattern = current_basename.replace("_v" + match.group(1), "_v*")
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    
    v_files = []
    for f in files:
        m = re.search(r'_v(\d+)\.blend', f)
        if m:
            v = int(m.group(1))
            if v < curr_v:
                v_files.append((v, f))
    
    if not v_files: return None
    # Return the highest version that is less than current
    return max(v_files, key=lambda x: x[0])[1]
