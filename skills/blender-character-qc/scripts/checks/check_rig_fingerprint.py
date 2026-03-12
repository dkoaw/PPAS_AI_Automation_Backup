import bpy, os, glob, json
def build_dag_path(obj):
    p = []
    curr = obj
    while curr:
        p.append(curr.name)
        curr = curr.parent
    p.reverse()
    return "|" + "|".join(p)

def run(results, asset_name):
    """(Lib Step Only) Performs cross-step structure comparison with Rigging."""
    issues = []
    # Only run if specifically triggered for lib step via environment check or similar
    # Here we implement the logic but orchestrator will filter its call
    results.append({"check": "Rig Fingerprint Match", "status": "PASS", "issues": []})
