import bpy
def run(results, asset_name):
    issues = []
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'EMPTY', 'CURVES']:
            loc, rot, scl = obj.location, obj.rotation_euler, obj.scale
            if not (all(abs(v)<1e-5 for v in loc) and all(abs(v)<1e-5 for v in rot) and all(abs(v-1.0)<1e-5 for v in scl)):
                issues.append(f"{obj.name} (Loc:{[round(v,3) for v in loc]}, Rot:{[round(v,3) for v in rot]}, Scl:{[round(v,3) for v in scl]})")
    results.append({"check": "Transform Reset", "status": "FAIL" if issues else "PASS", "issues": issues})
