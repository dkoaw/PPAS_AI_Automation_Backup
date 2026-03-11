import bpy
import sys
import os

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
            self.refresh_project_name()

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
            
            self._project_refresh_pb_ = QtWidgets.QPushButton(u'刷新状态')
            self._project_refresh_pb_.setMaximumWidth(80)
            self._project_refresh_pb_.clicked.connect(self.refresh_project_name)

            # 添加层区块
            self._append_layer_gb_ = QtWidgets.QGroupBox('')
            self._append_color_layer_pb_ = QtWidgets.QPushButton(u'添加 角色Color 层（唯一）')
            self._append_env_color_layer_pb_ = QtWidgets.QPushButton(u'添加 场景Color 层')
            self._append_hdr_layer_pb_ = QtWidgets.QPushButton(u'添加 HDR 层')
            self._2d_texture_lb_ = QtWidgets.QLabel(u'2D 材质:')
            self._2d_texture_cb_ = QtWidgets.QComboBox()
            self._append_2d_layer_pb_ = QtWidgets.QPushButton(u'添加 2D 光照层')
            self._append_3d_layer_pb_ = QtWidgets.QPushButton(u'添加 3D 光照层')
            self._append_fog_layer_pb_ = QtWidgets.QPushButton(u'添加 Fog 层')
            self._append_emi_layer_pb_ = QtWidgets.QPushButton(u'添加 Emission 层')
            self._append_shadow_layer_pb_ = QtWidgets.QPushButton(u'添加 Shadow 层')
            self._append_line_layer_pb_ = QtWidgets.QPushButton(u'添加 Line 层（唯一）')
            self._append_piercing_layer_pb_ = QtWidgets.QPushButton(u'添加 CBCS 层（唯一）')

            # 层编辑器区块
            self._layer_editor_gb_ = QtWidgets.QGroupBox(u'')
            self._layer_editor_st_ = QtWidgets.QSplitter()
            self._layer_editor_st_.setOrientation(QtCore.Qt.Horizontal)
            self._render_layer_list_wt_ = QtWidgets.QWidget()

            self._render_layer_list_lb_ = QtWidgets.QLabel(u'渲染层列表')
            self._render_layer_list_lb_.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  
            self._render_layer_list_lw_ = QtWidgets.QListWidget()
            
            self._hide_obj_list_wt_ = QtWidgets.QWidget()
            self._hide_obj_list_lb_ = QtWidgets.QLabel(u'当前层内隐藏物体')
            self._hide_obj_list_lb_.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)      
            self._hide_obj_list_lw_ = QtWidgets.QListWidget()

            self._append_selected_to_layers_pb_ = QtWidgets.QPushButton(u'添加到渲染层')
            self._remove_selected_from_layers_pb_ = QtWidgets.QPushButton(u'从渲染层中移除')

            self._solo_selected_objs_pb_ = QtWidgets.QPushButton(u'切换显隐状态')
            self._hide_selected_objs_pb_ = QtWidgets.QPushButton(u'隐藏所选')
            self._show_selected_objs_pb_ = QtWidgets.QPushButton(u'显示所选')

            self._remove_selected_layers_pb_ = QtWidgets.QPushButton(u'移除选中渲染层')
            self._clear_all_layers_pb_ = QtWidgets.QPushButton(u'清空所有层')
            self._duplicate_selected_layers_pb_ = QtWidgets.QPushButton(u'复制选中渲染层')

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
            info_lay.addStretch(True)

            # 添加层布局
            self._layout_.addWidget(self._append_layer_gb_)
            add_layer_lay = QtWidgets.QGridLayout(self._append_layer_gb_)
            add_layer_lay.addWidget(self._append_color_layer_pb_, 0, 0, 1, 3)
            add_layer_lay.addWidget(self._append_env_color_layer_pb_, 0, 3, 1, 3)
            add_layer_lay.addWidget(self._append_hdr_layer_pb_, 1, 0, 1, 2)
            add_layer_lay.addWidget(self._append_3d_layer_pb_, 1, 2, 1, 2)
            add_layer_lay.addWidget(self._append_line_layer_pb_, 1, 4, 1, 2)
            add_layer_lay.addWidget(self._append_emi_layer_pb_, 2, 0, 1, 2)
            add_layer_lay.addWidget(self._append_fog_layer_pb_, 2, 2, 1, 2)
            add_layer_lay.addWidget(self._append_shadow_layer_pb_, 2, 4, 1, 2)
            add_layer_lay.addWidget(self._append_piercing_layer_pb_, 4, 0, 1, 6)
            add_layer_lay.addWidget(self._2d_texture_lb_, 3, 0)
            add_layer_lay.addWidget(self._2d_texture_cb_, 3, 1, 1, 4)
            add_layer_lay.addWidget(self._append_2d_layer_pb_, 3, 5)

            # 层编辑器布局
            self._layout_.addWidget(self._layer_editor_gb_)
            render_layer_lay = QtWidgets.QVBoxLayout(self._layer_editor_gb_)
            
            render_lay = QtWidgets.QVBoxLayout(self._render_layer_list_wt_)
            render_lay.addWidget(self._render_layer_list_lb_)
            render_lay.addWidget(self._render_layer_list_lw_)
            
            layer_editor_lay = QtWidgets.QHBoxLayout()
            layer_editor_lay.addWidget(self._append_selected_to_layers_pb_)
            layer_editor_lay.addWidget(self._remove_selected_from_layers_pb_)
            render_lay.addLayout(layer_editor_lay)

            hide_lay = QtWidgets.QVBoxLayout(self._hide_obj_list_wt_)
            hide_lay.addWidget(self._hide_obj_list_lb_)
            hide_lay.addWidget(self._hide_obj_list_lw_)

            hide_editor_lay = QtWidgets.QHBoxLayout()
            hide_editor_lay.addWidget(self._solo_selected_objs_pb_)
            label = QtWidgets.QLabel('|')
            label.setMaximumWidth(15)
            hide_editor_lay.addWidget(label)
            hide_editor_lay.addWidget(self._hide_selected_objs_pb_)
            hide_editor_lay.addWidget(self._show_selected_objs_pb_)
            hide_lay.addLayout(hide_editor_lay)

            self._layer_editor_st_.addWidget(self._render_layer_list_wt_)
            self._layer_editor_st_.addWidget(self._hide_obj_list_wt_)
            self._layer_editor_st_.setSizes([250, 300])
            render_layer_lay.addWidget(self._layer_editor_st_)
            
            render_layer_lay.addWidget(self.append_frame())
            editor_lay = QtWidgets.QHBoxLayout()
            editor_lay.addWidget(self._remove_selected_layers_pb_)
            editor_lay.addWidget(self._clear_all_layers_pb_)
            render_layer_lay.addLayout(editor_lay)
            render_layer_lay.addWidget(self._duplicate_selected_layers_pb_)

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

from bpy.app.handlers import persistent

qt_layer_mgr_ref = None

@persistent
def auto_refresh_qt_project_info(dummy=None):
    """监听 Blender 的保存和加载事件，自动刷新 Qt 窗口信息 (增加延迟保护)"""
    global qt_layer_mgr_ref
    if qt_layer_mgr_ref:
        try:
            # 延迟 0.1 秒执行，确保 Blender 已经完成文件路径的后台更新
            bpy.app.timers.register(lambda: qt_layer_mgr_ref.refresh_project_name() or None, first_interval=0.1)
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

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    if auto_refresh_qt_project_info in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(auto_refresh_qt_project_info)
    if auto_refresh_qt_project_info in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(auto_refresh_qt_project_info)
