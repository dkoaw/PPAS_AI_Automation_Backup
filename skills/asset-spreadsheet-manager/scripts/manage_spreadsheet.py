# -*- coding: utf-8 -*-
import os
import json
import csv
import sys
import io
import subprocess
import codecs

# Import Excel libraries
try:
    import xlsxwriter
    import openpyxl
except ImportError:
    pass

def run_sg_query(project_name):
    """调用 sg-data-reader 逻辑获取资产任务状态"""
    query_in = {
        "action": "raw_query",
        "entity_type": "Task",
        "filters": [
            ["project.Project.name", "is", project_name],
            ["entity.Asset.sg_asset_type", "in", ["chr", "prp", "env"]],
            ["content", "in", ["texMaster", "rigMaster", "facialTex", "lightMap", "libRig", "libMaster"]]
        ],
        "fields": ["entity", "content", "sg_status_list", "entity.Asset.sg_asset_type"]
    }
    
    tmp_in = "X:/AI_Automation/.gemini/tmp/sg_batch_query_in.json"
    tmp_out = "X:/AI_Automation/.gemini/tmp/sg_batch_query_out.json"
    
    with io.open(tmp_in, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(query_in, ensure_ascii=False)))
        
    sg_script = "X:/AI_Automation/.gemini/skills/sg-data-reader/scripts/sg_query.py"
    blender_path = "C:/Program Files/Blender Foundation/Blender 5.0/blender.exe"
    
    env = {str(k): str(v) for k, v in os.environ.items()}
    env["SG_QUERY_IN"] = str(tmp_in)
    env["SG_QUERY_OUT"] = str(tmp_out)
    
    subprocess.call([blender_path, "-b", "-P", sg_script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if os.path.exists(tmp_out):
        with io.open(tmp_out, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('data', [])
    return []

def manage_table(project_name):
    spreadsheet_dir = os.path.join("X:/AI_Automation/Project", project_name, "work", "spreadsheet")
    if not os.path.exists(spreadsheet_dir):
        os.makedirs(spreadsheet_dir)
        
    file_path_xlsx = os.path.join(spreadsheet_dir, u"{}_资产入库管理表.xlsx".format(project_name))
    
    if os.path.exists(file_path_xlsx):
        print(u"检测到现有表格，进入【增量更新模式】...")
    else:
        print(u"未检测到对应表格，进入【初始化创建模式】...")
    
    print("Querying ShotGrid for project: {}...".format(project_name))
    sg_tasks = run_sg_query(project_name)
    
    sg_map = {}
    for task in sg_tasks:
        asset_name = task['entity']['name']
        task_name = task['content']
        status = task['sg_status_list']
        asset_type = task.get('entity.Asset.sg_asset_type', 'unknown')
        if asset_name not in sg_map:
            sg_map[asset_name] = {"type": asset_type}
        sg_map[asset_name][task_name] = status

    # 标准表头
    headers = [u"资产类型", u"资产名称", u"texMaster", u"rigMaster", u"facialTex", u"lightMap", u"QC_step_1", u"灯光文件制作", u"libRig", u"QC_step_2", u"libMaster"]
    
    # 定义 Flow (ShotGrid) 的标准状态下拉列表
    # 根据常规项目配置，包含：等待、就绪、进行中、完成、审核通过、发布、临时发布、暂停、遗弃、重做
    status_list = [u"wtg", u"rdy", u"ip", u"fin", u"apr", u"pub", u"tmpub", u"rtk", u"hld", u"omt"]
    
    existing_data = []
    if os.path.exists(file_path_xlsx):
        try:
            wb = openpyxl.load_workbook(file_path_xlsx)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if rows:
                file_headers = [unicode(h) if h else u"" for h in rows[0]]
                for r in rows[1:]:
                    row_dict = {}
                    for i, val in enumerate(r):
                        if i < len(file_headers) and file_headers[i]:
                            row_dict[file_headers[i]] = val
                    existing_data.append(row_dict)
                for h in file_headers:
                    if h and h not in headers:
                        headers.append(h)
        except Exception as e:
            print("Warning: Failed to read existing XLSX: {}".format(e))

    final_rows = []
    processed_assets = set()
    
    for row in existing_data:
        asset_name = row.get(u"资产名称")
        if asset_name in sg_map:
            row[u"texMaster"] = sg_map[asset_name].get("texMaster", row.get(u"texMaster", u""))
            row[u"rigMaster"] = sg_map[asset_name].get("rigMaster", row.get(u"rigMaster", u""))
            row[u"facialTex"] = sg_map[asset_name].get("facialTex", row.get(u"facialTex", u""))
            processed_assets.add(asset_name)
        final_rows.append(row)
        
    for asset_name in sorted(sg_map.keys()):
        if asset_name not in processed_assets:
            info = sg_map[asset_name]
            new_row = {h: u"" for h in headers}
            new_row[u"资产类型"] = info["type"]
            new_row[u"资产名称"] = asset_name
            new_row[u"texMaster"] = info.get("texMaster", u"")
            new_row[u"rigMaster"] = info.get("rigMaster", u"")
            new_row[u"facialTex"] = info.get("facialTex", u"")
            new_row[u"lightMap"] = info.get("lightMap", u"")
            new_row[u"libRig"] = info.get("libRig", u"")
            new_row[u"libMaster"] = info.get("libMaster", u"")
            final_rows.append(new_row)

    try:
        workbook = xlsxwriter.Workbook(file_path_xlsx)
        worksheet = workbook.add_worksheet("Assets")
        
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        data_format = workbook.add_format({'border': 1})
        
        # 写入表头
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
            
        # 写入数据并设置下拉菜单
        for row_num, row_data in enumerate(final_rows):
            excel_row = row_num + 1
            for col_num, header in enumerate(headers):
                val = row_data.get(header, u"")
                worksheet.write(excel_row, col_num, val, data_format)
                
                # 为任务状态列添加数据验证（下拉列表）
                # 排除 "资产类型" 和 "资产名称" 
                if header not in [u"资产类型", u"资产名称"]:
                    worksheet.data_validation(excel_row, col_num, excel_row, col_num, {
                        'validate': 'list',
                        'source': status_list,
                        'input_title': u'选择状态',
                        'input_message': u'请从下拉列表中选择 Flow 标准状态',
                        'error_title': u'输入无效',
                        'error_message': u'非法状态！请务必使用 Flow 预设的状态代码。'
                    })
        
        # 设置列宽以便阅读
        worksheet.set_column(0, 0, 10) # 资产类型
        worksheet.set_column(1, 1, 25) # 资产名称
        worksheet.set_column(2, len(headers)-1, 15) # 任务列
        
        # 添加筛选功能
        if final_rows:
            worksheet.autofilter(0, 0, len(final_rows), len(headers) - 1)
            
        workbook.close()
        print("Table updated with Dropdown Lists and saved: {}".format(file_path_xlsx.encode('gbk')))
    except Exception as e:
        print("Error writing XLSX: {}".format(e))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    manage_table(sys.argv[1])
