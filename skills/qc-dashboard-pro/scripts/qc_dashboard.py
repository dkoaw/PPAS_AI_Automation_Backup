# -*- coding: utf-8 -*-
import sys
import os
import json
import codecs
import subprocess

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

class QCDashboard(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PPAS Lib QC Dashboard Pro V3.8 - LGT Control Mode")
        self.geometry("1600x800")
        
        self.colors = {
            'pub': '#D4EDDA',
            'tmpub': '#D4EDDA', 
            'wip': '#FFF3CD',
            'wtg': '#E2E3E5',
            'rtk': '#F8D7DA',
            'apr': '#CCE5FF',
            'None': '#FFFFFF'
        }
        
        self.status_list = ["", "wtg", "rdy", "ip", "fin", "apr", "pub", "tmpub", "rtk", "hld", "omt"]
        self.assets_data = []
        self.checkbox_vars = {}
        self.pending_updates = {}
        self.combo_widgets = {}
        
        self.init_ui()
        
    def init_ui(self):
        top_frame = tk.Frame(self, pady=10, padx=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Project:", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT)
        self.proj_entry = tk.Entry(top_frame, width=10, font=("Microsoft YaHei", 10))
        self.proj_entry.insert(0, "ysj")
        self.proj_entry.pack(side=tk.LEFT, padx=5)
        
        btn_sync = tk.Button(top_frame, text="1. Sync Flow Status", bg="#007BFF", fg="white", font=("Microsoft YaHei", 10, "bold"), command=self.sync_data)
        btn_sync.pack(side=tk.LEFT, padx=10)
        
        btn_load = tk.Button(top_frame, text="2. Load Local", font=("Microsoft YaHei", 10), command=self.load_radar)
        btn_load.pack(side=tk.LEFT, padx=5)

        btn_auto_apr = tk.Button(top_frame, text="3. Smart Auto-APR", bg="#17A2B8", fg="white", font=("Microsoft YaHei", 10, "bold"), command=self.auto_fill_apr)
        btn_auto_apr.pack(side=tk.LEFT, padx=15)

        btn_open_excel = tk.Button(top_frame, text="Open Excel", font=("Microsoft YaHei", 10), command=self.open_excel)
        btn_open_excel.pack(side=tk.LEFT, padx=10)
        
        btn_apply_edits = tk.Button(top_frame, text="Apply Edits to Spreadsheet", font=("Microsoft YaHei", 10, "bold"), bg="#FF9800", fg="black", command=self.apply_edits_to_excel)
        btn_apply_edits.pack(side=tk.LEFT, padx=15)
        
        filter_frame = tk.LabelFrame(self, text="Smart Filters", font=("Microsoft YaHei", 10), padx=10, pady=5)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        
        type_frame = tk.Frame(filter_frame)
        type_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(type_frame, text="Type:", font=("Microsoft YaHei", 9, "bold")).pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(type_frame, textvariable=self.type_var, values=["All", "chr", "prp", "env"], width=6, state="readonly", font=("Microsoft YaHei", 9))
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filter())
        type_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(filter_frame, text=" | ", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="all")
        tk.Radiobutton(filter_frame, text="Show All", variable=self.filter_var, value="all", command=self.apply_filter, font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        tk.Radiobutton(filter_frame, text="Only: Ready for QC1", variable=self.filter_var, value="qc1", command=self.apply_filter, font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(filter_frame, text="Only: Stuck in Rig Sync", variable=self.filter_var, value="rig_wait", command=self.apply_filter, font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(filter_frame, text="Only: Ready for QC2", variable=self.filter_var, value="qc2", command=self.apply_filter, font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=10)

        table_frame = tk.Frame(self, padx=10, pady=10)
        table_frame.pack(expand=True, fill=tk.BOTH)
        
        header = tk.Frame(table_frame, bg="#343A40")
        header.pack(fill=tk.X)
        # Added LGT to Headers
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

        bottom_frame = tk.Frame(self, pady=10, bg="#F8F9FA")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        btn_run = tk.Button(bottom_frame, text="Execute Selected Pipelines!", bg="#28A745", fg="white", font=("Microsoft YaHei", 12, "bold"), command=self.run_pipeline)
        btn_run.pack(pady=10)

    def get_color(self, status):
        return self.colors.get(status.lower() if status else 'None', self.colors['None'])

    def sync_data(self):
        proj = self.proj_entry.get()
        if not proj: return
        self.title("Syncing data from Flow...")
        self.update()
        try:
            subprocess.call(["python", SYNC_SCRIPT, proj])
            subprocess.call(["python", os.path.join(TMP_DIR, "read_sheet.py"), proj])
            self.load_radar()
        except Exception as e:
            messagebox.showerror("Sync Error", str(e))
        finally:
            self.title("PPAS Lib QC Dashboard Pro V3.8")

    def load_radar(self):
        if not os.path.exists(JSON_PATH): return
        try:
            with codecs.open(JSON_PATH, 'r', 'utf-8') as f:
                self.assets_data = json.load(f)
            self.apply_filter()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def open_excel(self):
        import glob
        proj = self.proj_entry.get()
        if not proj: return
        search_pattern = os.path.normpath("X:/AI_Automation/Project/{}/work/spreadsheet/{}_*.xlsx".format(proj, proj))
        found_files = glob.glob(search_pattern)
        if found_files:
            excel_path = found_files[0]
            subprocess.call('attrib -r "{}"'.format(excel_path), shell=True)
            os.startfile(excel_path)
            if messagebox.askyesno("Confirm", "Spreadsheet Unlocked and Opened.\n\nDid you finish editing and saving? (Click Yes to lock again)"):
                subprocess.call('attrib +r "{}"'.format(excel_path), shell=True)
                self.sync_data()
        else:
            messagebox.showwarning("Warning", "Spreadsheet not found.")

    def register_change(self, asset_name, column_name, event_or_val):
        new_val = event_or_val.widget.get() if hasattr(event_or_val, 'widget') else event_or_val
        if asset_name not in self.pending_updates:
            self.pending_updates[asset_name] = {}
        self.pending_updates[asset_name][column_name] = new_val

    def apply_edits_to_excel(self):
        if not self.pending_updates:
            messagebox.showinfo("Notice", "No changes detected.")
            return
        proj = self.proj_entry.get()
        confirm = messagebox.askyesno("Confirm", "Apply edits to Spreadsheet?")
        if not confirm: return
        try:
            updates = []
            for asset, cols in self.pending_updates.items():
                for col_name, val in cols.items():
                    col_id = col_name
                    if col_name == "Assignee": col_id = u"\u5236\u4f5c\u4eba\u5458"
                    elif col_name == "LGT": col_id = u"\u706f\u5149\u6587\u4ef6\u5236\u4f5c"
                    updates.append(u"{}|{}|{}".format(asset, col_id, val))
            payload = u";".join(updates)
            cmd = ["python", BATCH_UPDATE_SCRIPT, proj, payload.encode('utf-8')]
            subprocess.call(cmd)
            messagebox.showinfo("Success", "Edits successfully written and locked.")
            self.pending_updates.clear()
            self.sync_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def auto_fill_apr(self):
        """Rules-based libMaster APR auto-filler"""
        count = 0
        valid_states = ['pub', 'tmpub']
        for item in self.assets_data:
            atype = item.get(u'\u8d44\u4ea7\u7c7b\u578b') or item.get('Type')
            name = item.get(u'\u8d44\u4ea7\u540d\u79f0') or item.get('Name')
            t_tex = item.get('texMaster', '')
            t_qc1 = item.get('QC_step_1', '')
            t_rig = item.get('rigMaster', '')
            t_lrig = item.get('libRig', '')
            t_qc2 = item.get('QC_step_2', '')
            t_libm = item.get('libMaster', '')
            
            if t_libm == 'apr': continue
            
            eligible = False
            if atype in ['chr', u'chr']:
                if t_tex in valid_states and t_qc1 == t_tex and t_qc2 == t_tex and \
                   t_rig in valid_states and t_lrig == t_rig:
                    eligible = True
            elif atype in ['prp', u'prp']:
                if t_tex in valid_states and t_qc1 == t_tex and \
                   t_rig in valid_states and t_lrig == t_rig:
                    eligible = True
            
            if eligible:
                self.register_change(name, "libMaster", "apr")
                if name in self.combo_widgets:
                    self.combo_widgets[name].set("apr")
                count += 1
        if count > 0:
            messagebox.showinfo("Smart Filter", "Found {} eligible assets. Set to 'apr'.".format(count))

    def apply_filter(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.checkbox_vars.clear()
        self.combo_widgets.clear()
        
        filter_mode = self.filter_var.get()
        type_filter = self.type_var.get()
        valid_states = ['pub', 'tmpub']
        
        for item in self.assets_data:
            asset_type = item.get(u'\u8d44\u4ea7\u7c7b\u578b') or item.get('Type', 'unknown')
            if type_filter != "All" and asset_type != type_filter: continue
            if not asset_type: continue
            
            name = item.get(u'\u8d44\u4ea7\u540d\u79f0') or item.get('Name')
            t_tex = item.get('texMaster', '')
            t_qc1 = item.get('QC_step_1', '')
            t_rig = item.get('rigMaster', '')
            t_lrig = item.get('libRig', '')
            t_lgt = item.get(u'\u706f\u5149\u6587\u4ef6\u5236\u4f5c', '')
            t_qc2 = item.get('QC_step_2', '')
            t_assignee = item.get(u'\u5236\u4f5c\u4eba\u5458', '')
            t_libm = item.get('libMaster', '')
            
            is_qc1_ready = (t_tex in valid_states and t_qc1 != t_tex)
            is_rig_wait = (t_qc1 == t_tex and t_lrig != t_rig and t_rig in valid_states)
            
            if asset_type in ['env', u'env']:
                is_qc2_ready = (t_qc1 == t_tex and t_tex in valid_states and t_qc2 != t_tex)
                is_eligible = (t_qc1 == t_tex and t_tex in valid_states)
            elif asset_type in ['prp', u'prp']:
                is_qc2_ready = False
                is_eligible = (t_tex in valid_states and t_qc1 == t_tex and t_rig in valid_states and t_lrig == t_rig)
            else: # chr
                # NEW QC2 Condition: tex, rig, and LGT must all be pub/tmpub
                is_qc2_ready = (t_qc1 == t_tex and t_tex in valid_states and \
                                t_lrig == t_rig and t_rig in valid_states and \
                                t_lgt in valid_states and \
                                t_qc2 != t_tex)
                is_eligible = (t_tex in valid_states and t_qc1 == t_tex and t_qc2 == t_tex and t_rig in valid_states and t_lrig == t_rig)

            if filter_mode == "qc1" and not is_qc1_ready: continue
            if filter_mode == "rig_wait" and not is_rig_wait: continue
            if filter_mode == "qc2" and not is_qc2_ready: continue

            row_frame = tk.Frame(self.scrollable_frame, pady=2)
            row_frame.pack(fill=tk.X)
            
            var = tk.BooleanVar()
            self.checkbox_vars[name] = var
            chk = tk.Checkbutton(row_frame, variable=var, width=4)
            chk.pack(side=tk.LEFT, padx=1)
            
            widths = [20, 6, 10, 10, 10, 10, 10, 10, 15, 10]
            
            tk.Label(row_frame, text=asset_type, font=("Microsoft YaHei", 9, "bold"), fg="#17A2B8", relief="ridge", borderwidth=1, width=widths[1]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=name, font=("Microsoft YaHei", 9), relief="ridge", borderwidth=1, width=widths[0]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=t_tex, font=("Microsoft YaHei", 9), bg=self.get_color(t_tex), relief="ridge", borderwidth=1, width=widths[2]).pack(side=tk.LEFT, padx=1)
            
            # QC1
            combo_qc1 = ttk.Combobox(row_frame, values=self.status_list, width=widths[3], font=("Microsoft YaHei", 9))
            combo_qc1.set(t_qc1)
            combo_qc1.bind('<<ComboboxSelected>>', lambda e, a=name, c="QC_step_1": self.register_change(a, c, e))
            combo_qc1.pack(side=tk.LEFT, padx=1)
            
            # rigMaster
            tk.Label(row_frame, text=t_rig, font=("Microsoft YaHei", 9), bg=self.get_color(t_rig), relief="ridge", borderwidth=1, width=widths[4]).pack(side=tk.LEFT, padx=1)
            
            # libRig
            combo_lrig = ttk.Combobox(row_frame, values=self.status_list, width=widths[5], font=("Microsoft YaHei", 9))
            combo_lrig.set(t_lrig)
            combo_lrig.bind('<<ComboboxSelected>>', lambda e, a=name, c="libRig": self.register_change(a, c, e))
            combo_lrig.pack(side=tk.LEFT, padx=1)
            
            # LGT
            combo_lgt = ttk.Combobox(row_frame, values=self.status_list, width=widths[7], font=("Microsoft YaHei", 9))
            combo_lgt.set(t_lgt)
            combo_lgt.bind('<<ComboboxSelected>>', lambda e, a=name, c="LGT": self.register_change(a, c, e))
            combo_lgt.pack(side=tk.LEFT, padx=1)
            
            # Assignee (Maker)
            entry_maker = tk.Entry(row_frame, font=("Microsoft YaHei", 9), width=widths[8])
            entry_maker.insert(0, t_assignee)
            entry_maker.bind('<FocusOut>', lambda e, a=name, c="Assignee": self.register_change(a, c, e))
            entry_maker.pack(side=tk.LEFT, padx=1)

            # QC2
            combo_qc2 = ttk.Combobox(row_frame, values=self.status_list, width=widths[9], font=("Microsoft YaHei", 9))
            combo_qc2.set(t_qc2)
            combo_qc2.bind('<<ComboboxSelected>>', lambda e, a=name, c="QC_step_2": self.register_change(a, c, e))
            combo_qc2.pack(side=tk.LEFT, padx=1)
            
            # libMaster
            combo_libm = ttk.Combobox(row_frame, values=self.status_list, width=widths[10], font=("Microsoft YaHei", 9))
            combo_libm.set(t_libm)
            if is_eligible and t_libm != 'apr': combo_libm.configure(background="#E0FFFF")
            combo_libm.bind('<<ComboboxSelected>>', lambda e, a=name, c="libMaster": self.register_change(a, c, e))
            combo_libm.pack(side=tk.LEFT, padx=1)
            self.combo_widgets[name] = combo_libm

    def run_pipeline(self):
        selected_assets = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected_assets: return
        proj = self.proj_entry.get()
        confirm = messagebox.askyesno("Execute", "Run pipeline for selected?")
        if not confirm: return
        self.title("Executing...")
        self.update()
        try:
            subprocess.call(["python", PIPELINE_SCRIPT, proj, ",".join(selected_assets)])
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.title("PPAS Lib QC Dashboard Pro V3.8")
        messagebox.showinfo("Done", "Pipeline Finished.")

if __name__ == "__main__":
    app = QCDashboard()
    app.mainloop()
