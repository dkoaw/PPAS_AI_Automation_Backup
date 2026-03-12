import bpy
def run(results, asset_name):
    scripts = [t.name for t in bpy.data.texts if t.name != 'PPAS_NOTE_NODE']
    results.append({"check": "Extra Scripts", "status": "FAIL" if scripts else "PASS", "issues": scripts})
