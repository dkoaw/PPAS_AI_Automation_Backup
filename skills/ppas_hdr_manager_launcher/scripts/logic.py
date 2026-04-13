import sys
import os

"""
HDR 光照管理器 -- 三角架构整合发射总管 (Launcher)
"""

# ========= 0. 环境路径注射 (生产部署) =========
# 严格绑定至管线资产中枢，无视宿主 Blender Text 缓存的临时位置
project_root = r"X:\AI_Automation"
skills_dir = os.path.join(project_root, ".gemini", "skills")

skill_paths = [
    os.path.join(skills_dir, "ppas_hdr_asset_parser", "scripts"),
    os.path.join(skills_dir, "ppas_hdr_blender_core", "scripts"),
    os.path.join(skills_dir, "ppas_hdr_qt_panel", "scripts")
]

for p in skill_paths:
    if p not in sys.path:
        sys.path.append(p)

# ========= 1. 挂载三大模块 (Import Modules) =========
try:
    import importlib
    
    # 强暴力拔除旧缓存 (比 reload 更彻底，确保跨模块刷新)
    for m in ['hdr_parser', 'hdr_blender_core', 'hdr_qt_ui']:
        if m in sys.modules:
            del sys.modules[m]
            
    import hdr_parser
    import hdr_blender_core
    import hdr_qt_ui
    
    from hdr_parser import HDRAssetParser
    from hdr_blender_core import HDRBlenderCore
    from hdr_qt_ui import HdrUIControlPanel
    
    # 根据你的环境可能是 PySide2 或是 PyQt5
    from PySide6 import QtWidgets, QtCore 
except ImportError as e:
    raise ImportError(f"载入致命错误! 无法找到底层模块或 PySide6 库。\n详情: {e}\n检测搜索路径: {skills_dir}")

# ========= 2. 中枢事件连接站 (Central Event Bus) =========
class HDRIntegrationBus:
    def __init__(self, ui_instance):
        self.ui = ui_instance
        self._link_events()
        self._last_context_signature = None # 用于缓存上一次检测到的环境签名 (Scene + ViewLayer)
        
    def _link_events(self):
        """将瞎盲的 UI 信号线，强插进 Blender 执行核心"""
        self.ui.sig_push_to_engine.connect(self.on_ui_push_data)
        self.ui.sig_request_info.connect(self.on_ui_pull_request)
        if hasattr(self.ui, 'sig_check_auth'):
            self.ui.sig_check_auth.connect(self.on_ui_check_auth)
        if hasattr(self.ui, 'sig_request_cache_update'):
            self.ui.sig_request_cache_update.connect(self.on_request_cache_update)

    def on_request_cache_update(self):
        """强制清盘重扫，重构 JSON 极速缓存"""
        print("[HDR 总线] 接收到极速缓存刷新指令，开始执行深度扫盘...")
        parser = HDRAssetParser()
        asset_dict = parser.scan_assets(force_rebuild=True)
        self.ui.load_gallery_data(asset_dict)
        print("[HDR 总线] HDR 画廊热更新完毕。")

    def on_ui_check_auth(self):
        """仅做条件判断拦截，不向引擎写入任何变更数据"""
        is_legal, msg = HDRBlenderCore.is_context_authorized()
        if not is_legal:
            QtWidgets.QMessageBox.warning(self.ui, "非法环境拦截", msg)

    def heartbeat_sync_logic(self):
        """
        [核心引擎逻辑：层级自动同步]
        每 500ms 探测一次当前 Blender 的层级环境。
        一旦检测到层级切换，自动拉取该层的数据并同步给 UI。
        """
        import bpy
        try:
            scn = bpy.context.scene
            vl = bpy.context.view_layer
        except:
            return # Blender 处于渲染或 Modal 模式时跳过
            
        current_sig = f"{scn.name}:{vl.name}"
        
        # 鉴权前置逻辑：判断是否在非法层级
        is_legal, msg = HDRBlenderCore.is_context_authorized()
        if not is_legal:
            # 根据用户需求，屏蔽心跳扫描时的主动弹窗。仅执行数据清空：
            if current_sig != self._last_context_signature:
                self.ui.load_data_pack(HDRBlenderCore.DEFAULT_PACK)
                self._last_context_signature = current_sig
            return
        
        # 合法层级逻辑 (屏蔽心跳检测带来的 UI 解锁干扰)
        # self.ui.unlock_shield()
        
        # 检测层级切换签名
        if current_sig != self._last_context_signature:
            print(f"[HDR 总线] 检测到环境切换 -> {current_sig}，开始同步层级数据...")
            
            # 1. 尝试从该层沙盒读取数据
            layer_data = HDRBlenderCore.read_from_sandbox()
            
            # 2. 如果数据为空（新层级），则使用默认包（复位 UI）
            if not layer_data:
                print(f"[HDR 总线] 当前层无 HDR 数据，执行复位。")
                self.ui.load_data_pack(HDRBlenderCore.DEFAULT_PACK)
            else:
                # 3. 如果有数据，同步 UI 数值与列表选中项
                print(f"[HDR 总线] 成功回读层级数据，刷新 UI 数值。")
                self.ui.load_data_pack(layer_data)
                
            self._last_context_signature = current_sig

    def on_ui_push_data(self, data_dict):
        # 1. 操作时强制进行拦截
        is_legal, msg = HDRBlenderCore.is_context_authorized()
        if not is_legal:
            # self.ui.lock_shield(msg) # 用户要求仅在操作时弹窗作为提示，不再强行锁死 UI
            QtWidgets.QMessageBox.warning(self.ui, "非法环境拦截", msg)
            return
            
        # 鉴权成功，写入沙盒并注入节点
        HDRBlenderCore.snapshot_to_sandboox(data_dict)
        success, msg = HDRBlenderCore.inject_topology_and_update(pack_data=data_dict)
        # print(f"[集成总线]: 织补回调 -> {msg}")

    def on_ui_pull_request(self):
        # UI主动索取数据
        is_legal, msg = HDRBlenderCore.is_context_authorized()
        if not is_legal:
             QtWidgets.QMessageBox.warning(self.ui, "非法环境拦截", msg)
             return
             
        data = HDRBlenderCore.read_from_sandbox()
        if data:
             print(f"成功窃取沙盒残量参数: {data}")
             self.ui.load_data_pack(data) # 使用刚才编写的新方法
             
# ========= 3. 引擎点火 (Ignition) =========
def run_manager():
    import bpy
    # 彻底抹杀旧实例，保证只能存在唯一窗口 (Singleton)
    if hasattr(bpy, "_ppas_hdr_ui_win"):
        try:
            old_win = getattr(bpy, "_ppas_hdr_ui_win")
            old_win.close()
            old_win.deleteLater()
        except: pass

    # 检测 QApplication
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
        
    # 建立底层资产探针
    parser = HDRAssetParser()
    print("开始扫盘 HDR 资产，请稍候...")
    asset_data = parser.scan_assets()
    
    # 构建瞎壳 UI
    ui_win = HdrUIControlPanel()
    ui_win.load_gallery_data(asset_data)
    
    # 将窗口对象强行锚定到 Blender 全局内存，防止多开和游离
    bpy._ppas_hdr_ui_win = ui_win
    
    # 通过总线将三者缝合
    bus = HDRIntegrationBus(ui_win)
    ui_win._bus_keeper = bus
    
    # [核心修改：静默同步心跳] 恢复每 500ms 的探测，用于检测层级切换签名
    timer = QtCore.QTimer(ui_win)
    timer.timeout.connect(bus.heartbeat_sync_logic)
    timer.start(500) 
    ui_win._timer_keeper = timer
    
    ui_win.show()
    return ui_win

if __name__ == "__main__":
    # 若在脱离 Blender 的普通 IDE 测试将报错因为无 bpy, 
    # 该文件必须在 Blender 脚本视图中以 Python 方式执行
    global_ui_win = run_manager()
