# -*- coding: utf-8 -*-
import sys, os, subprocess

try:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox

SKILLS_DIR = r"X:\AI_Automation\.gemini\skills"
SYNC_SCRIPT = os.path.join(SKILLS_DIR, "rig-production-qc", "scripts", "manage_rig_spreadsheet.py")
PIPELINE_SCRIPT = os.path.join(SKILLS_DIR, "rig-production-qc", "scripts", "rig_pipeline_executor.py") # We will create this in Step 4

class RigQCDashboard(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PPAS Rig QC Dashboard V1.0")
        self.geometry("900x700")
        
        self.colors = {
            'pub': '#D4EDDA', 'tmpub': '#D4EDDA', 
            'wip': '#FFF3CD', 'wtg': '#E2E3E5',
            'rep': '#F8D7DA', 'apr': '#CCE5FF', 'rtk': '#F8D7DA', 'fin': '#D4EDDA', 'None': '#FFFFFF'
        }
        
        self.status_list = ["", "wtg", "rdy", "ip", "fin", "apr", "pub", "tmpub", "rep", "rtk", "hld", "omt"]
        
        # --- Filter Variables ---
        self.filter_vars = {
            "Type": tk.StringVar(value="All"),
            "modM": tk.StringVar(value="All"),
            "uvM": tk.StringVar(value="All"),
            "texM": tk.StringVar(value="All"),
            "rigM": tk.StringVar(value="All"),
            "rigQC": tk.StringVar(value="All")
        }
        
        self.assets_data = []
        self.checkbox_vars = {}
        
        self.init_ui()
        
    def init_ui(self):
        top_frame = tk.Frame(self, pady=10, padx=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Project:", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT)
        self.proj_entry = tk.Entry(top_frame, width=10, font=("Microsoft YaHei", 10))
        self.proj_entry.insert(0, "ysj")
        self.proj_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="1. Sync Rig Data from SG", bg="#17A2B8", fg="white", font=("Microsoft YaHei", 10, "bold"), command=self.sync_data).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="Open Spreadsheet", font=("Microsoft YaHei", 10), command=self.open_excel).pack(side=tk.LEFT, padx=10)
        
        # --- Filter UI ---
        filter_frame = tk.Frame(self, pady=5, padx=10, bg="#E9ECEF")
        filter_frame.pack(side=tk.TOP, fill=tk.X)
        
        filter_options = ["All"] + [s for s in self.status_list if s]
        type_options = ["All", "chr", "prp", "env"]
        
        tk.Label(filter_frame, text="Filters:", font=("Microsoft YaHei", 9, "bold"), bg="#E9ECEF").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="Type:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["Type"], values=type_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="modM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["modM"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="uvM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["uvM"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="texM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["texM"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="rigM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["rigM"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="rigQC:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["rigQC"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        # Bind combobox selection to trigger re-filtering
        for var in self.filter_vars.values():
            var.trace("w", lambda name, index, mode: self.apply_filter())

        # --- Table Header ---
        table_frame = tk.Frame(self, padx=10, pady=10)
        table_frame.pack(expand=True, fill=tk.BOTH)
        
        header = tk.Frame(table_frame, bg="#2C3E50")
        header.pack(fill=tk.X)
        cols = ["Select", "Type", "Asset Name", "modM", "uvM", "texM", "rigMaster", "rigQC"]
        widths = [5, 10, 30, 8, 8, 8, 15, 15]
        for i, c in enumerate(cols): 
            tk.Label(header, text=c, fg="white", bg="#2C3E50", font=("Microsoft YaHei", 10, "bold"), width=widths[i]).pack(side=tk.LEFT, padx=1, pady=5)
            
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
        tk.Button(bottom_frame, text="🚀 Execute Selected Rig QC", bg="#28A745", fg="white", font=("Microsoft YaHei", 12, "bold"), command=self.run_pipeline).pack(side=tk.LEFT, padx=50)
        
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(side=tk.RIGHT, padx=50)

    def get_color(self, status): 
        return self.colors.get(status.lower() if status else 'None', self.colors['None'])

    def sync_data(self):
        proj = self.proj_entry.get()
        if not proj: return
        self.title("Syncing Rig Data...")
        self.update()
        try:
            subprocess.call(["python", SYNC_SCRIPT, proj])
            self.load_radar()
        except Exception as e: 
            messagebox.showerror("Error", str(e))
        finally: 
            self.title("PPAS Rig QC Dashboard V1.0")

    def load_radar(self):
        proj = self.proj_entry.get()
        spreadsheet_path = os.path.join("X:/AI_Automation/Project", proj, "work", "spreadsheet", u"{}_Rig制作管理表.xlsx".format(proj))
        if not os.path.exists(spreadsheet_path): return
        
        try:
            import openpyxl
            wb = openpyxl.load_workbook(spreadsheet_path, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            headers = [unicode(h) if h else u"" for h in rows[0]]
            self.assets_data = []
            for r in rows[1:]:
                row_dict = {}
                for i, val in enumerate(r):
                    if i < len(headers):
                        row_dict[headers[i]] = val
                self.assets_data.append(row_dict)
            self.apply_filter()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def open_excel(self):
        proj = self.proj_entry.get()
        if not proj: return
        p = os.path.normpath(u"X:/AI_Automation/Project/{}/work/spreadsheet/{}_Rig制作管理表.xlsx".format(proj, proj))
        if os.path.exists(p):
            subprocess.call('attrib -r "{}"'.format(p.encode('gbk')), shell=True)
            os.startfile(p)
            if messagebox.askyesno("Confirm", "Spreadsheet Opened. Finished?"):
                subprocess.call('attrib +r "{}"'.format(p.encode('gbk')), shell=True)
                self.load_radar()

    def apply_filter(self):
        for widget in self.scrollable_frame.winfo_children(): 
            widget.destroy()
        self.checkbox_vars.clear()
        
        f_type = self.filter_vars["Type"].get()
        f_mod = self.filter_vars["modM"].get()
        f_uv = self.filter_vars["uvM"].get()
        f_tex = self.filter_vars["texM"].get()
        f_rigM = self.filter_vars["rigM"].get()
        f_rigQC = self.filter_vars["rigQC"].get()

        for item in self.assets_data:
            atype = item.get(u'资产类型', 'unknown')
            name = item.get(u'资产名称', '')
            t_mod = item.get('modMaster', '')
            t_uv = item.get('uvMaster', '')
            t_tex = item.get('texMaster', '')
            t_rigM = item.get('rigMaster', '')
            t_rigQC = item.get('rigQC', '')
            
            # Apply filters
            if f_type != "All" and atype != f_type: continue
            if f_mod != "All" and t_mod != f_mod: continue
            if f_uv != "All" and t_uv != f_uv: continue
            if f_tex != "All" and t_tex != f_tex: continue
            if f_rigM != "All" and t_rigM != f_rigM: continue
            if f_rigQC != "All" and t_rigQC != f_rigQC: continue
            
            row_frame = tk.Frame(self.scrollable_frame, pady=2)
            row_frame.pack(fill=tk.X)
            var = tk.BooleanVar()
            
            # Auto-check logic: Master is 'apr' and QC is not 'fin'
            if t_rigM == 'apr' and t_rigQC not in ['fin', 'apr', 'pass']:
                var.set(True)
                
            self.checkbox_vars[name] = var
            tk.Checkbutton(row_frame, variable=var, width=4).pack(side=tk.LEFT, padx=1)
            
            widths = [5, 10, 30, 8, 8, 8, 15, 15]
            tk.Label(row_frame, text=atype, font=("Microsoft YaHei", 9, "bold"), fg="#8E44AD", relief="ridge", borderwidth=1, width=widths[1]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=name, font=("Microsoft YaHei", 9), relief="ridge", borderwidth=1, width=widths[2]).pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_mod, font=("Microsoft YaHei", 9), bg=self.get_color(t_mod), relief="ridge", borderwidth=1, width=widths[3]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=t_uv, font=("Microsoft YaHei", 9), bg=self.get_color(t_uv), relief="ridge", borderwidth=1, width=widths[4]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=t_tex, font=("Microsoft YaHei", 9), bg=self.get_color(t_tex), relief="ridge", borderwidth=1, width=widths[5]).pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_rigM, font=("Microsoft YaHei", 9), bg=self.get_color(t_rigM), relief="ridge", borderwidth=1, width=widths[6]).pack(side=tk.LEFT, padx=1)
            c_rqc = ttk.Combobox(row_frame, values=self.status_list, width=widths[7], font=("Microsoft YaHei", 9), state="disabled")
            c_rqc.set(t_rigQC)
            c_rqc.pack(side=tk.LEFT, padx=1)

    def run_pipeline(self):
        selected = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected: return
        proj = self.proj_entry.get()
        if messagebox.askyesno("Execute", "Run Maya Rig QC on selected assets?"):
            self.title("Executing Rig QC...")
            self.progress.start(15)
            import threading
            def task():
                try:
                    subprocess.call(["python", PIPELINE_SCRIPT, proj, ",".join(selected)])
                finally:
                    self.after(0, self.on_pipeline_done)
            threading.Thread(target=task).start()

    def on_pipeline_done(self):
        self.progress.stop()
        self.title("PPAS Rig QC Dashboard V1.0")
        messagebox.showinfo("Done", "Rig QC Pipeline Finished.")
        self.load_radar()

if __name__ == "__main__": 
    app = RigQCDashboard()
    app.mainloop()
