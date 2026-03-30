# -*- coding: utf-8 -*-
import sys, os, json, codecs, subprocess

# Python 2/3 compatibility
if sys.version_info[0] >= 3:
    unicode = str

try:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog

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
            "modQC": tk.StringVar(value="All"),
            "uvM": tk.StringVar(value="All"),
            "uvQC": tk.StringVar(value="All"),
            "texM": tk.StringVar(value="All"),
            "texQC": tk.StringVar(value="All"),
            "can_modQC": tk.BooleanVar(value=False),
            "can_uvQC": tk.BooleanVar(value=False),
            "can_texQC": tk.BooleanVar(value=False)
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
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["Type"], values=type_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(filter_frame, text="modM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["modM"], values=filter_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(filter_frame, text="modQC:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["modQC"], values=filter_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(filter_frame, text="uvM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["uvM"], values=filter_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(filter_frame, text="uvQC:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["uvQC"], values=filter_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(filter_frame, text="texM:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["texM"], values=filter_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(filter_frame, text="texQC:", font=("Microsoft YaHei", 9), bg="#E9ECEF").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.filter_vars["texQC"], values=filter_options, width=4, state="readonly").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Checkbutton(filter_frame, text=u"可执行 Mod", variable=self.filter_vars["can_modQC"], bg="#E9ECEF", font=("Microsoft YaHei", 9, "bold"), fg="#17A2B8").pack(side=tk.LEFT, padx=(5, 5))
        tk.Checkbutton(filter_frame, text=u"可执行 UV", variable=self.filter_vars["can_uvQC"], bg="#E9ECEF", font=("Microsoft YaHei", 9, "bold"), fg="#6C757D").pack(side=tk.LEFT, padx=(0, 5))
        tk.Checkbutton(filter_frame, text=u"可执行 Tex", variable=self.filter_vars["can_texQC"], bg="#E9ECEF", font=("Microsoft YaHei", 9, "bold"), fg="#28A745").pack(side=tk.LEFT, padx=(0, 5))
        
        for var in self.filter_vars.values():
            var.trace("w", lambda name, index, mode: self.apply_filter())

        # --- Table Header ---
        table_frame = tk.Frame(self, padx=10, pady=10)
        table_frame.pack(expand=True, fill=tk.BOTH)
        
        header = tk.Frame(table_frame, bg="#2C3E50")
        header.pack(fill=tk.X)
        cols = ["Select", "Type", "Asset Name", "modM", "modQC", "uvM", "uvQC", "texM", "texQC"]
        widths = [5, 6, 22, 10, 10, 10, 10, 10, 10]
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
        
        tk.Button(bottom_frame, text="🚀 执行 Mod QC", bg="#17A2B8", fg="white", font=("Microsoft YaHei", 12, "bold"), command=lambda: self.run_pipeline("mod")).pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="🚀 执行 UV QC", bg="#6C757D", fg="white", font=("Microsoft YaHei", 12, "bold"), command=lambda: self.run_pipeline("uv")).pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="🚀 执行 Tex QC", bg="#28A745", fg="white", font=("Microsoft YaHei", 12, "bold"), command=lambda: self.run_pipeline("tex")).pack(side=tk.LEFT, padx=10)

        # self.pub_module = tk.StringVar(value="")
        # tk.Radiobutton(bottom_frame, text="提交 UV", variable=self.pub_module, value="uv", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        # tk.Radiobutton(bottom_frame, text="提交 Tex", variable=self.pub_module, value="tex", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        
        # New Publish Options Block
        # opt_frame = tk.Frame(bottom_frame, bg="#F8F9FA")
        # opt_frame.pack(side=tk.LEFT, padx=15)
        # self.opt_pub_mat = tk.BooleanVar(value=True)
        # self.opt_2k = tk.BooleanVar(value=True)
        # tk.Checkbutton(opt_frame, text=u"同步发包 S->X", variable=self.opt_pub_mat, bg="#F8F9FA", font=("Microsoft YaHei", 8)).pack(side=tk.TOP, anchor="w")
        # tk.Checkbutton(opt_frame, text=u"切 2K图(限Tex)", variable=self.opt_2k, bg="#F8F9FA", font=("Microsoft YaHei", 8)).pack(side=tk.TOP, anchor="w")

        # tk.Button(bottom_frame, text="🚀 快速 Publish", bg="#17A2B8", fg="white", font=("Microsoft YaHei", 12, "bold"), command=self.run_publish_no_qc).pack(side=tk.LEFT, padx=5)
        
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
            self.title("PPAS Mod/UV/Tex QC Dashboard V2.0")

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
        f_modQC = self.filter_vars["modQC"].get()
        f_uv = self.filter_vars["uvM"].get()
        f_uvQC = self.filter_vars["uvQC"].get()
        f_tex = self.filter_vars["texM"].get()
        f_texQC = self.filter_vars["texQC"].get()
        f_can_mod = self.filter_vars["can_modQC"].get()
        f_can_uv = self.filter_vars["can_uvQC"].get()
        f_can_tex = self.filter_vars["can_texQC"].get()

        for item in self.assets_data:
            atype = item.get(u'资产类型', 'unknown')
            name = item.get(u'资产名称', '')
            t_mod = item.get('modMaster', '')
            t_modQC = item.get('modQC', '')
            t_uv = item.get('uvMaster', '')
            t_uvQC = item.get('uvQC', '')
            t_tex = item.get('texMaster', '')
            t_texQC = item.get('texQC', '')
            
            # Apply filters
            if f_type != "All" and atype != f_type: continue
            if f_mod != "All" and t_mod != f_mod: continue
            if f_modQC != "All" and t_modQC != f_modQC: continue
            if f_uv != "All" and t_uv != f_uv: continue
            if f_uvQC != "All" and t_uvQC != f_uvQC: continue
            if f_tex != "All" and t_tex != f_tex: continue
            if f_texQC != "All" and t_texQC != f_texQC: continue
            
            if f_can_mod and t_mod.strip().lower() not in ["apr", "tmpub"]: continue
            if f_can_uv and t_uv.strip().lower() not in ["apr", "tmpub"]: continue
            if f_can_tex and t_tex.strip().lower() not in ["apr", "tmpub"]: continue
            
            row_frame = tk.Frame(self.scrollable_frame, pady=2)
            row_frame.pack(fill=tk.X)
            var = tk.BooleanVar()
            
            # No automatic checking in this pure-free version
            self.checkbox_vars[name] = var
            tk.Checkbutton(row_frame, variable=var, width=4).pack(side=tk.LEFT, padx=1)
            
            widths = [5, 6, 22, 10, 10, 10, 10, 10, 10]
            tk.Label(row_frame, text=atype, font=("Microsoft YaHei", 9, "bold"), fg="#E67E22", relief="ridge", borderwidth=1, width=widths[1]).pack(side=tk.LEFT, padx=1)
            tk.Label(row_frame, text=name, font=("Microsoft YaHei", 9), relief="ridge", borderwidth=1, width=widths[2]).pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_mod, font=("Microsoft YaHei", 9), bg=self.get_color(t_mod), relief="ridge", borderwidth=1, width=widths[3]).pack(side=tk.LEFT, padx=1)
            c_mqc = ttk.Combobox(row_frame, values=self.status_list, width=widths[4], font=("Microsoft YaHei", 9), state="disabled")
            c_mqc.set(t_modQC if t_modQC else "")
            c_mqc.pack(side=tk.LEFT, padx=1)
            
            tk.Label(row_frame, text=t_uv, font=("Microsoft YaHei", 9), bg=self.get_color(t_uv), relief="ridge", borderwidth=1, width=widths[5]).pack(side=tk.LEFT, padx=1)
            c_uqc = ttk.Combobox(row_frame, values=self.status_list, width=widths[6], font=("Microsoft YaHei", 9), state="disabled")
            c_uqc.set(t_uvQC if t_uvQC else "")
            c_uqc.pack(side=tk.LEFT, padx=1)

            tk.Label(row_frame, text=t_tex, font=("Microsoft YaHei", 9), bg=self.get_color(t_tex), relief="ridge", borderwidth=1, width=widths[7]).pack(side=tk.LEFT, padx=1)
            c_tqc = ttk.Combobox(row_frame, values=self.status_list, width=widths[8], font=("Microsoft YaHei", 9), state="disabled")
            c_tqc.set(t_texQC if t_texQC else "")
            c_tqc.pack(side=tk.LEFT, padx=1)

    def run_pipeline(self, run_type):
        """run_type can be 'uv' or 'tex'"""
        selected = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected: return
        
        # --- A.R.E.V SOP: Status Prerequisites Validation ---
        invalid_assets = []
        for name in selected:
            asset_info = next((item for item in self.assets_data if item.get(u'资产名称', '') == name), None)
            if asset_info is not None:
                if run_type == "mod":
                    if asset_info.get('modMaster', '').strip().lower() not in ["apr", "tmpub"]:
                        invalid_assets.append(name)
                elif run_type == "uv":
                    if asset_info.get('uvMaster', '').strip().lower() not in ["apr", "tmpub"]:
                        invalid_assets.append(name)
                elif run_type == "tex":
                    if asset_info.get('texMaster', '').strip().lower() not in ["apr", "tmpub"]:
                        invalid_assets.append(name)
                        
        if invalid_assets:
            joined_names = ", ".join([unicode(n) for n in invalid_assets])
            msg = u"执行失败！(A.R.E.V SOP 拦截)\n\n执行 {} QC 的前提要求其对应的 {}Master 环节状态必须为 'apr' 或 'tmpub'。\n\n以下资产状态不符，已被系统拒绝：\n{}".format(
                run_type.upper(),
                run_type,
                joined_names
            )
            messagebox.showerror(u"环节状态校验失败", msg)
            return
        # ----------------------------------------------------
        
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

    def run_publish_no_qc(self):
        selected = [name for name, var in self.checkbox_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Warning", u"请至少勾选一个资产。")
            return
            
        pub_mod = self.pub_module.get()
        if not pub_mod:
            messagebox.showwarning("Warning", u"请在 Publish 按钮旁勾选要提交的环节 (UV 或 Tex)。")
            return
            
        proj = self.proj_entry.get()
        asset_name = selected[0]
        
        # 查找类型 (chr, prop...)
        asset_type = "chr"
        if hasattr(self, 'assets_data'):
            for a in self.assets_data:
                name_val = a.get(u"资产名称", "")
                if name_val == asset_name:
                    asset_type = a.get(u"资产类型", "chr")
                    break
        else:
            asset_type = "chr"

        import glob
        qc_dir = os.path.join(r"X:\AI_Automation\Project", proj, r"work\assets", asset_type, asset_name, pub_mod, "QC")
        fixed_files = glob.glob(os.path.join(qc_dir, "*_fixed.blend"))
        fixed_file_path = fixed_files[0] if fixed_files else ""
        
        if not fixed_file_path or not os.path.exists(fixed_file_path):
            messagebox.showerror("Error", u"未找到该资产 %s 环节经过黑箱修正的 _fixed.blend 文件！\n预期路径: %s" % (pub_mod.upper(), qc_dir))
            return
            
        self._show_publish_dialog(proj, asset_type, asset_name, pub_mod, fixed_file_path)

    def _show_publish_dialog(self, proj, asset_type, asset_name, pub_mod, fixed_file_path):
        dlg = tk.Toplevel(self)
        dlg.title(u"提审附属舱 - %s" % asset_name)
        dlg.geometry("600x650")
        dlg.transient(self)
        dlg.grab_set()

        is_publish_mat = self.opt_pub_mat.get()
        # 强制 UV 环节无视 2k 设置
        is_2k = self.opt_2k.get() if pub_mod.lower() == 'tex' else False

        tk.Label(dlg, text=u"[预检查] S盘材质转换: %s | 大小切图: %s" % ("On" if is_publish_mat else "Off", "On" if is_2k else "Off"), fg="grey").pack(pady=5)

        # 1. Mandatory LookDev Image
        tk.Label(dlg, text=u"1. [必填项] 最终效果展示图 (LookDev Thumbnail):", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
        thumb_frm = tk.Frame(dlg)
        thumb_frm.pack(fill="x", padx=15)
        
        thumb_var = tk.StringVar()
        thumb_entry = tk.Entry(thumb_frm, textvariable=thumb_var, width=55, state="readonly", font=("Microsoft YaHei", 9))
        thumb_entry.pack(side="left", fill="x", expand=True)
        
        def sel_thumb():
            f = filedialog.askopenfilename(title=u"选择预览效果图", filetypes=[("Images", "*.jpg *.png *.jpeg")])
            if f:
                thumb_var.set(f)
                
        tk.Button(thumb_frm, text=u"浏览图片...", command=sel_thumb).pack(side="right", padx=(5,0))

        # 2. Optional Attachments
        tk.Label(dlg, text=u"2. [选填项] 附加工程文件包 (存入backup_file):", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
        
        listbox = tk.Listbox(dlg, height=4, width=70)
        listbox.pack(padx=15, fill="x")
        
        attached_files = []
        def add_files():
            fs = filedialog.askopenfilenames(title=u"选择附件工程文件")
            if fs:
                for f in fs:
                    if f not in attached_files:
                        attached_files.append(f)
                        listbox.insert(tk.END, f)
                        
        def clear_files():
            attached_files[:] = []
            listbox.delete(0, tk.END)

        btn_frm = tk.Frame(dlg)
        btn_frm.pack(fill="x", padx=15, pady=2)
        tk.Button(btn_frm, text=u"📎 添加附件 (多选)...", command=add_files).pack(side="left")
        tk.Button(btn_frm, text=u"清空", command=clear_files).pack(side="left", padx=5)

        # 3. Flow Comment
        tk.Label(dlg, text=u"3. Flow/ShotGrid 审核小作文 (Comment):", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
        text_comment = tk.Text(dlg, height=6, width=70, font=("Microsoft YaHei", 9))
        text_comment.pack(padx=15)
        
        def on_confirm():
            if not thumb_var.get():
                messagebox.showerror(u"拦截", u"请务必提供一张最终效果展示图 (LookDev Thumbnail) 作为网格封面！", parent=dlg)
                return
                
            comment_text = text_comment.get("1.0", tk.END).strip()
            dlg.destroy()
            self._execute_publish(proj, asset_type, asset_name, pub_mod, fixed_file_path, is_publish_mat, is_2k, comment_text, thumb_var.get(), attached_files)
            
        tk.Button(dlg, text=u"🚀 确认最终定档发车\n(发射指令并上锁)", bg="#17A2B8", fg="white", font=("Microsoft YaHei", 12, "bold"), command=on_confirm).pack(pady=20, fill="x", padx=30)

    def _execute_publish(self, proj, asset_type, asset_name, pub_mod, fixed_file_path, is_publish_mat, is_2k, comment_text, thumb_file, attached_files):
        # 1. Target Directory Setting
        pub_dir = os.path.join(r"X:\AI_Automation\Project", proj, "pub", "assets", asset_type, asset_name, pub_mod, pub_mod + "Master")
        if not os.path.exists(pub_dir):
            os.makedirs(pub_dir)
            
        # Version Calculation
        import glob
        pattern = "{}_{}_{}_{}_{}Master_v*.blend".format(proj, asset_type, asset_name, pub_mod, pub_mod)
        search_path = os.path.join(pub_dir, pattern)
        files = glob.glob(search_path)
        
        max_v = 0
        for f in files:
            base = os.path.basename(f)
            try:
                v_str = base.split('_v')[-1].split('.blend')[0]
                v_num = int(v_str)
                if v_num > max_v: max_v = v_num
            except: pass
        next_v = max_v + 1
        new_basename = "{}_{}_{}_{}_{}Master_v{:03d}.blend".format(proj, asset_type, asset_name, pub_mod, pub_mod, next_v)
        target_blend = os.path.join(pub_dir, new_basename)

        # Process Files
        import shutil
        try:
            # Handle Mandatory Thumbnail
            if thumb_file and os.path.exists(thumb_file):
                ext = os.path.splitext(thumb_file)[1].lower()
                targ = target_blend.replace('.blend', ext)
                shutil.copy2(thumb_file, targ)

            # Handle Optional Backup files
            for fpath in attached_files:
                backup_dir = os.path.join(pub_dir, 'backup_file')
                if not os.path.exists(backup_dir): os.makedirs(backup_dir)
                shutil.copy2(fpath, os.path.join(backup_dir, os.path.basename(fpath)))
        except Exception as e:
            print("Warning storing attachments:", e)

        import tempfile
        worker_payload = {
            "target_blend": target_blend,
            "is_publish_mat": is_publish_mat,
            "is_2k": is_2k,
            "project": proj,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "module": pub_mod
        }
        worker_json = os.path.join(tempfile.gettempdir(), "headless_worker.json")
        with open(worker_json, 'w') as f:
            json.dump(worker_payload, f)
            
        sg_payload = {
            "project": proj,
            "updates": [{
                "asset_name": asset_name,
                "task_name": pub_mod + "Master",
                "status": "rev",
                "comment": comment_text if comment_text else u"Dashboard Automatic Publish Execute"
            }]
        }
        sg_json = os.path.join(tempfile.gettempdir(), "sg_pub_update.json")
        with open(sg_json, 'w') as f:
            json.dump(sg_payload, f)

        blender_path = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        worker_script = os.path.join(SKILLS_DIR, "publish-element-no-qc", "scripts", "headless_pub_worker.py")
        sg_script = os.path.join(SKILLS_DIR, "sg-data-reader", "scripts", "sg_batch_update.py")

        self.progress.start(15)
        import threading
        def task():
            try:
                # 使用 CMD 并在末尾追加 pause，防止黑窗运行完一闪而过关闭！
                import subprocess
                CREATE_NEW_CONSOLE = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0x10
                
                cmd_worker = '"{}" -b "{}" -P "{}" -- "{}"'.format(blender_path, fixed_file_path, worker_script, worker_json)
                subprocess.call('cmd.exe /c "title 引擎后台算力中... && {} && echo. && echo Engine Finish! && pause"'.format(cmd_worker), creationflags=CREATE_NEW_CONSOLE)
                
                cmd_sg = '"{}" -b -P "{}" -- "{}"'.format(blender_path, sg_script, sg_json)
                subprocess.call('cmd.exe /c "title ShotGrid 同步引擎... && {} && echo. && echo SG Update Finish! && pause"'.format(cmd_sg), creationflags=CREATE_NEW_CONSOLE)
                
            except Exception as e:
                print("Error launching pipeline:", str(e))
            finally:
                try: os.remove(worker_json)
                except: pass
                try: os.remove(sg_json)
                except: pass
                self.after(0, self.progress.stop)
                self.after(0, lambda: messagebox.showinfo("Done", u"定档大货完毕！\n请前往 %s\n查收您的数据。" % pub_dir))
        threading.Thread(target=task).start()

if __name__ == "__main__": 
    app = TexUVDashboard()
    app.mainloop()
