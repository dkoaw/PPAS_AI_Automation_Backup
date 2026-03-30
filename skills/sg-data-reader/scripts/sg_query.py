import sys
import json
import os
import traceback

def get_sg():
    with open(r"X:\AI_Automation\.gemini\env_core\sg_data.json", 'r') as r:
        api_dict = json.load(r)
    import shotgun_api3
    return shotgun_api3.Shotgun(**api_dict)

def execute_query(sg, query_config):
    action = query_config.get("action")
    project_name = query_config.get("project_name")
    
    if not action:
        return {"status": "error", "message": "Missing 'action' in query config."}

    # Helper to get project
    def get_project(p_name):
        return sg.find_one("Project", [["name", "is", p_name]], ["id", "name"])

    try:
        if action == "find_project":
            proj = get_project(project_name)
            return {"status": "success", "data": proj}
            
        elif action == "find_assets":
            proj = get_project(project_name)
            if not proj: return {"status": "error", "message": "Project {} not found".format(project_name)}
            
            filters = [["project", "is", proj]]
            asset_type = query_config.get("asset_type") # e.g. 'chr', 'prp'
            if asset_type:
                filters.append(["sg_asset_type", "is", asset_type])
                
            fields = ["id", "code", "sg_asset_type", "description"]
            assets = sg.find("Asset", filters, fields)
            return {"status": "success", "data": assets}
            
        elif action == "find_tasks":
            proj = get_project(project_name)
            if not proj: return {"status": "error", "message": "Project {} not found".format(project_name)}
            
            entity_type = query_config.get("entity_type") # "Asset" or "Shot"
            entity_name = query_config.get("entity_name")
            
            # Find the entity first
            entity_filters = [["project", "is", proj], ["code", "is", entity_name]]
            entity = sg.find_one(entity_type, entity_filters, ["id", "code"])
            
            if not entity: return {"status": "error", "message": "{} {} not found in project {}".format(entity_type, entity_name, project_name)}
            
            task_filters = [["entity", "is", entity]]
            
            # Filter by step if provided
            step_short_name = query_config.get("step")
            if step_short_name:
                step = sg.find_one("Step", [["short_name", "is", step_short_name]], ["id", "short_name"])
                if step:
                    task_filters.append(["step", "is", step])
                    
            fields = ["id", "content", "step", "sg_status_list", "task_assignees", "start_date", "due_date"]
            tasks = sg.find("Task", task_filters, fields)
            return {"status": "success", "data": tasks, "entity": entity}
            
        elif action == "raw_query":
            # For ultimate flexibility
            entity_type = query_config.get("entity_type")
            filters = query_config.get("filters", [])
            fields = query_config.get("fields", [])
            limit = query_config.get("limit", 0)
            
            data = sg.find(entity_type, filters, fields, limit=limit)
            return {"status": "success", "data": data}
            
        else:
            return {"status": "error", "message": "Unknown action: {}".format(action)}
            
    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}


if __name__ == "__main__":
    in_path = os.environ.get("SG_QUERY_IN")
    out_path = os.environ.get("SG_QUERY_OUT")
    
    if not in_path or not out_path:
        print("Missing SG_QUERY_IN or SG_QUERY_OUT environment variables.")
        sys.exit(1)
        
    try:
        with open(in_path, 'r', encoding='utf-8') as f:
            query_config = json.load(f)
            
        sg = get_sg()
        result = execute_query(sg, query_config)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        error_result = {"status": "error", "message": str(e), "traceback": traceback.format_exc()}
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, ensure_ascii=False, indent=4)
        sys.exit(1)
