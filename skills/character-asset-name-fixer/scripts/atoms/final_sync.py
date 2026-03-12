import bpy, os
def run(asset_name, report):
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES']:
            if obj.data:
                expected = obj.name + "Shape"
                if obj.data.name != expected: obj.data.name = expected
    for obj in bpy.data.objects:
        if obj.type in ['MESH', 'CURVE', 'CURVES', 'EMPTY']:
            loc, rot, scl = obj.location, obj.rotation_euler, obj.scale
            if not (all(abs(v)<1e-5 for v in loc) and all(abs(v)<1e-5 for v in rot) and all(abs(v-1.0)<1e-5 for v in scl)):
                report["manual_fix_needed"].append(f"Transform Not Zero: {obj.name}")
