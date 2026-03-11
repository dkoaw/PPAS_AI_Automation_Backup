# -*- coding: utf-8 -*-
import os
import json
import io
import sys
import codecs
import time
import shutil
import subprocess

# ----------------- 核心组件配置 -----------------
SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
TMP_DIR = r"X:\AI_Automation\.gemini\tmp"

BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
FIXER_SCRIPT = os.path.join(SKILLS_DIR, "character-asset-name-fixer", "scripts", "rename_fixer.py")
QC_SCRIPT = os.path.join(SKILLS_DIR, "blender-character-qc", "scripts", "qc_executor.py")
INFO_EXPORTER = os.path.join(SKILLS_DIR, "blender-asset-info-exporter", "scripts", "export_info.py")
SPREADSHEET_MGR = os.path.join(SKILLS_DIR, "asset-spreadsheet-manager", "scripts", "manage_spreadsheet.py")
SCREENSHOT_SCRIPT = os.path.join(SKILLS_DIR, "blender-screenshot", "scripts", "capture_shot.py")
COMPARATOR = os.path.join(SKILLS_DIR, "blender-asset-info-comparator", "scripts", "compare_asset_data.py")

# ----------------- 状态记录对象 -----------------
class AssetResult:
    def __init__(self, asset_data):
        self.name = asset_data[u'资产名称']
        self.type = asset_data.get(u'资产类型', 'chr')
        self.tex_status = asset_data.get(u'texMaster', '')
        self.rig_status = asset_data.get(u'rigMaster', '')
        self.lgt_status = asset_data.get(u'灯光文件制作', '')
        self.lib_master_status = asset_data.get(u'libMaster', '')
        self.qc1_existing = asset_data.get(u'QC_step_1', '')
        self.librig_existing = asset_data.get(u'libRig', '')
        
        self.step1_res = "SKIP"
        self.step1_msg = ""
        self.qc1_fail_summary = [] # 新增：记录 QC1 失败项
        self.rig_res = "SKIP"
        self.rig_msg = ""
        self.step2_res = "SKIP"
        self.step2_msg = ""
        self.errors = []
        self.screenshot_path = "" 

# ... (省略中间 log, get_spreadsheet_data 等函数)

def run_step_1_logic(res, project_name, asset_data):
    if res.tex_status not in ['pub', 'tmpub'] or res.lib_master_status == res.tex_status: return
    log(u"[{}] QC_step_1...".format(res.name))
    
    src_dir = os.path.join(r"X:\Project", project_name, r"pub\assets", res.type, res.name, r"tex\texMaster")
    latest = get_latest_file(src_dir, "ysj_{}_{}_tex_texMaster_v*.blend".format(res.type, res.name))
    if not latest: res.step1_res = "FAIL"; res.step1_msg = u"找不到源文件"; return
    
    s1_dir = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1")
    if not os.path.exists(s1_dir): os.makedirs(s1_dir)
    
    dest_path = os.path.join(s1_dir, u"{}_{}_{}_lib_libMaster.blend".format(project_name, res.type, res.name))
    shutil.copy2(latest, dest_path)
    
    # 1. 洗稿
    env = {str(k): str(v) for k, v in os.environ.items()}
    subprocess.call([BLENDER_PATH, "-b", dest_path, "-P", FIXER_SCRIPT], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    fixed_path = dest_path.replace(".blend", "_fixed.blend")
    
    # 2. 截图 (Active Run Only)
    capture_asset_shot(res, s1_dir, fixed_path)
    
    # 3. 质检
    qc_out = os.path.join(s1_dir, "qc_out.json")
    env["QC_STEP_NAME"] = "tex"; env["QC_OUT_PATH"] = str(qc_out)
    subprocess.call([BLENDER_PATH, "-b", fixed_path, "-P", QC_SCRIPT], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 4. 生成单体报告
    generate_individual_report(res, s1_dir, qc_out)
    
    try:
        with io.open(qc_out, 'r', encoding='utf-8') as f:
            data = json.load(f)
            failed_items = [i for i in data if i.get("status") == "FAIL"]
            if not failed_items:
                res.step1_res = "PASS"
                env["EXTRACT_INFO_OUT"] = str(fixed_path.replace(".blend", ".json"))
                subprocess.call([BLENDER_PATH, "-b", fixed_path, "-P", INFO_EXPORTER], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else: 
                res.step1_res = "FAIL"
                # 记录核心失败原因
                res.qc1_fail_summary = [u"{} ({})".format(i['check'], u", ".join(i['issues'])) for i in failed_items]
    except: res.step1_res = "FAIL"

# ... (省略中间函数)

def finalize_all(project_name, results):
    log(u"固化汇总报告...")
    ups = []; rpt = [u"# 🚀 lib 自动化入库总表", u"时间: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"))]
    
    # 仅保留本次有实际操作(非SKIP)的资产
    active_results = [r for r in results if r.step1_res != "SKIP" or r.rig_res != "SKIP" or r.step2_res != "SKIP"]
    
    if not active_results:
        rpt.append(u"### ℹ️ 本次运行无资产符合入库/质检流转条件 (全部跳过)。")
    else:
        for res in active_results:
            b = [u"## 📦 资产: `{}`".format(res.name)]
            if res.step1_res == "PASS": 
                ups.append((res.name, u"QC_step_1", res.tex_status))
                b.append(u"### 📝 初步质检 (QC1): ✅ PASS")
                sync_s2(project_name, res)
            elif res.step1_res == "FAIL": 
                ups.append((res.name, u"QC_step_1", u"rtk"))
                b.append(u"### 📝 初步质检 (QC1): ❌ FAIL (打回)")
                if res.qc1_fail_summary:
                    b.append(u"**🚨 QC1 失败详情**:")
                    for msg in res.qc1_fail_summary:
                        b.append(u"  * {}".format(msg))
            
            if res.rig_res == "PASS": 
                ups.append((res.name, u"libRig", res.rig_status))
                b.append(u"### 💍 Rig 比对: ✅ 一致 (PASS)")
                sync_rg(project_name, res)
            elif res.rig_res == "FAIL": 
                ups.append((res.name, u"libRig", u"rtk"))
                b.append(u"### 💍 Rig 比对: ⚠️ 不一致 (已导出 ABC)")
                abc_path = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1", u"{}_{}_{}_lib_libMaster.abc".format(project_name, res.type, res.name))
                b.append(u"**🚨 操作指引**: 请绑定师提取 ABC 更新 rig 文件，同步后重新发布 rigMaster。")
                b.append(u"**📂 ABC 路径**: `{}`".format(abc_path))
                
                diff_md = os.path.join(r"X:\AI_Automation\Project", project_name, r"work\assets_lib", res.type, res.name, "QC_step_1", "lib_rig_diff.md")
                if os.path.exists(diff_md):
                    with codecs.open(diff_md, 'r', 'utf-8') as df:
                        b.append(u"**📝 差异摘要**:\n```\n" + df.read()[:500] + u"\n...\n```")
            
            if res.screenshot_path:
                uri = u"file:///" + res.screenshot_path.replace("\\", "/")
                b.append(u"\n### 📸 大纲预览\n")
                b.append(u'<img src="{}" width="450">'.format(uri))
            
            rpt.append(u"\n".join(b))
            rpt.append(u"\n---")
        
    apply_batch(project_name, ups)
    p = os.path.join(r"X:\AI_Automation\Project", project_name, "report", "lib_qc_final_{}.md".format(time.strftime("%Y_%m_%d_%H%M")))
    with codecs.open(p, 'w', 'utf-8') as f: f.write(u"\n".join(rpt))
    subprocess.call('start notepad++ "{}"'.format(p.encode('gbk')), shell=True)

def apply_batch(project_name, ups):
    if not ups: return
    bs = os.path.join(TMP_DIR, "batch_update_cells.py")
    with codecs.open(bs, 'w', 'utf-8') as f:
        f.write(u'''# -*- coding: utf-8 -*-
import openpyxl, os, subprocess, sys
pn = sys.argv[1].decode('utf-8')
fp = u"X:/AI_Automation/Project/{0}/work/spreadsheet/{0}_资产入库管理表.xlsx".format(pn)
subprocess.call('attrib -r "{}"'.format(fp.encode('gbk')), shell=True)
wb = openpyxl.load_workbook(fp); ws = wb.active; hs = {c.value: i+1 for i,c in enumerate(ws[1]) if c.value}
for e in sys.argv[2].decode('utf-8').split(';'):
    if not e: continue
    a, c, v = e.split('|')
    for r in range(2, ws.max_row+1):
        ca = ws.cell(row=r, column=2).value
        if (ca if isinstance(ca, unicode) else unicode(ca) if ca else u"") == a:
            if c in hs: ws.cell(row=r, column=hs[c]).value = v
            break
wb.save(fp); subprocess.call('attrib +r "{}"'.format(fp.encode('gbk')), shell=True)
''')
    pl = u";".join([u"{}|{}|{}".format(a, c, v) for a, c, v in ups])
    subprocess.call(["python", bs, project_name.encode('utf-8'), pl.encode('utf-8')])

def sync_s2(p, r):
    b = os.path.join(r"X:\AI_Automation\Project", p, r"work\assets_lib", r.type, r.name)
    s = os.path.join(b, "QC_step_1", u"{}_{}_{}_lib_libMaster_fixed.blend".format(p, r.type, r.name))
    d = os.path.join(b, "QC_step_2")
    if not os.path.exists(d): os.makedirs(d)
    if os.path.exists(s): shutil.copy2(s, os.path.join(d, u"{}_{}_{}_lib_libMaster.blend".format(p, r.type, r.name)))

def sync_rg(p, r):
    s = get_latest_file(os.path.join(r"X:\Project", p, r"pub\assets", r.type, r.name, r"rig\rigMaster"), "ysj_*.m[ab]")
    if s:
        d = os.path.join(r"X:\AI_Automation\Project", p, r"work\assets_lib", r.type, r.name, "libRig")
        if not os.path.exists(d): os.makedirs(d)
        shutil.copy2(s, os.path.join(d, u"{}_{}_{}_lib_libRig{}".format(p, r.type, r.name, os.path.splitext(s)[1])))

if __name__ == "__main__": execute_pipeline(sys.argv[1] if len(sys.argv) > 1 else "ysj")
