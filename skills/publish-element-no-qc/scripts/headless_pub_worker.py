# -*- coding: utf-8 -*-
import sys
import os
import io
import json

# Setup Blender paths
try:
    sys.path.append(r'P:\pipeline\python39_python_lib')
    sys.path.append(r'P:\pipeline\ppas')
except:
    pass

import bpy
from dayu_path import DayuPath

def run_worker():
    # Parse payload
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    else:
        print("Error: No payload arguments passed")
        sys.exit(1)
        
    payload_file = args[0]
    with io.open(payload_file, 'r', encoding='utf-8') as f:
        payload = json.load(f)
        
    target_blend = payload.get("target_blend")
    is_publish_mat = payload.get("is_publish_mat", False)
    is_2k = payload.get("is_2k", False)
    project = payload.get("project", "")
    asset_type = payload.get("asset_type", "chr")
    asset = payload.get("asset_name", "")
    module = payload.get("module", "tex")
    
    print(">>> Headless Publish Worker Start: " + target_blend)
    
    from app._blender.api.api_until import tex_publish
    from app._blender.api.api_until import mesh_info_until
    import importlib
    importlib.reload(tex_publish)
    importlib.reload(mesh_info_until)

    # 1. Texture Relocation & Save
    if is_publish_mat:
        local_source = r'S:\Project\{project}\sourceimages'.format(project=project)
        server_source = r'X:\Project\{project}\sourceimages'.format(project=project)
        print(">>> Publishing Texture from S: to X:")
        try:
            tex_publish.publish_texture(local_source, server_source, target_blend)
        except Exception as e:
            print(">>> Texture Publish Warning: " + str(e))
    else:
        print(">>> Saving direct blend to: " + target_blend)
        DayuPath(target_blend).parent.mkdir(parents=True)
        bpy.ops.wm.save_as_mainfile(filepath=target_blend)

    # Ensure we are operating on the targeted blend file going forward
    bpy.ops.wm.open_mainfile(filepath=target_blend)

    # 2. Mesh Info Extraction (JSON) (Only for texMaster)
    if module == "tex":
        info_file = DayuPath(target_blend).parent.child('.info').child('%s.json' % DayuPath(target_blend).stem)
        print(">>> Exporting Mesh JSON to: " + str(info_file))
        try:
            info_file.parent.mkdir(parents=True)
            mesh_info_until.export_mesh_info(str(info_file))
        except Exception as e:
            print(">>> Mesh JSON Export failed: " + str(e))
    else:
        print(">>> Module is %s, skipping Mesh JSON Export." % module)

    # 3. 2K/1K Texture Pyramid Generation
    if is_2k:
        print(">>> Generating 1K/2K pyramids...")
        try:
            master_root = r'X:/Project/{project}/sourceimages/{asset_type}/{asset}/tex/master'.format(
                project=project, asset=asset, asset_type=asset_type)
            if DayuPath(master_root).exists():
                image_2k_root = DayuPath(master_root).parent.child('master_2k')
                image_1k_root = DayuPath(master_root).parent.child('master_1k')
                tex_publish.publish_2k_image(DayuPath(master_root), image_2k_root, image_1k_root)
            else:
                # Scrape nodes for texture sources if master direct path isn't used
                file_dict = {}
                for mat in bpy.data.materials:
                    if mat.use_nodes:
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image:
                                filepath = node.image.filepath.replace('\\', '/')
                                if 'sourceimages/env/' in filepath: # original script logic
                                    try:
                                        folder_name = filepath.split('tex/master/')[-1].split('/')[0]
                                        pre_root = DayuPath(filepath.split('/%s/' % folder_name)[0]).child(folder_name)
                                        file_dict.setdefault(folder_name, pre_root)
                                    except: pass
                for _, sub_root in file_dict.items():
                    image_2k_root = DayuPath(sub_root).replace('/master/', '/master_2k/')
                    image_1k_root = DayuPath(sub_root).replace('/master/', '/master_1k/')
                    tex_publish.publish_2k_image(DayuPath(sub_root), DayuPath(image_2k_root), DayuPath(image_1k_root))
        except Exception as e:
            print(">>> 2K pyramid generation failed: " + str(e))

    print(">>> Worker Successfully Finished All Tasks!")

if __name__ == "__main__":
    try:
        run_worker()
        sys.exit(0)
    except Exception as base_e:
        print("Worker fatal error: " + str(base_e))
        sys.exit(1)
