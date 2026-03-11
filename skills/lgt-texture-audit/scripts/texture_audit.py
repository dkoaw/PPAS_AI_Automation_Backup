import bpy
import os
import sys
import math
import re
import time
from bpy.app.handlers import persistent

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False

class TextureAnalyzer:
    @staticmethod
    def _analyze_buffer(pixels, total_pixels, channels):
        if total_pixels == 0: return 1.0, False, False, False
        step = max(1, int(total_pixels / 4096)) * channels
        try:
            _ = pixels[0]; samples = pixels[::step]
        except: return 1.0, False, False, False
        if not samples: return 0.0, True, True, True

        luminance_values = []
        is_greyscale = True; has_alpha = False
        
        for i in range(0, len(samples), 4):
            if i+3 >= len(samples): break
            r, g, b, a = samples[i], samples[i+1], samples[i+2], samples[i+3]
            lum = 0.2126*r + 0.7152*g + 0.0722*b
            luminance_values.append(lum)
            if abs(r - g) > 0.005 or abs(g - b) > 0.005: is_greyscale = False
            if a < 0.999: has_alpha = True
            
        if not luminance_values: return 0.0, True, True, True
        mean = sum(luminance_values) / len(luminance_values)
        variance = sum((x - mean) ** 2 for x in luminance_values) / len(luminance_values)
        std_dev = math.sqrt(variance)
        return std_dev, (std_dev < 0.005), is_greyscale, has_alpha

    @staticmethod
    def analyze_tile(image, tile_index=None):
        if not image.has_data:
            try: image.reload(); _ = image.pixels[0]
            except: return 1.0, False, False, True
        if tile_index is not None and image.source == 'TILED':
            try:
                if image.tiles.active_index != tile_index:
                    image.tiles.active_index = tile_index; _ = image.pixels[0] 
            except: return 1.0, False, False, True
        return TextureAnalyzer._analyze_buffer(image.pixels, image.size[0]*image.size[1], image.channels)

    @staticmethod
    def get_memory_info(image):
        bytes_per_chan = 4 
        base_mb = (image.size[0] * image.size[1] * 4 * bytes_per_chan) / (1024 * 1024)
        
        tile_count = 1
        if hasattr(image, "tiles") and len(image.tiles) > 0: tile_count = len(image.tiles)
        total_mb = base_mb * tile_count
        return total_mb, tile_count, image.is_float

if HAS_PYSIDE:
    class TextureAuditDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("贴图优化审计 V14.7 (修复UDIM列表检索Bug版)")
            self.resize(1500, 800)
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            self.init_ui()
        def init_ui(self):
            l = QtWidgets.QVBoxLayout(self)
            l.addWidget(QtWidgets.QLabel("已修复 UI 名称修改导致 Blender 实体对象查找失败进而漏掉 UDIM 序列的 Bug。"))
            self.table = QtWidgets.QTableWidget(); self.table.setColumnCount(11)
            self.table.setHorizontalHeaderLabels(["Tile", "名称", "尺寸", "位深", "当前显存", "优化后(MB)", "复杂度", "色彩", "建议", "状态", "格式建议"])
            self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            self.table.setSortingEnabled(True) 
            l.addWidget(self.table)
            stats_box = QtWidgets.QFrame(); stats_box.setStyleSheet("background-color: #333; border-radius: 5px; padding: 10px;")
            stats_l = QtWidgets.QHBoxLayout(stats_box)
            self.lbl_total_vram = QtWidgets.QLabel("贴图总显存 (保守): 0 MB"); self.lbl_total_vram.setStyleSheet("font-size: 16px; font-weight: bold; color: #EEE;")
            stats_l.addWidget(self.lbl_total_vram); stats_l.addStretch(); l.addWidget(stats_box)
            btn_box = QtWidgets.QHBoxLayout()
            btn = QtWidgets.QPushButton("开始全面分析"); btn.clicked.connect(self.run); btn.setFixedHeight(40); btn_box.addWidget(btn)
            btn_opt = QtWidgets.QPushButton("执行优化并重定向至 fix_texture"); btn_opt.clicked.connect(self.run_optimization); btn_opt.setFixedHeight(40); btn_box.addWidget(btn_opt)
            btn_opt.setStyleSheet("background-color: #533; font-weight: bold;")
            l.addLayout(btn_box)
            self.prog = QtWidgets.QProgressBar(); l.addWidget(self.prog)

        def _get_actual_udim_path(self, base_path, tile_id_str):
            if not tile_id_str: return base_path
            if "<UDIM>" in base_path:
                return base_path.replace("<UDIM>", tile_id_str)
            match = re.search(r'\.(\d{4})\.', base_path)
            if match:
                return base_path[:match.start(1)] + tile_id_str + base_path[match.end(1):]
            match = re.search(r'(\d{4})', base_path)
            if match:
                head, sep, tail = base_path.rpartition(match.group(1))
                return head + tile_id_str + tail
            return base_path

        def run_optimization(self):
            import subprocess
            import shutil
            import os
            target_base_dir = r"X:\Project\ysj\pub\lgt_comp\lookdev\gaogeyaoguai\fix_texture"
            if self.table.rowCount() == 0:
                QtWidgets.QMessageBox.warning(self, "警告", "请先点击【开始全面分析】获取优化建议，然后再执行优化！")
                return
            all_paths = []
            valid_tasks = []
            for row in range(self.table.rowCount()):
                name_item = self.table.item(row, 1)
                img_name = name_item.data(QtCore.Qt.UserRole)
                if not img_name:
                     img_name = name_item.text()
                tile_item = self.table.item(row, 0)
                tile_id_str = tile_item.text() if tile_item else ""
                img = bpy.data.images.get(img_name)
                if img and img.source in ['FILE', 'TILED', 'SEQUENCE'] and img.filepath:
                    try:
                        base_path = os.path.normpath(bpy.path.abspath(img.filepath))
                        actual_path = base_path
                        if img.source == 'TILED' and tile_id_str:
                            actual_path = self._get_actual_udim_path(base_path, tile_id_str)
                        if os.path.exists(actual_path):
                            all_paths.append(actual_path)
                            valid_tasks.append((row, img, actual_path, base_path))
                    except: pass
            if not all_paths:
                QtWidgets.QMessageBox.warning(self, "警告", "没有找到任何有效的实体贴图文件！")
                return
            drives = set(os.path.splitdrive(p)[0].upper() for p in all_paths)
            if len(drives) > 1:
                QtWidgets.QMessageBox.critical(self, "错误", f"资产跨越了多个盘符，原则上不允许！检测到的盘符: {', '.join(drives)}")
                return
            common_prefix = os.path.commonpath(all_paths)
            if os.path.isfile(common_prefix):
                common_prefix = os.path.dirname(common_prefix)
            self.prog.setMaximum(len(valid_tasks)); self.prog.setValue(0)
            processed_count = 0
            updated_images = {}
            for step, (row, img, actual_path, base_path) in enumerate(valid_tasks):
                self.prog.setValue(step + 1); QtWidgets.QApplication.processEvents()
                sugg_res = self.table.item(row, 8).text()
                fmt_sugg = self.table.item(row, 10).text()
                rel_path = os.path.relpath(actual_path, common_prefix)
                new_filepath = os.path.join(target_base_dir, rel_path)
                new_dir = os.path.dirname(new_filepath)
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir, exist_ok=True)
                cmd_args = []
                needs_optimization = not (sugg_res == "Keep" and fmt_sugg == "OK")
                if needs_optimization:
                    if sugg_res == "-> 64px": cmd_args.append('-resize "64x64>"')
                    elif sugg_res == "-> 1K": cmd_args.append('-resize "1024x1024>"')
                    if "转BW" in fmt_sugg: cmd_args.append('-colorspace gray')
                    if "去Alpha" in fmt_sugg: cmd_args.append('-alpha off')
                    if "转8bit" in fmt_sugg: cmd_args.append('-depth 8')
                    if actual_path.lower().endswith('.exr'): cmd_args.append('-compress dwaa')
                do_process = False
                if not os.path.exists(new_filepath):
                    do_process = True
                else:
                    try:
                        if os.path.getmtime(actual_path) > os.path.getmtime(new_filepath):
                            do_process = True
                    except:
                        do_process = True
                if do_process:
                    if needs_optimization and cmd_args:
                        cmd_str = f'magick "{actual_path}" {" ".join(cmd_args)} "{new_filepath}"'
                        try: subprocess.run(cmd_str, check=True, shell=True)
                        except Exception as e: continue
                    else:
                        try: shutil.copy2(actual_path, new_filepath)
                        except Exception as e: continue
                if os.path.exists(new_filepath):
                    processed_count += 1
                    if img not in updated_images:
                        rel_base = os.path.relpath(base_path, common_prefix)
                        new_base_filepath = os.path.join(target_base_dir, rel_base)
                        updated_images[img] = new_base_filepath
            for img, new_base_path in updated_images.items():
                img.filepath = new_base_path
                img.reload()
            QtWidgets.QMessageBox.information(self, "完成", f"处理完成！共处理/迁移并重定向了 {processed_count} 张贴图（含UDIM序列）。基础路径: {target_base_dir}")

        def add_row(self, name, size_str, mem_mb, score, is_solid, is_grey, has_alpha, is_float, depth, tile_id=""):
            w, h = map(int, size_str.split('x'))
            mx = max(w, h)
            target_mem = mem_mb
            sugg_res = "Keep"; stat = "OK"; col = None
            if is_solid:
                if mx>64: 
                    sugg_res="-> 64px"; stat="极浪费"; col=QtGui.QColor(255,100,100)
                    target_mem = target_mem * ((64.0*64.0)/(w*h))
            elif score<0.02 and mx>1024:
                sugg_res="-> 1K"; stat="建议降级"; col=QtGui.QColor(255,200,100)
                target_mem = target_mem / 16.0
            fmt_sugg = []
            is_env_format = ("hdr" in name.lower() or "exr" in name.lower())
            file_chans = 4
            if is_float:
                if depth in (32, 16): file_chans = 1
                elif depth in (96, 48): file_chans = 3
                elif depth in (128, 64): file_chans = 4
            else:
                if depth in (8, 16): file_chans = 1
                elif depth in (24, 48): file_chans = 3
                elif depth in (32, 64): file_chans = 4
            target_chans = file_chans
            if is_grey:
                if file_chans > 1:
                    fmt_sugg.append("转BW")
                target_chans = 1.0
            elif not has_alpha:
                if file_chans == 4 and not is_env_format:
                    fmt_sugg.append("去Alpha")
                target_chans = 3.0
            target_mem = target_mem * (target_chans / 4.0)
            if is_float:
                if "disp" not in name.lower() and not is_env_format:
                    fmt_sugg.append("转8bit")
                    target_mem = target_mem / 4.0 
            fmt_str = ", ".join(fmt_sugg) if fmt_sugg else "OK"
            if fmt_str == "OK" and sugg_res == "Keep":
                target_mem = mem_mb
            if fmt_str != "OK":
                if stat == "OK": stat = "格式可优"; col = QtGui.QColor(200, 200, 255)
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(tile_id)))
            display_name = name
            if tile_id:
                 img_obj = bpy.data.images.get(name)
                 if img_obj and img_obj.filepath:
                     base_path = os.path.basename(bpy.path.abspath(img_obj.filepath))
                     display_name = self._get_actual_udim_path(base_path, str(tile_id))
            name_item = QtWidgets.QTableWidgetItem(display_name)
            name_item.setData(QtCore.Qt.UserRole, name)
            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(size_str))
            depth_str = "Float" if is_float else "Byte"
            self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(depth_str))
            mem_item = QtWidgets.QTableWidgetItem(f"{mem_mb:.1f}"); mem_item.setData(QtCore.Qt.UserRole, mem_mb)
            self.table.setItem(r, 4, mem_item)
            opt_item = QtWidgets.QTableWidgetItem(f"{target_mem:.1f}"); opt_item.setData(QtCore.Qt.UserRole, target_mem)
            if target_mem < mem_mb * 0.9: opt_item.setBackground(QtGui.QColor(200, 255, 200))
            self.table.setItem(r, 5, opt_item)
            self.table.setItem(r, 6, QtWidgets.QTableWidgetItem(f"{score:.4f}"))
            color_type = "纯色" if is_solid else ("灰度" if is_grey else "彩色")
            self.table.setItem(r, 7, QtWidgets.QTableWidgetItem(color_type))
            self.table.setItem(r, 8, QtWidgets.QTableWidgetItem(sugg_res))
            it = QtWidgets.QTableWidgetItem(stat)
            if col: it.setBackground(col); it.setForeground(QtCore.Qt.black)
            self.table.setItem(r, 9, it)
            self.table.setItem(r, 10, QtWidgets.QTableWidgetItem(fmt_str))
            return mem_mb, target_mem

        def run(self):
            imgs = [i for i in bpy.data.images if i.source in ['FILE', 'TILED', 'SEQUENCE']]
            self.table.setRowCount(0); self.table.setSortingEnabled(False)
            self.prog.setMaximum(len(imgs)*2); total_mem=0.0; total_opt=0.0
            step = 0
            for img in imgs:
                step+=1; self.prog.setValue(step); QtWidgets.QApplication.processEvents()
                is_float = img.is_float
                depth = img.depth
                if img.source == 'TILED':
                    orig_idx = img.tiles.active_index
                    for i, tile in enumerate(img.tiles):
                        score, is_solid, is_grey, has_alpha = TextureAnalyzer.analyze_tile(img, i)
                        mem_mb, _, _ = TextureAnalyzer.get_memory_info(img)
                        single_tile_mb = mem_mb / len(img.tiles)
                        m, o = self.add_row(img.name, f"{img.size[0]}x{img.size[1]}", single_tile_mb, score, is_solid, is_grey, has_alpha, is_float, depth, tile.number)
                        total_mem += m; total_opt += o
                    img.tiles.active_index = orig_idx
                else:
                    score, is_solid, is_grey, has_alpha = TextureAnalyzer.analyze_tile(img, None)
                    mem_mb, _, _ = TextureAnalyzer.get_memory_info(img)
                    m, o = self.add_row(img.name, f"{img.size[0]}x{img.size[1]}", mem_mb, score, is_solid, is_grey, has_alpha, is_float, depth, "")
                    total_mem += m; total_opt += o
            gb_val = total_mem / 1024.0; gb_opt = total_opt / 1024.0; saved = gb_val - gb_opt
            self.lbl_total_vram.setText(f"贴图总显存 (保守): {gb_val:.2f} GB -> 优化后: {gb_opt:.2f} GB (省 {saved:.2f} GB)")
            self.table.setSortingEnabled(True)
            self.prog.setValue(self.prog.maximum())
            QtWidgets.QMessageBox.information(self,"完成",f"分析结束。总占用: {gb_val:.2f} GB")

qt_audit_ref = None
def show_qt_audit():
    global qt_audit_ref; app=QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    qt_audit_ref = TextureAuditDialog(); qt_audit_ref.show()

class PPAS_OT_AuditTextures(bpy.types.Operator):
    bl_idname = "ppas.audit_textures"; bl_label = "贴图内容审计"
    def execute(self, ctx):
        if not HAS_PYSIDE: return {'CANCELLED'}
        show_qt_audit(); return {'FINISHED'}

classes = (PPAS_OT_AuditTextures,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
