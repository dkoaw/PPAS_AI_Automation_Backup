import bpy
import sys
import os

# 注册同级目录以便模块动态导入
script_dir = os.path.dirname(__file__)
if script_dir not in sys.path:
    sys.path.append(script_dir)
import ppas_layer_core

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False

if HAS_PYSIDE:
    class RenderLayerMainWidget(QtWidgets.QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle(u"渲染层管理工具 (空壳待接入)")
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            self.resize(500, 880)
            self.create_widgets()
            self.create_layouts()
            self.init_project_info()

        def init_project_info(self):
            """自动解析当前项目并更新下拉框"""
            self.do_full_refresh()

        def do_full_refresh(self):
            self.refresh_project_name()
            self.refresh_scene_list()

        def refresh_project_name(self):
            filepath = bpy.data.filepath
            project_name = "未保存"
            if filepath:
                project_name = "非管线路径"
                norm_path = os.path.normpath(filepath)
                parts = norm_path.split(os.sep)
                for i, p in enumerate(parts):
                    if p.lower() == "project" and i + 1 < len(parts):
                        project_name = parts[i + 1]
                        break
            
            self._project_cb_.clear()
            self._project_cb_.addItem(project_name)

        def create_widgets(self):
            # 渲染层管理工具标题
            self._toolkit_title_lb_ = QtWidgets.QLabel(u'渲染层管理工具')
            self._toolkit_title_lb_.setAlignment(QtCore.Qt.AlignCenter)

            # 项目信息
            self._project_infos_gb_ = QtWidgets.QGroupBox('')
            self._project_lb_ = QtWidgets.QLabel(u'项目:')
            self._project_cb_ = QtWidgets.QComboBox()
            self._project_cb_.setMinimumWidth(150)
            self._project_cb_.setEnabled(False)
            
            self._project_refresh_pb_ = QtWidgets.QPushButton(u'全部刷新')
            self._project_refresh_pb_.setMaximumWidth(80)
            self._project_refresh_pb_.clicked.connect(self.do_full_refresh)

            # --- 全局核心装配 ---
            self._global_tools_gb_ = QtWidgets.QGroupBox(u'【顶层环境装配】')
            self._global_set_master_pb_ = QtWidgets.QPushButton(u'全局设置 (指定为主层)')
            self._global_clear_master_pb_ = QtWidgets.QPushButton(u'清除母层')
            self._global_set_res_pb_ = QtWidgets.QPushButton(u'设置分辨率与帧率')
            self._global_sync_pb_ = QtWidgets.QPushButton(u'当前参数全域强制同步')

            # 添加层区块
            self._append_layer_gb_ = QtWidgets.QGroupBox('')
            self._layer_tabs_ = QtWidgets.QTabWidget()
            
            # Cycles 组
            self._append_color_layer_pb_ = QtWidgets.QPushButton(u'添加 chr_color 层')
            self._append_env_color_layer_pb_ = QtWidgets.QPushButton(u'添加 场景Color 层')
            self._append_hdr_layer_pb_ = QtWidgets.QPushButton(u'添加 HDR 层')
            self._append_cyc_light_layer_pb_ = QtWidgets.QPushButton(u'添加 CYCLES 光照层')
            self._append_cyc_hdr_layer_pb_ = QtWidgets.QPushButton(u'添加 CYCLES HDR 层')
            self._append_3d_layer_pb_ = QtWidgets.QPushButton(u'添加 3D 光照层')
            self._append_emi_layer_pb_ = QtWidgets.QPushButton(u'添加 Emission 层')
            self._append_shadow_layer_pb_ = QtWidgets.QPushButton(u'添加 Shadow 层')
            self._append_sss_layer_pb_ = QtWidgets.QPushButton(u'添加 SSS 渲染层 (调用专板)')
            
            # Eevee 组
            self._append_line_layer_pb_ = QtWidgets.QPushButton(u'添加 Line 层')
            self._append_fog_layer_pb_ = QtWidgets.QPushButton(u'添加 Fog 层')
            self._2d_texture_lb_ = QtWidgets.QLabel(u'2D 材质:')
            self._2d_texture_cb_ = QtWidgets.QComboBox()
            self._2d_texture_cb_.addItems(["基础黑白遮罩", "通用贴花光"])
            self._append_2d_layer_pb_ = QtWidgets.QPushButton(u'添加 2D 光照层')
            self._append_piercing_layer_pb_ = QtWidgets.QPushButton(u'添加 CBCS 层（唯一）')

            # 附加独立模块接入 (红线位置)
            self._launch_hdr_manager_pb_ = QtWidgets.QPushButton(u'启动独立 HDR 贴图选择器面板')
            self._launch_hdr_manager_pb_.setStyleSheet("background-color: #3b5066; font-weight: bold; padding: 6px;")
            
            # 层编辑器区块
            self._layer_editor_gb_ = QtWidgets.QGroupBox(u'')
            self._layer_editor_st_ = QtWidgets.QSplitter()
            self._layer_editor_st_.setOrientation(QtCore.Qt.Horizontal)
            self._render_layer_list_wt_ = QtWidgets.QWidget()

            self._render_layer_list_lb_ = QtWidgets.QLabel(u'场景列表')
            self._render_layer_list_lb_.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  
            self._render_layer_list_lw_ = QtWidgets.QListWidget()
            
            self._hide_obj_list_wt_ = QtWidgets.QWidget()
            self._hide_obj_list_lb_ = QtWidgets.QLabel(u'当前场景包含的层 (ViewLayers)')
            self._hide_obj_list_lb_.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)      
            self._hide_obj_list_lw_ = QtWidgets.QListWidget()

            self._delete_selected_scene_pb_ = QtWidgets.QPushButton(u'删除选中场景')
            self._delete_selected_viewlayer_pb_ = QtWidgets.QPushButton(u'删除选中层')

            self._clear_all_layers_pb_ = QtWidgets.QPushButton(u'清空所有场景')
            self._duplicate_selected_layers_pb_ = QtWidgets.QPushButton(u'复制选中场景')

            # 附加功能区块
            self._plus_tools_gb_ = QtWidgets.QGroupBox('')
            self._create_collection_pb_ = QtWidgets.QPushButton(u'创建 collection ')      
            self._append_collection_pb_ = QtWidgets.QPushButton(u'添加 collection 到场景')
            self._remove_collections_pb_ = QtWidgets.QPushButton(u'删除 collection')      
            self._light_fog_tool_pb_ = QtWidgets.QPushButton(u'灯光雾工具')
            self._create_fog_cube_pb_ = QtWidgets.QPushButton(u'创建 Fog cube')
            self._set_convert_common_shot_pb_ = QtWidgets.QPushButton(u'Set 转常规镜头文件')

        def append_frame(self):
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.HLine)
            return frame

        def create_layouts(self):
            self._layout_ = QtWidgets.QVBoxLayout(self)
            self._layout_.addWidget(self._toolkit_title_lb_)

            # 项目信息布局
            self._layout_.addWidget(self._project_infos_gb_)
            info_lay = QtWidgets.QHBoxLayout(self._project_infos_gb_)
            info_lay.addWidget(self._project_lb_)
            info_lay.addWidget(self._project_cb_)
            info_lay.addWidget(self._project_refresh_pb_)
            info_lay.addStretch(True)

            # 全局功能布局
            self._layout_.addWidget(self._global_tools_gb_)
            global_lay = QtWidgets.QHBoxLayout(self._global_tools_gb_)
            global_lay.addWidget(self._global_set_master_pb_)
            # global_lay.addWidget(self._global_clear_master_pb_)  # 按规范强制移除易损坏按钮
            global_lay.addWidget(self._global_set_res_pb_)
            global_lay.addWidget(self._global_sync_pb_)

            # 添加层布局
            self._layout_.addWidget(self._append_layer_gb_)
            self._append_layer_lay_ = QtWidgets.QVBoxLayout(self._append_layer_gb_)
            self._append_layer_lay_.addWidget(self._layer_tabs_)
            
            # Cycles Layout
            self._cycles_tab_ = QtWidgets.QWidget()
            cyc_lay = QtWidgets.QVBoxLayout(self._cycles_tab_)
            cyc_lay.addWidget(self._append_cyc_light_layer_pb_)
            cyc_lay.addWidget(self._append_cyc_hdr_layer_pb_)
            
            self._cycles_placeholder_ = QtWidgets.QLabel("其它预留物理层等待接入...")
            self._cycles_placeholder_.setAlignment(QtCore.Qt.AlignCenter)
            cyc_lay.addWidget(self._cycles_placeholder_)
            cyc_lay.addStretch()
            self._layer_tabs_.addTab(self._cycles_tab_, "CYCLES 渲染层")
            
            # Eevee Layout
            self._eevee_tab_ = QtWidgets.QWidget()
            eev_lay = QtWidgets.QVBoxLayout(self._eevee_tab_)
            # 正式将各渲染层放入 Eevee UI 布局中
            eev_lay.addWidget(self._append_color_layer_pb_)
            # eev_lay.addWidget(self._append_line_layer_pb_) # 按用户要求暂时隐藏
            eev_lay.addWidget(self._append_hdr_layer_pb_)
            eev_lay.addWidget(self._append_3d_layer_pb_)
            eev_lay.addWidget(self._append_sss_layer_pb_)
            eev_lay.addWidget(self._append_2d_layer_pb_)
            eev_lay.addStretch()
            self._layer_tabs_.addTab(self._eevee_tab_, "EEVEE / 特殊风格层")

            # 插入独立 HDR 工具启动按钮
            self._layout_.addWidget(self._launch_hdr_manager_pb_)

            # 层编辑器布局
            self._layout_.addWidget(self._layer_editor_gb_)
            render_layer_lay = QtWidgets.QVBoxLayout(self._layer_editor_gb_)
            
            # 左侧：场景列表 + 删除场景
            render_lay = QtWidgets.QVBoxLayout(self._render_layer_list_wt_)
            render_lay.addWidget(self._render_layer_list_lb_)
            render_lay.addWidget(self._render_layer_list_lw_)
            render_lay.addWidget(self._delete_selected_scene_pb_)

            # 右侧：层列表 + 删除层
            hide_lay = QtWidgets.QVBoxLayout(self._hide_obj_list_wt_)
            hide_lay.addWidget(self._hide_obj_list_lb_)
            hide_lay.addWidget(self._hide_obj_list_lw_)
            hide_lay.addWidget(self._delete_selected_viewlayer_pb_)

            self._layer_editor_st_.addWidget(self._render_layer_list_wt_)
            self._layer_editor_st_.addWidget(self._hide_obj_list_wt_)
            self._layer_editor_st_.setSizes([250, 300])
            render_layer_lay.addWidget(self._layer_editor_st_)
            
            render_layer_lay.addWidget(self.append_frame())
            editor_lay = QtWidgets.QHBoxLayout()
            editor_lay.addWidget(self._duplicate_selected_layers_pb_)
            editor_lay.addWidget(self._clear_all_layers_pb_)
            render_layer_lay.addLayout(editor_lay)

            # 附加功能布局
            self._layout_.addWidget(self._plus_tools_gb_)
            plus_tool_lay = QtWidgets.QVBoxLayout(self._plus_tools_gb_)
            col_lay = QtWidgets.QHBoxLayout()
            col_lay.addWidget(self._create_collection_pb_)
            col_lay.addWidget(self._append_collection_pb_)
            col_lay.addWidget(self._remove_collections_pb_)
            plus_tool_lay.addLayout(col_lay)

            fog_lay = QtWidgets.QGridLayout()
            fog_lay.addWidget(self._light_fog_tool_pb_, 0, 0, 2, 1)
            fog_lay.addWidget(self._create_fog_cube_pb_, 0, 2, 2, 1)
            plus_tool_lay.addWidget(self.append_frame())
            plus_tool_lay.addLayout(fog_lay)

            plus_lay = QtWidgets.QVBoxLayout()
            plus_lay.addWidget(self._set_convert_common_shot_pb_)
            plus_tool_lay.addWidget(self.append_frame())
            plus_tool_lay.addLayout(plus_lay)
            
            self.setup_signals()

        def _invoke_dynamic_module(self, module_name):
            import importlib
            try:
                mod = importlib.import_module(module_name)
                importlib.reload(mod) # 支持边改代码边执行，对 TD 极其友好
                mod.execute()
                self.refresh_scene_list()
            except Exception as e:
                err_str = str(e)
                if "NO_MASTER_SCENE" in err_str:
                    QtWidgets.QMessageBox.warning(self, "管线防呆拦截", "未检测到被标记为【母场景/主层】的场景！\n请先在大纲选中任意起始场景，然后点击 [全局设置] 或相关接口将其升格为母场景，再尝试克隆分层。")
                else:
                    QtWidgets.QMessageBox.critical(self, "层模块执行崩溃", f"执行库 {module_name} 崩溃:\n{err_str}")
                print(f"[UI 框架拦截] 动态加载/执行层模块失败 {module_name}: {e}")
                
        def setup_signals(self):
            # 按流程式要求，所有按钮剥离具体逻辑，全部发往外部微服务模块(Micro-services)
            self._append_color_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_eevee.char_color_layer"))
            self._append_line_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_eevee.line_layer"))
            self._append_3d_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_eevee.scene_light_layer"))
            self._append_sss_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_eevee.scene_sss_layer"))
            self._append_2d_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_eevee.scene_twod_layer"))
            
            # Eevee 工具新增
            self._append_hdr_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_eevee.scene_hdr_layer"))
            
            # Cycles 工具新增
            self._append_cyc_light_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_cycles.scenec_light_layer"))
            self._append_cyc_hdr_layer_pb_.clicked.connect(lambda: self._invoke_dynamic_module("modules_cycles.scenec_hdr_layer"))

            # UI 联动
            self._render_layer_list_lw_.itemSelectionChanged.connect(self.on_scene_selection_changed)
            
            self._delete_selected_scene_pb_.clicked.connect(self._cb_delete_selected_scene)
            self._delete_selected_viewlayer_pb_.clicked.connect(self._cb_delete_selected_viewlayer)
            
            self._clear_all_layers_pb_.clicked.connect(self.action_clear_all_layers)
            self._duplicate_selected_layers_pb_.clicked.connect(self.action_duplicate_layer)
            self._remove_collections_pb_.clicked.connect(self._cb_remove_collections)
            self._set_convert_common_shot_pb_.clicked.connect(self._cb_set_convert_common_shot)

            # 独立技能接入绑定
            self._launch_hdr_manager_pb_.clicked.connect(self._cb_launch_hdr_manager)

            # --- 全局核心环境绑定 ---
            self._global_set_master_pb_.clicked.connect(self._cb_global_set_master)
            self._global_clear_master_pb_.clicked.connect(self._cb_global_clear_master)
            self._global_set_res_pb_.clicked.connect(self._cb_global_set_res)
            self._global_sync_pb_.clicked.connect(self._cb_global_sync)
            
            self.refresh_scene_list()

        # ====================================
        # 全局控制事件槽
        # ====================================
        def _cb_global_clear_master(self):
            try:
                count = 0
                for s in bpy.data.scenes:
                    if s.get("ppas_is_master") is not None:
                        del s["ppas_is_master"]
                        count += 1
                self.do_full_refresh()
                if count > 0:
                    QtWidgets.QMessageBox.information(self, "解绑成功", f"成功解除了 {count} 个场景的母层特权烙印。")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "解绑异常", str(e))
                
        def _cb_global_set_master(self):
            try:
                if hasattr(bpy.ops.ppas, 'set_all_global'):
                    bpy.ops.ppas.set_all_global()
                    self.refresh_scene_list()
                    QtWidgets.QMessageBox.information(self, "成功", "已成功指定当前场景为【母场景/主层】，列表状态已更新！")
                else:
                    QtWidgets.QMessageBox.warning(self, "未找到算子", "插件 [set_all_global] 未正确加载，请检查 PPAS 主插件状态。")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "操作异常", str(e))
                
        def _cb_global_set_res(self):
            try:
                if hasattr(bpy.ops.ppas, 'set_resolution_fps'):
                    # 必须以 INVOKE_DEFAULT 结合顶级上下文唤起 Blender 原生弹窗
                    with bpy.context.temp_override(window=bpy.data.window_managers[0].windows[0]):
                        bpy.ops.ppas.set_resolution_fps('INVOKE_DEFAULT')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "操作异常", str(e))
                
        def _cb_global_sync(self):
            try:
                if hasattr(bpy.ops.ppas, 'sync_master_params'):
                    bpy.ops.ppas.sync_master_params()
                    QtWidgets.QMessageBox.information(self, "成功", "本层当前自定义参数已全域穿透同步至下级渲染层！")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "同步中断", str(e))

        # ====================================
        # 回调函数与槽
        # ====================================
        def _cb_remove_collections(self):
            pass

        def _cb_set_convert_common_shot(self):
            pass

        def _cb_launch_hdr_manager(self):
            import importlib.util
            import sys
            import os
            
            launcher_path = r"X:\AI_Automation\.gemini\skills\ppas_hdr_manager_launcher\scripts\logic.py"
            
            try:
                # 动态加载避免同名 logic.py 的命名空间冲突
                spec = importlib.util.spec_from_file_location("ppas_hdr_manager_launcher_logic", launcher_path)
                hdr_mod = importlib.util.module_from_spec(spec)
                sys.modules["ppas_hdr_manager_launcher_logic"] = hdr_mod
                spec.loader.exec_module(hdr_mod)
                
                # 执行 manager 核心主循环并挂靠在当前窗口上防止垃圾回收
                self.hdr_ui_ref = hdr_mod.run_manager()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "HDR总控启动失败", f"无法唤起底层 HDR 启动器逻辑：\n{e}")

        def get_master_scene(self):
            # 将该函数的实现委派给基础核心库
            return ppas_layer_core.get_master_scene()

        def refresh_scene_list(self):
            self._render_layer_list_lw_.clear()
            for s in bpy.data.scenes:
                item = QtWidgets.QListWidgetItem(s.name)
                if s.get("ppas_is_master"): item.setText(f"{s.name} [母]")
                if s == bpy.context.scene: item.setSelected(True)
                self._render_layer_list_lw_.addItem(item)
            self.refresh_hidden_objects()

        def on_scene_selection_changed(self):
            items = self._render_layer_list_lw_.selectedItems()
            if not items: return
            name = items[0].text().replace(" [母]", "")
            if name in bpy.data.scenes:
                # [技术优化] 强行拆除物理视口联动。
                # 之前这里有一段 bpy.context.window.scene = bpy.data.scenes[name]
                # 这会导致每次点击列表，Blender都会做一次全量的 Depsgraph (依赖图) 重算，造成巨大卡顿。
                # 现在完全解绑，UI 仅做 Data 层面 (内存读取) 的查询，实现 0 毫秒响应。
                
                # 无论物理界面是否切换成功，UI右侧一定要强行刷新出这个选中名称对应的数据！
                self.refresh_hidden_objects()

        def refresh_hidden_objects(self):
            # 严格根据左侧列表选中的场景来提取层，防止上下文缓存错乱
            self._hide_obj_list_lw_.clear()
            
            items = self._render_layer_list_lw_.selectedItems()
            if items:
                name = items[0].text().replace(" [母]", "")
                target_scene = bpy.data.scenes.get(name)
            else:
                target_scene = bpy.context.scene
                
            if not target_scene: return
            
            for vl in target_scene.view_layers:
                item = QtWidgets.QListWidgetItem(vl.name)
                # 如果是当前激活的层，给它个选中高亮
                if hasattr(bpy.context.window, "view_layer") and vl == bpy.context.window.view_layer:
                    item.setSelected(True)
                self._hide_obj_list_lw_.addItem(item)

        def _cb_delete_selected_scene(self):
            items = self._render_layer_list_lw_.selectedItems()
            if not items: return
            name = items[0].text().replace(" [母]", "")
            s = bpy.data.scenes.get(name)
            
            # 严格保护母场景
            if s and s == self.get_master_scene():
                QtWidgets.QMessageBox.warning(self, "禁止删除", "抱歉，指定的【母场景】受到管线严格保护，禁止删除！")
                return
                
            if s:
                bpy.data.scenes.remove(s)
                self.refresh_scene_list()

        def _cb_delete_selected_viewlayer(self):
            # 获取来源场景
            scene_items = self._render_layer_list_lw_.selectedItems()
            if not scene_items: return
            scene_name = scene_items[0].text().replace(" [母]", "")
            s = bpy.data.scenes.get(scene_name)
            
            # 严格保护母场景的视图层
            if s and s == self.get_master_scene():
                QtWidgets.QMessageBox.warning(self, "禁止删除", "抱歉，指定【母场景】的 ViewLayer 受到管线严格保护，禁止删除！")
                return
                
            # 获取目标 ViewLayer
            vl_items = self._hide_obj_list_lw_.selectedItems()
            if not vl_items: return
            vl_name = vl_items[0].text()
            
            if s:
                vl = s.view_layers.get(vl_name)
                if vl:
                    # Blender 强制要求每个 scene 至少全活1个 view_layer
                    if len(s.view_layers) <= 1:
                        QtWidgets.QMessageBox.warning(self, "禁止操作", "Blender 引擎限制：每个场景至少必须保留一个 ViewLayer 节点！")
                        return
                    s.view_layers.remove(vl)
                    # 重新刷新右侧列表
                    self.refresh_hidden_objects()

        def action_clear_all_layers(self):
            master = self.get_master_scene()
            for s in list(bpy.data.scenes):
                if s != master:
                    bpy.data.scenes.remove(s)
            self.refresh_scene_list()

        def action_duplicate_layer(self):
            bpy.ops.scene.new(type='LINK_COPY')
            self.refresh_scene_list()

from bpy.app.handlers import persistent

qt_layer_mgr_ref = None

@persistent
def auto_refresh_qt_project_info(dummy=None):
    """监听 Blender 的保存和加载事件，自动刷新 Qt 窗口信息 (增加延迟保护)"""
    global qt_layer_mgr_ref
    if qt_layer_mgr_ref:
        try:
            if qt_layer_mgr_ref:
                qt_layer_mgr_ref.do_full_refresh()
                
            # 作为双重安全冗余，0.5秒后再强制刷一次（防止底层尚未就绪）
            def _delayed_refresh():
                if qt_layer_mgr_ref:
                    try: qt_layer_mgr_ref.do_full_refresh()
                    except Exception: pass
            if hasattr(bpy.app, 'timers'):
                bpy.app.timers.register(lambda: _delayed_refresh() or None, first_interval=0.5)
        except RuntimeError:
            qt_layer_mgr_ref = None
        except Exception as e:
            print(f"Auto refresh error: {e}")

class PPAS_OT_OpenRenderLayerManager(bpy.types.Operator):
    """弹出独立的 Qt 渲染层管理窗口 (壳)"""
    bl_idname = "ppas.open_render_layer_manager"
    bl_label = "渲染层管理器 (测试中)"
    
    def execute(self, context):
        if not HAS_PYSIDE:
            self.report({'ERROR'}, "未检测到 PySide6 环境")
            return {'CANCELLED'}
            
        global qt_layer_mgr_ref
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        
        # Singleton 单例护航逻辑
        if qt_layer_mgr_ref is not None:
            try:
                # 尝试将旧窗口强行拉回最前并获取焦点
                qt_layer_mgr_ref.show() # 这是被点 X 关闭后能复活的关键
                qt_layer_mgr_ref.setWindowState(qt_layer_mgr_ref.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
                qt_layer_mgr_ref.activateWindow()
                qt_layer_mgr_ref.raise_()
                self.report({'INFO'}, "已将现存的渲染层管理器拉回前台")
                return {'FINISHED'}
            except RuntimeError:
                # C++ wrapped 对象已被用户点 X 关掉
                qt_layer_mgr_ref = None
                
        qt_layer_mgr_ref = RenderLayerMainWidget()
        qt_layer_mgr_ref.show()
        
        self.report({'INFO'}, "已打开渲染层管理器 (支持自动刷新)")
        return {'FINISHED'}

classes = (PPAS_OT_OpenRenderLayerManager,)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    if auto_refresh_qt_project_info not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(auto_refresh_qt_project_info)
    if auto_refresh_qt_project_info not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(auto_refresh_qt_project_info)
    if hasattr(bpy.app.handlers, 'load_factory_startup_post') and auto_refresh_qt_project_info not in bpy.app.handlers.load_factory_startup_post:
        bpy.app.handlers.load_factory_startup_post.append(auto_refresh_qt_project_info)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    if auto_refresh_qt_project_info in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(auto_refresh_qt_project_info)
    if auto_refresh_qt_project_info in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(auto_refresh_qt_project_info)
    if hasattr(bpy.app.handlers, 'load_factory_startup_post') and auto_refresh_qt_project_info in bpy.app.handlers.load_factory_startup_post:
        bpy.app.handlers.load_factory_startup_post.remove(auto_refresh_qt_project_info)
