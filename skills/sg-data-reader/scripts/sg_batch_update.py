# -*- coding: utf-8 -*-
import os, sys, json, io

# --- ShotGrid Environment Setup ---
def get_sg():
    # Use the established pipeline config path
    config_path = r"P:\pipeline\common_lib\db_bridge\api\config\sg_data.json"
    if not os.path.exists(config_path):
        # Fallback for local testing if needed
        return None
        
    with open(config_path, 'r') as r:
        api_dict = json.load(r)
    import shotgun_api3
    return shotgun_api3.Shotgun(**api_dict)

def update_sg_statuses(project_name, updates):
    """
    updates: list of dicts { "asset_name": str, "task_name": str, "status": str }
    """
    sg = get_sg()
    if not sg:
        print("Error: ShotGrid configuration not found.")
        return False

    # 1. Get Project ID
    proj = sg.find_one("Project", [["name", "is", project_name]])
    if not proj:
        print("Error: Project '{}' not found.".format(project_name))
        return False

    # Status Mapping Table
    status_map = {
        "rep": "rep",
        "apr": "apr",
        "pub": "pub",
        "tmpub": "tmpub",
        "wtg": "wtg",
        "ip": "wip",
        "fin": "fin"
    }

    for up in updates:
        asset_name = up["asset_name"]
        task_name = up["task_name"]
        raw_status = up["status"]
        
        # Translate to SG valid status
        new_status = status_map.get(raw_status, raw_status)
        
        # 2. Find the Task
        filters = [
            ["project", "is", proj],
            ["entity.Asset.code", "is", asset_name],
            ["content", "is", task_name]
        ]
        task = sg.find_one("Task", filters)
        
        if task:
            sg.update("Task", task["id"], {"sg_status_list": new_status})
            print("Successfully updated {} - {} to {}".format(asset_name, task_name, new_status))
        else:
            print("Warning: Task '{}' not found for asset '{}'".format(task_name, asset_name))
    
    return True

if __name__ == "__main__":
    import sys
    # Handle Blender arguments
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    else:
        args = sys.argv[1:]
        
    if not args:
        print("Usage: python sg_batch_update.py <payload_json>")
        sys.exit(1)
        
    input_path = args[0]
    with io.open(input_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    success = update_sg_statuses(config["project"], config["updates"])
    sys.exit(0 if success else 1)
