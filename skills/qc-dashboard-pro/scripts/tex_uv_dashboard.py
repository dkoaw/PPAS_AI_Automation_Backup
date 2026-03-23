# -*- coding: utf-8 -*-
import sys, os, json, codecs, subprocess

# Python 2/3 compatibility
if sys.version_info[0] >= 3:
    unicode = str

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

# Scripts references
SYNC_SCRIPT = os.path.join(SKILLS_DIR, "tex-production-qc", "scripts", "manage_tex_spreadsheet.py")
PIPELINE_SCRIPT = os.path.join(SKILLS_DIR, "tex-production-qc", "scripts", "tex_pipeline_executor.py")

class TexUVDashboard(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PPAS Tex & UV QC Dashboard V2.0")
        self.geometry("1100x800")
        
        self.colors = {
            'pub': '#D4EDDA', 'tmpub': '#D4EDDA', 
            'wip': '#FFF3CD', 'wtg': '#E2E3E5',
            'rep': '#F8D7DA', 'apr': '#CCE5FF', 'rtk': '#F8D7DA', 'fin': '#D4EDDA', 'mis': '#ADB5BD', 'None': '#FFFFFF'
        }
        
        self.status_list = ["", "wtg", "rdy", "ip", "fin", "apr", "pub", "tmpub", "rep", "rtk", "hld", "omt", "mis"]
        
        # --- Filter Variables ---
        self.filter_vars = {
            "Type": tk.StringVar(value="All"),
            "modM": tk.StringVar(value="All"),
            "uvM": tk.StringVar(value="All"),
            "uvQC": tk.StringVar(value="All"),
            "texM": tk.StringVar(value="All"),
            "texQC": tk.StringVar(value="All")
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
        
        tk.Button(top_frame, text="1. Sync Data from SG", bg="#17A2B8", fg="white", font=("Microsoft YaHei", 10, "bold"), command=self.sync_data).pack(side=tk.LEFT, padx=10)
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
        
        tk.Label(filter_frame, text="uvQC:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["uvQC"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(filter_frame, text="texM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["texM"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(filter_frame, text="texQC:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["texQC"], values=filter_options, width=5, state="readonly").pack(side=tk.LEFT, padx=(0, 10))
        
        for var in self.filter_vars.values():
            var.trace("w", lambda name, index, mode: self.apply_filter())

        # --- Table Header ---
        table_frame = tk.Frame(self, padx=10, pady=10)
        table_frame.pack(expand=True, fill=tk.BOTH)
        
        header = tk.Frame(table_frame, bg="#2C3E50")
        header.pack(fill=tk.X)
        cols = ["Select", "Type", "Asset Name", "modM", "uvM", "uvQC", "texM", "texQC"]
        widths = [5, 6, 25, 10, 10, 10, 10, 10]
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

        # --- Bottom Actions ---
        bottom_frame = tk.Frame(self, pady=15, bg="#F8F9FA")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Button(bottom_frame, text="🚀 执行 UV QC", bg="#6C757D", fg="white", font=("Microsoft YaHei", 12, "bold"), command=lambda: self.run_pipeline("uv")).pack(side=tk.LEFT, padx=20)
        tk.Button(bottom_frame, text="🚀 执行 Tex QC", bg="#28A745", fg="white", font=("Microsoft YaHei", 12, "bold"), command=lambda: self.run_pipeline("tex")).pack(side=tk.LEFT, padx=20)
        
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", length=200, mode="indeterminate")
        self.progress.pack(side=tk.RIGHT, padx=20)

    def get_color(self, status): 
        return self.colors.get(status.lower() if status else 'None', self.colors['None'])

    def sync_data(self):
        proj = self.proj_entry.get()
        if not proj: return
        self.title("Syncing Data...")
        self.update()
        try:
            subprocess.call(["python", SYNC_SCRIPT, proj])
            self.load_radar()
        except Exception as e: 
            messagebox.showerror("Error", str(e))
        finally: 
            self.title("PPAS Tex & UV QC Dashboard V2.0")

    def load_radar(self):
        proj = self.proj_entry.get()
        spreadsheet_path = os.path.join("X:/AI_Automation/Project", proj, "work", "spreadsheet", u"{}_Tex制作管理表.xlsx".format(proj))
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
        p = os.path.normpath(u"X:/AI_Automation/Project/{}/work/spreadsheet/{}_Tex制作管理表.xlsx".format(proj, proj))
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
        f_uvQC = self.filter_vars["uvQC"].get()
        f_tex = self.filter_vars["texM"].get()
        f_texQC = self.filter_vars["texQC"].get()

        for item in self.assets_data:
            atype = item.get(u'资产类型', 'unknown')
            name = item.get(u'资产名称', '')
            t_mod = item.get('modMaster', '')
            t_uv = item.get('uvMaster', '')
            t_uvQC = item.get('uvQC', '')
            t_tex = item.get('texMaster', '')
            t_texQC = item.get('texQC', '')
            
            # Apply filters
            if f_type != "All" and atype != f_type: continue
            if f_mod != "All" and t_mod != f_mod: continue
            if f_uv != "All" and t_uv != f_uv: continue
            if f_uvQC != "All" and t_uvQC != f_uvQC: continue
            if f_tex != "All" and t_tex != f_tex: continue
            if f_texQC != "All" and t_texQC != f_texQC: continue
            
            row_frame = tk.Frame(self.scrollable_frame, pady=2)
            row_frame.pack(fill=tk.X)
            var = tk.BooleanVar()
            
            # No automatic checking in this pure-free version
            self.checkbox_vars[name] = var
            tk.Checkbutton(row_frame, variable=var, width=4).pack(side=tk.LEFT, padx=1)
            
            widths = [5, 6, 25, 10, 10, 10, 10, 10]
            tk.Label(row_frame, text=atype, font=("Microsoft YaHei", 9, "bold"), fg="#E67E22", relief="ridge", borderwidth=1, width=widths[1]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=name, font=("Microsoft YaHei", 9), relief="ridge", borderwidth=1, width=widths[2]).pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_mod, font=("Microsoft YaHei", 9), bg=self.get_color(t_mod), relief="ridge", borderwidth=1, width=widths[3]).pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_uv, font=("Microsoft YaHei", 9), bg=self.get_color(t_uv), relief="ridge", borderwidth=1, width=widths[4]).pack(side=tk.LEFT, padx=1)
            c_uqc = ttk.Combobox(row_frame, values=self.status_list, width=widths[5], font=("Microsoft YaHei", 9), state="disabled")
            c_uqc.set(t_uvQC if t_uvQC else "")
            c_uqc.pack(side=tk.LEFT, padx=1)

            tk.Label(row_frame, text=t_tex, font=("Microsoft YaHei", 9), bg=self.get_color(t_tex), relief="ridge", borderwidth=1, width=widths[6]).pack(side=tk.LEFT, padx=1)
            c_tqc = ttk.Combobox(row_frame, values=self.status_list, width=widths[7], font=("Microsoft YaHei", 9), state="disabled")
            c_tqc.set(t_texQC if t_texQC else "")
            c_tqc.pack(side=tk.LEFT, padx=1)

    def run_pipeline(self, run_type):
        """run_type can be 'uv' or 'tex'"""
        selected = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected: return
        proj = self.proj_entry.get()
        if messagebox.askyesno("Execute", u"确认对选中的资产执行 {} QC 吗？\n(这将会洗稿、生成报告，并记录状态)".format(run_type.upper())):
            self.title("Executing {} QC...".format(run_type.upper()))
            self.progress.start(15)
            import threading
            def task():
                try:
                    subprocess.call(["python", PIPELINE_SCRIPT, proj, run_type, ",".join(selected)])
                finally:
                    self.after(0, self.on_pipeline_done)
            threading.Thread(target=task).start()

    def on_pipeline_done(self):
        self.progress.stop()
        self.title("PPAS Tex & UV QC Dashboard V2.0")
        messagebox.showinfo("Done", "QC Pipeline Finished.")
        self.load_radar()

if __name__ == "__main__": 
    app = TexUVDashboard()
    app.mainloop()
