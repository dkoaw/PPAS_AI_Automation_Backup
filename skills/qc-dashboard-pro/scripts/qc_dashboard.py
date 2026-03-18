# -*- coding: utf-8 -*-
import sys, os, json, io, codecs, subprocess, shutil

try:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
TMP_DIR = r"X:\AI_Automation\.gemini\tmp"
JSON_PATH = os.path.join(TMP_DIR, "spreadsheet_data.json")
SYNC_SCRIPT = os.path.join(SKILLS_DIR, "asset-spreadsheet-manager", "scripts", "manage_spreadsheet.py")
PIPELINE_SCRIPT = os.path.join(SKILLS_DIR, "lib-master-qc", "scripts", "pipeline_executor.py")
BATCH_UPDATE_SCRIPT = os.path.join(TMP_DIR, "batch_update_cells.py")
SG_UPDATE_SCRIPT = os.path.join(SKILLS_DIR, "sg-data-reader", "scripts", "sg_batch_update.py")
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

class QCDashboard(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PPAS Lib QC Dashboard Pro V4.2 - Strict Standard Mode")
        self.geometry("1600x850")
        
        self.colors = {
            'pub': '#D4EDDA', 'tmpub': '#D4EDDA', 
            'wip': '#FFF3CD', 'wtg': '#E2E3E5',
            'rep': '#F8D7DA', 'apr': '#CCE5FF', 'None': '#FFFFFF'
        }
        
        self.status_list = ["", "wtg", "rdy", "ip", "fin", "apr", "pub", "tmpub", "rep", "hld", "omt"]
        self.assets_data = []
        self.checkbox_vars = {}
        self.pending_updates = {}
        
        self.init_ui()
        
    def init_ui(self):
        top_frame = tk.Frame(self, pady=10, padx=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Project:", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT)
        self.proj_entry = tk.Entry(top_frame, width=10, font=("Microsoft YaHei", 10))
        self.proj_entry.insert(0, "ysj")
        self.proj_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="1. Sync Flow Status", bg="#007BFF", fg="white", font=("Microsoft YaHei", 10, "bold"), command=self.sync_data).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="2. Load Local", font=("Microsoft YaHei", 10), command=self.load_radar).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Open Excel", font=("Microsoft YaHei", 10), command=self.open_excel).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="Apply Edits to Spreadsheet", font=("Microsoft YaHei", 10, "bold"), bg="#FF9800", fg="black", command=self.apply_edits_to_excel).pack(side=tk.LEFT, padx=15)
        
        filter_frame = tk.LabelFrame(self, text="Smart Filters", font=("Microsoft YaHei", 10), padx=10, pady=5)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        
        f_type = tk.Frame(filter_frame)
        f_type.pack(side=tk.LEFT, padx=5)
        tk.Label(f_type, text="Type:", font=("Microsoft YaHei", 9, "bold")).pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value="All")
        ttk.Combobox(f_type, textvariable=self.type_var, values=["All", "chr", "prp", "env"], width=6, state="readonly", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=5)
        self.type_var.trace('w', lambda *args: self.apply_filter())
        
        f_lib = tk.Frame(filter_frame)
        f_lib.pack(side=tk.LEFT, padx=15)
        tk.Label(f_lib, text="lib Status:", font=("Microsoft YaHei", 9, "bold")).pack(side=tk.LEFT)
        self.lib_status_var = tk.StringVar(value="All")
        ttk.Combobox(f_lib, textvariable=self.lib_status_var, values=["All", "Passed", "Pending", "Not Passed"], width=12, state="readonly", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=5)
        self.lib_status_var.trace('w', lambda *args: self.apply_filter())

        tk.Label(filter_frame, text=" | ", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="all")
        for text, val in [("Show All", "all"), ("Ready for QC1", "qc1"), ("Stuck in Rig", "rig_wait"), ("Ready for LGT", "lgt_ready"), ("Ready for QC2", "qc2")]:
            tk.Radiobutton(filter_frame, text=text, variable=self.filter_var, value=val, command=self.apply_filter, font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=5)

        table_frame = tk.Frame(self, padx=10, pady=10)
        table_frame.pack(expand=True, fill=tk.BOTH)
        
        header = tk.Frame(table_frame, bg="#343A40")
        header.pack(fill=tk.X)
        cols = ["Select", "Type", "Asset Name", "texMaster", "QC_step_1", "rigMaster", "libRig", "LGT", "Assignee", "QC_step_2", "libMaster"]
        widths = [5, 6, 20, 10, 10, 10, 10, 10, 15, 10, 10]
        for i, c in enumerate(cols): 
            tk.Label(header, text=c, fg="white", bg="#343A40", font=("Microsoft YaHei", 10, "bold"), width=widths[i]).pack(side=tk.LEFT, padx=1, pady=5)
            
        canvas = tk.Canvas(table_frame)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom_frame = tk.Frame(self, pady=15, bg="#F8F9FA")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(bottom_frame, text="1. Execute Selected Pipelines!", bg="#28A745", fg="white", font=("Microsoft YaHei", 12, "bold"), command=self.run_pipeline).pack(side=tk.LEFT, padx=50)
        tk.Button(bottom_frame, text="2. 🚀 Final Release & Publish to Production", bg="#DC3545", fg="white", font=("Microsoft YaHei", 12, "bold"), command=self.final_release).pack(side=tk.LEFT, padx=20)

    def get_color(self, status): 
        return self.colors.get(status.lower() if status else 'None', self.colors['None'])

    def sync_data(self):
        proj = self.proj_entry.get()
        if not proj: return
        self.title("Syncing from Flow...")
        self.update()
        try:
            r1 = subprocess.call(["python", SYNC_SCRIPT, proj])
            r2 = subprocess.call(["python", os.path.join(TMP_DIR, "read_sheet.py"), proj])
            if r1 == 0 and r2 == 0:
                self.load_radar()
            else: 
                messagebox.showerror("Error", "Sync Subprocess failed.")
        except Exception as e: 
            messagebox.showerror("Error", str(e))
        finally: 
            self.title("PPAS Lib QC Dashboard Pro V4.2")

    def load_radar(self):
        if not os.path.exists(JSON_PATH): return
        try:
            with codecs.open(JSON_PATH, 'r', 'utf-8') as f: 
                self.assets_data = json.load(f)
            self.apply_filter()
        except Exception as e: 
            messagebox.showerror("Load Error", str(e))

    def open_excel(self):
        proj = self.proj_entry.get()
        if not proj: return
        p = os.path.normpath(u"X:/AI_Automation/Project/{}/work/spreadsheet/{}_资产入库管理表.xlsx".format(proj, proj))
        if os.path.exists(p):
            subprocess.call('attrib -r "{}"'.format(p.encode('gbk')), shell=True)
            os.startfile(p)
            if messagebox.askyesno("Confirm", "Spreadsheet Opened. Finished?"):
                subprocess.call('attrib +r "{}"'.format(p.encode('gbk')), shell=True)
                self.sync_data()
        else: 
            messagebox.showwarning("Warning", u"File missing.")

    def register_change(self, a, c, e):
        v = e.widget.get() if hasattr(e, 'widget') else e
        if a not in self.pending_updates: 
            self.pending_updates[a] = {}
        self.pending_updates[a][c] = v

    def apply_edits_to_excel(self):
        if not self.pending_updates: return
        proj = self.proj_entry.get()
        if not messagebox.askyesno("Confirm", "Apply edits?"): return
        try:
            updates = []
            for a, cols in self.pending_updates.items():
                for c, v in cols.items():
                    cid = c
                    if c == "Assignee": cid = u"\u5236\u4f5c\u4eba\u5458"
                    elif c == "LGT": cid = u"\u706f\u5149\u6587\u4ef6\u5236\u4f5c"
                    updates.append(u"{}|{}|{}".format(a, cid, v))
            payload = u";".join(updates).encode('utf-8')
            if subprocess.call(["python", BATCH_UPDATE_SCRIPT, proj, payload]) == 0:
                messagebox.showinfo("Success", "Updated.")
                self.pending_updates.clear()
                self.sync_data()
        except Exception as e: 
            messagebox.showerror("Error", str(e))

    def sync_to_flow(self, project, updates):
        tmp = os.path.join(TMP_DIR, "sg_update_payload.json")
        with io.open(tmp, 'w', encoding='utf-8') as f:
            c = json.dumps({"project": project, "updates": updates}, ensure_ascii=False)
            if sys.version_info[0] < 3: 
                c = unicode(c)
            f.write(c)
        subprocess.call([BLENDER_PATH, "-b", "-P", SG_UPDATE_SCRIPT, "--", tmp])

    def apply_filter(self):
        for widget in self.scrollable_frame.winfo_children(): 
            widget.destroy()
        self.checkbox_vars.clear()
        f_mode = self.filter_var.get()
        t_filter = self.type_var.get()
        l_filter = self.lib_status_var.get()
        valid = ['pub', 'tmpub']
        for item in self.assets_data:
            atype = item.get(u'\u8d44\u4ea7\u7c7b\u578b') or item.get('Type', 'unknown')
            if t_filter != "All" and atype != t_filter: continue
            name = item.get(u'\u8d44\u4ea7\u540d\u79f0') or item.get('Name')
            t_tex = item.get('texMaster', '')
            t_qc1 = item.get('QC_step_1', '')
            t_rig = item.get('rigMaster', '')
            t_lrig = item.get('libRig', '')
            t_lgt = item.get(u'\u706f\u5149\u6587\u4ef6\u5236\u4f5c', '')
            t_qc2 = item.get('QC_step_2', '')
            t_libm = item.get('libMaster', '')
            
            if l_filter == "Passed":
                if t_libm not in valid: continue
            elif l_filter == "Pending":
                if t_libm != "apr": continue
            elif l_filter == "Not Passed":
                if t_libm in valid or t_libm == "apr": continue
                
            is_qc1_ready = (t_tex in valid and (t_qc1 != t_tex or item.get('is_stale') in ['tex', 'both']))
            is_rig_wait = (t_qc1 == t_tex and t_lrig != t_rig and t_rig in valid)
            is_lgt_ready = (atype in ['chr', u'chr'] and t_qc1 in valid and t_lrig in valid and t_lgt not in valid)
            
            if atype in ['env', u'env']: 
                is_qc2_ready = (t_qc1 == t_tex and t_tex in valid and t_qc2 != t_tex)
            elif atype in ['prp', u'prp']: 
                is_qc2_ready = False
            else: # chr
                is_qc2_ready = (t_qc1 == t_tex and t_tex in valid and t_lrig == t_rig and t_rig in valid and t_lgt in valid and t_qc2 != t_tex)
            
            if f_mode == "qc1" and not is_qc1_ready: continue
            if f_mode == "rig_wait" and not is_rig_wait: continue
            if f_mode == "lgt_ready" and not is_lgt_ready: continue
            if f_mode == "qc2" and not is_qc2_ready: continue
            
            row_frame = tk.Frame(self.scrollable_frame, pady=2)
            row_frame.pack(fill=tk.X)
            var = tk.BooleanVar()
            self.checkbox_vars[name] = var
            tk.Checkbutton(row_frame, variable=var, width=4).pack(side=tk.LEFT, padx=1)
            
            widths = [5, 6, 20, 10, 10, 10, 10, 10, 15, 10, 10]
            tk.Label(row_frame, text=atype, font=("Microsoft YaHei", 9, "bold"), fg="#17A2B8", relief="ridge", borderwidth=1, width=widths[1]).pack(side=tk.LEFT, padx=1)
            stale = item.get('is_stale')
            tk.Label(row_frame, text=(u"⚠️ " if stale else u"") + name, font=("Microsoft YaHei", 9), bg="#FFF9C4" if stale else "SystemButtonFace", relief="ridge", borderwidth=1, width=widths[2]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=t_tex, font=("Microsoft YaHei", 9), bg=self.get_color(t_tex), relief="ridge", borderwidth=1, width=widths[3]).pack(side=tk.LEFT, padx=1)
            
            c_qc1 = ttk.Combobox(row_frame, values=self.status_list, width=widths[4], font=("Microsoft YaHei", 9))
            c_qc1.set(t_qc1)
            c_qc1.bind('<<ComboboxSelected>>', lambda e, a=name, c="QC_step_1": self.register_change(a, c, e))
            c_qc1.pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_rig, font=("Microsoft YaHei", 9), bg=self.get_color(t_rig), relief="ridge", borderwidth=1, width=widths[5]).pack(side=tk.LEFT, padx=1)
            
            c_lrig = ttk.Combobox(row_frame, values=self.status_list, width=widths[6], font=("Microsoft YaHei", 9))
            c_lrig.set(t_lrig)
            c_lrig.bind('<<ComboboxSelected>>', lambda e, a=name, c="libRig": self.register_change(a, c, e))
            c_lrig.pack(side=tk.LEFT, padx=1)
            
            c_lgt = ttk.Combobox(row_frame, values=self.status_list, width=widths[7], font=("Microsoft YaHei", 9))
            c_lgt.set(t_lgt)
            c_lgt.bind('<<ComboboxSelected>>', lambda e, a=name, c="LGT": self.register_change(a, c, e))
            c_lgt.pack(side=tk.LEFT, padx=1)
            
            e_maker = tk.Entry(row_frame, font=("Microsoft YaHei", 9), width=widths[8])
            e_maker.insert(0, item.get(u'\u5236\u4f5c\u4eba\u5458', ''))
            e_maker.bind('<FocusOut>', lambda e, a=name, c="Assignee": self.register_change(a, c, e))
            e_maker.pack(side=tk.LEFT, padx=1)

            c_qc2 = ttk.Combobox(row_frame, values=self.status_list, width=widths[9], font=("Microsoft YaHei", 9))
            c_qc2.set(t_qc2)
            c_qc2.bind('<<ComboboxSelected>>', lambda e, a=name, c="QC_step_2": self.register_change(a, c, e))
            c_qc2.pack(side=tk.LEFT, padx=1)
            
            c_libm = ttk.Combobox(row_frame, values=self.status_list, width=widths[10], font=("Microsoft YaHei", 9), state="disabled")
            c_libm.set(t_libm)
            c_libm.pack(side=tk.LEFT, padx=1)

    def run_pipeline(self):
        selected = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected: return
        proj = self.proj_entry.get()
        if messagebox.askyesno("Execute", "Run pipeline?"):
            self.title("Executing..."); self.update()
            try:
                subprocess.call(["python", PIPELINE_SCRIPT, proj, ",".join(selected)])
                messagebox.showinfo("Done", "Pipeline Finished.")
            finally: 
                self.title("PPAS Lib QC Dashboard Pro V4.2")
                self.sync_data()

    def final_release(self):
        selected = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected: return
        proj = self.proj_entry.get()
        if not messagebox.askyesno("Final Release", "Confirm Publish?"): return
        self.title("Publishing..."); self.update()
        res_sum = []; sg_ups = []; ex_ups = []
        for name in selected:
            item = next((i for i in self.assets_data if (i.get(u'\u8d44\u4ea7\u540d\u79f0') or i.get('Name')) == name), None)
            if not item: continue
            atype = item.get(u'\u8d44\u4ea7\u7c7b\u578b') or item.get('Type')
            t_tex = item.get('texMaster', ''); t_rig = item.get('rigMaster', '')
            t_lgt = item.get(u'\u706f\u5149\u6587\u4ef6\u5236\u4f5c', '')
            preds = [t_tex, t_rig]
            if atype in ['chr', u'chr']: preds.append(t_lgt)
            target = "pub"
            if "tmpub" in preds: target = "tmpub"
            if all(s not in ['pub', 'tmpub'] for s in preds): 
                res_sum.append(u"{} - SKIP: No Preds".format(name)); continue
            try:
                bw = os.path.join("X:/AI_Automation/Project", proj, "work/assets_lib", atype, name)
                bp = os.path.join("X:/Project", proj, "pub/asset_lib", atype, name, "lib")
                rs = os.path.join(bw, "libRig", "{}_{}_{}_lib_libRig.ma".format(proj, atype, name))
                if not os.path.exists(rs): rs = rs.replace(".ma", ".mb")
                if os.path.exists(rs):
                    if not os.path.exists(os.path.join(bp, "libRig")): os.makedirs(os.path.join(bp, "libRig"))
                    shutil.copy2(rs, os.path.join(bp, "libRig", os.path.basename(rs)))
                ms = os.path.join(bw, "libMaster", "{}_{}_{}_lib_libMaster.blend".format(proj, atype, name))
                if os.path.exists(ms):
                    if not os.path.exists(os.path.join(bp, "libMaster")): os.makedirs(os.path.join(bp, "libMaster"))
                    shutil.copy2(ms, os.path.join(bp, "libMaster", os.path.basename(ms)))
                sg_ups.append({"asset_name": name, "task_name": "libRig", "status": t_rig})
                sg_ups.append({"asset_name": name, "task_name": "libMaster", "status": target})
                ex_ups.append(u"{}|libMaster|{}".format(name, target))
                res_sum.append(u"{} - OK: {}".format(name, target))
            except Exception as e: 
                res_sum.append(u"{} - ERR: {}".format(name, e))
        if sg_ups: self.sync_to_flow(proj, sg_ups)
        if ex_ups: 
            subprocess.call(["python", BATCH_UPDATE_SCRIPT, proj, u";".join(ex_ups).encode('utf-8')])
        self.sync_data()
        messagebox.showinfo("Release Finished", "\n".join(res_sum))

if __name__ == "__main__": 
    app = QCDashboard()
    app.mainloop()
