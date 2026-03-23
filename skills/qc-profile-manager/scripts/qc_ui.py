# -*- coding: utf-8 -*-
import sys
import os
import json

# 兼容 Python 2 (Tkinter) 和 Python 3 (tkinter) 的内置 GUI 库
try:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox

TARGET_JSON = r"X:\AI_Automation\.gemini\skills\blender-character-qc\scripts\qc_profiles.json"

ALL_ATOMS = {
    "cameras": u"清除多余相机",
    "lights": u"清除多余灯光",
    "unused_images": u"清理无用的Image节点",
    "unused_materials": u"清理无用的材质球",
    "unused_meshes": u"清理游离无用的Mesh块",
    "extra_scripts": u"清理多余Python脚本",
    "empty_groups": u"清理非法的空组(Empty)",
    "ngons": u"检测模型五边面",
    "transform_reset": u"检查Transform是否归零",
    "illegal_nodes": u"检测场景中非标非法节点",
    "subdivision": u"检查细分修改器规范",
    "uv_negative": u"UV负象限检查",
    "uv_cross_udim": u"UV跨象限(跨界)检查",
    "uv_overlap": u"UV非法重叠检测",
    "uv_inverted": u"反向UV(红面)检查",
    "uv_layer_naming": u"UV通道命名规范(map1/furuvmap)",
    "uv_layer_count": u"UV通道数量限制检查",
    "asset_prefix": u"检查大纲所有物体前缀",
    "mesh_parent_logic": u"Mesh与父组命名对齐检查",
    "data_sync": u"底层Data数据块同步检查",
    "hierarchy_nesting": u"检查Group->cache核心骨架",
    "group_validity": u"特殊组(hiddenMesh等)合法性",
    "facial_nodes": u"ysj项目表情贴图材质规范",
    "texture_consistency": u"贴图物理路径一致性检查(S/X盘)",
    "rig_fix_orig_shape": u"[Rig专属] 清理冗余 Orig Shape 节点",
    "rig_unused_skin": u"[Rig专属] 清理未使用蒙皮影响物",
    "maya_namespace": u"[Maya专属] 清除所有的 Namespace"
}

STEPS = ["uv", "tex", "rig", "lib_qc_step1", "lib_qc_step2"]

class QCProfileManager(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title(u"PPAS - QC 规则调度中心")
        self.geometry("850x650")
        
        self.current_data = {}
        self.vars = {}  # 存储所有的 BooleanVar
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # 顶部标题
        lbl_title = tk.Label(self, text=u"📦 管线质检引擎 (QC Profiles) 动态配置管理", font=("Microsoft YaHei", 14, "bold"), pady=10)
        lbl_title.pack(side=tk.TOP, fill=tk.X)

        # 中间选项卡
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        for step in STEPS:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=u"  环节: {}  ".format(step))
            
            # 使用 Canvas 实现滚动条
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e, canvas=canvas: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            self.vars[step] = {}
            row, col = 0, 0
            for atom_key, atom_name in ALL_ATOMS.items():
                # --- Visibility Filter Logic ---
                # 1. Maya/Rig exclusive atoms should ONLY show in "rig" tab
                if u"[Rig专属]" in atom_name and step != "rig":
                    continue
                if u"[Maya专属]" in atom_name and step != "rig":
                    continue
                
                # 2. Blender exclusive atoms should NEVER show in "rig" tab (Maya environment)
                blender_exclusives = [
                    "unused_meshes", "ngons", "subdivision", 
                    "unused_images", "texture_consistency", "facial_nodes",
                    "uv_negative", "uv_cross_udim", "uv_overlap", "uv_inverted", 
                    "uv_layer_naming", "uv_layer_count", "data_sync"
                ]
                if step == "rig" and atom_key in blender_exclusives:
                    continue
                    
                var = tk.BooleanVar()
                self.vars[step][atom_key] = var
                
                cb_text = u"{} [{}]".format(atom_name, atom_key)
                cb = tk.Checkbutton(scrollable_frame, text=cb_text, variable=var, font=("Microsoft YaHei", 10), justify=tk.LEFT, anchor='w')
                cb.grid(row=row, column=col, sticky="w", padx=10, pady=5)
                
                col += 1
                if col > 1:  # 每行排 2 个
                    col = 0
                    row += 1

        # 底部按钮区
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        btn_refresh = tk.Button(btn_frame, text=u"🔄 重新加载本地配置", font=("Microsoft YaHei", 10), width=20, command=self.load_data)
        btn_refresh.pack(side=tk.LEFT, padx=30)
        
        btn_save = tk.Button(btn_frame, text=u"💾 保存并应用到流水线引擎", font=("Microsoft YaHei", 12, "bold"), bg="#4CAF50", fg="white", width=25, command=self.save_data)
        btn_save.pack(side=tk.RIGHT, padx=30)

    def load_data(self):
        try:
            if os.path.exists(TARGET_JSON):
                with open(TARGET_JSON, 'r') as f:
                    self.current_data = json.load(f)
            else:
                self.current_data = {}
                
            for step in STEPS:
                active_atoms = self.current_data.get(step, [])
                for atom_key, var in self.vars[step].items():
                    var.set(atom_key in active_atoms)
        except Exception as e:
            messagebox.showerror(u"读取失败", u"无法加载配置文件:\n{}".format(e))

    def save_data(self):
        new_data = {}
        for step in STEPS:
            active_atoms = []
            for atom_key, var in self.vars[step].items():
                if var.get():
                    active_atoms.append(atom_key)
            new_data[step] = active_atoms
            
        try:
            with open(TARGET_JSON, 'w') as f:
                json.dump(new_data, f, indent=4)
            messagebox.showinfo(u"保存成功", u"QC 检查项配置已成功写入底层引擎！\n下次运行流水线时即刻生效。")
            self.current_data = new_data
        except Exception as e:
            messagebox.showerror(u"保存失败", u"写入 JSON 文件时发生错误:\n{}".format(e))

if __name__ == "__main__":
    app = QCProfileManager()
    app.mainloop()
