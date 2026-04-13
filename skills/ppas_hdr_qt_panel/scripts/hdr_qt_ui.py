try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui
    except ImportError:
        pass # 假设环境已配置特定 Qt 包

class HdrUIControlPanel(QtWidgets.QWidget):
    """
    纯粹的、全盲（无掺杂业务核心）界层 UI 控件。
    作为发射台（View端），全靠外部管家注入数据与连接线。
    """
    
    sig_push_to_engine = QtCore.Signal(dict) 
    sig_request_info = QtCore.Signal()
    sig_no_img_mode_toggled = QtCore.Signal(bool)
    sig_check_auth = QtCore.Signal()
    sig_request_cache_update = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HDR贴图选择器 -- v1.0.0 (管线鉴权版)")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(450, 700)
        self.setStyleSheet("background-color: #2b2b2b; color: #dfdfdf;")
        
        # 建立数据池
        self.current_data_pack = {
            "path": "",
            "r_x": 0.0,
            "r_y": 0.0,
            "r_z": 0.0,
            "purity": 1.0,
            "power": 1.0,
            "val": 1.0,
            "no_img_mode": False
        }
        
        self._build_ui()
        self._bind_internal_events()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # [顶部操纵杆]
        self.btn_update_info = QtWidgets.QPushButton("更新 HDR 信息 (从层级回读)")
        self.btn_no_img = QtWidgets.QPushButton("无图纯色模式")
        self.btn_no_img.setCheckable(True)
        
        for btn in [self.btn_update_info, self.btn_no_img]:
            btn.setMinimumHeight(35)
            btn.setStyleSheet("background-color: #404a57; border-radius: 4px;")
            main_layout.addWidget(btn)
            
        main_layout.addSpacing(10)
        
        # [中部滑块舱]
        self.param_group = QtWidgets.QGroupBox("")
        param_layout = QtWidgets.QFormLayout(self.param_group)
        
        self.sld_r_z = self._create_slider_row("水平(Z):", -180.0, 180.0, 0.0, param_layout, decimals=2)
        self.sld_r_x = self._create_slider_row("X轴:", -180.0, 180.0, 0.0, param_layout, decimals=2)
        self.sld_r_y = self._create_slider_row("Y轴:", -180.0, 180.0, 0.0, param_layout, decimals=2)
        self.sld_power = self._create_slider_row("亮度(Strength):", 0.0, 50.0, 1.0, param_layout, decimals=3)
        self.sld_purity = self._create_slider_row("纯度(Sat):", 0.0, 2.0, 1.0, param_layout, decimals=3)
        
        main_layout.addWidget(self.param_group)
        
        # [底部画廊池]
        lbl = QtWidgets.QLabel("HDR贴图列表")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(lbl)
        
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #2b2b2b; }")
        
        self.gallery_container = QtWidgets.QWidget()
        self.gallery_layout = QtWidgets.QVBoxLayout(self.gallery_container)
        self.gallery_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_layout.setSpacing(8)
        self.scroll_area.setWidget(self.gallery_container)
        
        main_layout.addWidget(self.scroll_area)
        
        # [极速索引器层]
        self.btn_update_cache = QtWidgets.QPushButton("更新 HDR 贴图库索引 (重扫网络盘)")
        self.btn_update_cache.setMinimumHeight(40)
        self.btn_update_cache.setStyleSheet("background-color: #3b5042; border-radius: 4px; font-weight: bold; color: #a1d1b1;")
        main_layout.addWidget(self.btn_update_cache)
        
        # 拦截罩 (鉴权失败时的 UI 顶层遮罩)
        self.shield_label = QtWidgets.QLabel("管线安全阻遏：当前环境为界外图层！\nHDR 管理器已进入物理休眠禁闭锁死。")
        self.shield_label.setStyleSheet("color: #ff5555; background-color: rgba(30, 0, 0, 200); font-weight: bold;")
        self.shield_label.setAlignment(QtCore.Qt.AlignCenter)
        self.shield_label.hide()
        
    def _create_slider_row(self, name, spin_min, spin_max, spin_def, layout, decimals=2):
        row_widget = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(row_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        factor = 10.0 ** decimals
        
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(spin_min, spin_max)
        spin.setDecimals(decimals)
        spin.setSingleStep(1.0 / factor)
        spin.setValue(spin_def)
        
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(int(spin_min * factor), int(spin_max * factor))
        slider.setValue(int(spin_def * factor))
        
        # 同步推拉
        slider.valueChanged.connect(lambda v: spin.setValue(v / factor))
        spin.valueChanged.connect(lambda v: slider.setValue(int(v * factor)))
        
        h_layout.addWidget(spin)
        h_layout.addWidget(slider)
        
        layout.addRow(name, row_widget)
        
        # 将 factor 和 spin 绑定为属性方便读取真实值与同步
        slider.factor = factor
        slider.spin = spin
        return slider

    def _bind_internal_events(self):
        # UI 内部交互汇总至包发射点
        self.btn_update_cache.clicked.connect(self.sig_request_cache_update.emit)
        # 列表的响应事件已移至 load_gallery_data 内部动态挂载
        
        # 滑块实时推拉：直接驱动引擎底层执行数据绑定
        for sld in [self.sld_r_x, self.sld_r_y, self.sld_r_z, self.sld_power, self.sld_purity]:
            sld.valueChanged.connect(self._emit_push)
            
        self.btn_update_info.clicked.connect(self.sig_request_info.emit)

    def load_gallery_data(self, asset_dict):
        """外部 Controller 提供解析完毕的字典，供 UI 显示"""
        # 清理旧组件
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # 保存所有新建的分类画廊列表，以便管理交互
        self._category_lws = []
                
        for cat, items in asset_dict.items():
            if not items: continue
            
            cat_btn = QtWidgets.QPushButton(cat)
            cat_btn.setStyleSheet("""
                QPushButton { background-color: #556677; padding: 6px; font-weight: bold; border-radius: 2px; text-align: left; }
                QPushButton:hover { background-color: #667788; }
            """)
            self.gallery_layout.addWidget(cat_btn)
            
            lw = QtWidgets.QListWidget()
            lw.setIconSize(QtCore.QSize(160, 90))
            lw.setSpacing(5)
            lw.setViewMode(QtWidgets.QListView.IconMode)
            lw.setResizeMode(QtWidgets.QListView.Adjust)
            lw.setWordWrap(True)
            lw.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333;")
            
            for f_item in items:
                # 第二项需求：严格拦截没有 PNG/JPG 缩略图的 HDR
                if not f_item["thumbnail_path"]:
                    continue
                    
                li = QtWidgets.QListWidgetItem(f_item["name"])
                li.setData(QtCore.Qt.UserRole, f_item["hdr_path"])
                li.setIcon(QtGui.QIcon(f_item["thumbnail_path"]))
                lw.addItem(li)
                
            if lw.count() > 0:
                # 给一个合适的高度算法：大约一行 3 个，每行高 120。限定最高 260，超出则出现内部滚动条
                row_count = (lw.count() + 2) // 3
                calc_h = min(280, row_count * 130 + 10)
                lw.setFixedHeight(calc_h)
                
                # 默认只展开第一个（或者全收起，视体验而定。这里默认全部收起，非常清爽）
                lw.setVisible(False)
                
                # 动态绑定折叠事件
                def make_toggle_func(widget):
                    return lambda: widget.setVisible(not widget.isVisible())
                cat_btn.clicked.connect(make_toggle_func(lw))
                
                self.gallery_layout.addWidget(lw)
                self._category_lws.append(lw)
                lw.itemSelectionChanged.connect(self._on_gallery_select)
                lw.itemDoubleClicked.connect(self._on_gallery_double_click)
            else:
                cat_btn.deleteLater()
                lw.deleteLater()
                
        self.gallery_layout.addStretch()

    def load_data_pack(self, data_pack):
        """
        [关键逻辑：同步回读] 
        根据传入的 Blender 层级参数包，强行同步 UI 界面。
        """
        import math
        # 1. 深度克隆数据，防止引用污染
        self.current_data_pack = data_pack.copy()
        
        # 2. 拉回所有滑块（反向弧度转角度）
        sliders_and_keys = [
            (self.sld_r_x, "r_x", True),
            (self.sld_r_y, "r_y", True),
            (self.sld_r_z, "r_z", True),
            (self.sld_power, "power", False),
            (self.sld_purity, "purity", False)
        ]
        
        for sld, key, is_rad in sliders_and_keys:
            sld.blockSignals(True)
            if hasattr(sld, "spin"):
                sld.spin.blockSignals(True)
            
            # 计算真实浮点值
            val_real = data_pack.get(key, 0.0)
            if is_rad: val_real = math.degrees(val_real)
            
            # 填入组件
            sld.setValue(int(val_real * sld.factor))
            if hasattr(sld, "spin"):
                sld.spin.setValue(val_real)
                
            if hasattr(sld, "spin"):
                sld.spin.blockSignals(False)
            sld.blockSignals(False)
            
        # 3. 列表状态匹配：如果路径为空，清空选择；如果不为空，尝试选中对应的项
        target_path = data_pack.get("path", "")
        for lw in getattr(self, "_category_lws", []):
            lw.blockSignals(True)
            lw.clearSelection()
            if target_path:
                for i in range(lw.count()):
                    item = lw.item(i)
                    if item.data(QtCore.Qt.UserRole) == target_path:
                        item.setSelected(True)
                        lw.scrollToItem(item)
            lw.blockSignals(False)

    def _on_gallery_select(self):
        snd = self.sender()
        if not snd: return
        
        sel = snd.selectedItems()
        if not sel: return
        
        # 维持排他的单选逻辑：跨列表互斥
        for lw in getattr(self, "_category_lws", []):
            if lw != snd:
                # [修复] 必须 blockSignals 否则 clearSelection 会导致高频死循环递归，Blender 容易假死
                lw.blockSignals(True)
                lw.clearSelection()
                lw.blockSignals(False)
                
        path = sel[0].data(QtCore.Qt.UserRole)
        if path:
            self.current_data_pack["path"] = path
            # [修改]：列表点击不再触发引擎同步，仅做管线拦截探针 (Condition check)
            self.sig_check_auth.emit()

    def _on_gallery_double_click(self, item):
        path = item.data(QtCore.Qt.UserRole)
        if path:
            self.current_data_pack["path"] = path
            # 双击则触发正式上图，真正向引擎执行推流
            self._emit_push()

    def _emit_push(self):
        import math
        # 提取瞬时盘面数值打包
        # Blender 节点内部吃的是弧度，UI 显示的是角度，这里完成换算
        self.current_data_pack["r_x"] = math.radians(self.sld_r_x.value() / self.sld_r_x.factor)
        self.current_data_pack["r_y"] = math.radians(self.sld_r_y.value() / self.sld_r_y.factor)
        self.current_data_pack["r_z"] = math.radians(self.sld_r_z.value() / self.sld_r_z.factor)
        
        self.current_data_pack["power"] = self.sld_power.value() / self.sld_power.factor
        self.current_data_pack["purity"] = self.sld_purity.value() / self.sld_purity.factor
        
        # 向外（Controller）投射，UI 本身浑然不知 Blender 的存在
        self.sig_push_to_engine.emit(self.current_data_pack)

    def lock_shield(self, msg="鉴权失败：已锁死"):
        """遭受引擎底层制裁，UI 提示非法环境，但不强制禁用按钮以便用户切换后重试"""
        # [修改] 移除 setDisabled，仅做视觉警告提示
        # self.param_group.setDisabled(True)
        # self.scroll_area.setDisabled(True)
        # self.btn_update_nodes.setDisabled(True)
        # self.btn_update_info.setDisabled(True)
        
        # 抛出抢眼的警告提示
        self.shield_label.setText(msg)
        self.shield_label.show()
        
    def unlock_shield(self):
        """验证通过，恢复视觉状态"""
        # self.param_group.setDisabled(False)
        # self.scroll_area.setDisabled(False)
        # self.btn_update_nodes.setDisabled(False)
        # self.btn_update_info.setDisabled(False)
        
        self.shield_label.hide()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = HdrUIControlPanel()
    w.show()
    sys.exit(app.exec_())
