import os
import json
import datetime
import subprocess
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QTextEdit, QMessageBox, QRadioButton, 
    QButtonGroup, QLineEdit, QSpinBox, QFileDialog, QProgressBar, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QGridLayout, QCompleter, QFrame,
    QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QProcess, QTimer, QStringListModel
from PyQt6.QtGui import QPixmap, QIntValidator, QIcon


# 兼容原有的核心库引用
from core.def_database import DataEngine, generate_default_data, deduce_overlay
from core.config_writer import RPiSystemManager

SETTINGS_FILE = "app_settings.json"

class AppSettings:
    @staticmethod
    def get_last_sku():
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("last_selected_sku", "")
            except:
                return ""
        return ""

    @staticmethod
    def set_last_sku(sku):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_selected_sku": sku}, f, ensure_ascii=False, indent=2)
        except:
            pass


class QATestCenter(QMainWindow):
    # ================= 顶级商业仪器质感 (Precision Clean Light) ================= #
    STYLE_SHEET = """
        /* 全局背景 */
        QWidget {
            background-color: #F1F5F9;
            color: #0F172A;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif;
        }

        /* 顶部导航与容器卡片 */
        QFrame#MainContainer, QTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
        }

        /* 现代化胶囊 Tab 栏 */
        QTabBar::tab {
            background-color: transparent;
            color: #64748B;
            padding: 10px 24px;
            margin: 4px 4px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
        }
        QTabBar::tab:hover {
            color: #0284C7;
            background-color: #F1F5F9;
        }
        QTabBar::tab:selected {
            background-color: #E0F2FE;
            color: #0284C7;
        }

        /* 驱动核心配置卡片 (Hero Card) */
        QFrame#HeroCard {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 24px;
        }
        QLabel#HeroTitle {
            font-size: 24px;
            font-weight: 800;
            color: #0F172A;
        }
        QLabel#HeroSubtitle {
            font-size: 14px;
            color: #64748B;
            font-weight: 500;
        }
        
        /* 状态指示胶囊 */
        QLabel#StatusBadge {
            background-color: #ECFDF5;
            border: 1px solid #A7F3D0;
            border-radius: 16px;
            color: #059669;
            font-weight: bold;
            padding: 6px 16px;
            font-size: 13px;
        }
        QLabel#StatusBadgeEmpty {
            background-color: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 16px;
            color: #64748B;
            font-weight: bold;
            padding: 6px 16px;
            font-size: 13px;
        }

        /* 全局胶囊搜索栏 (完美替换原先别扭的文字) */
         QLineEdit#GlobalSearchBar {
            background-color: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 19px; /* 高度38的一半，完美半圆胶囊 */
            padding: 0px 14px;   /* 左侧增加 14px 留白，让放大镜不要太靠边 */
            font-size: 13px;
            color: #0F172A;
        }
        QLineEdit#GlobalSearchBar:focus {
            background-color: #FFFFFF;
            border: 2px solid #0284C7;
            padding: 0px 13px; /* 减去边框增加的 1px，防止获取焦点时文字左右抖动 */
        }

        /* 表格过滤搜索栏 (配套胶囊风格) */
        QLineEdit#TableFilterBar {
            background-color: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 16px; /* 高度32的一半 */
            padding: 0px 12px;
            font-size: 13px;
            color: #0F172A;
        }
        QLineEdit#TableFilterBar:focus {
            background-color: #FFFFFF;
            border: 2px solid #0284C7;
            padding: 0px 11px;
        }
        QLineEdit#GlobalSearchBar::placeholder {
             color: #94A3B8;
        }

        /* 常规输入框 */
        QLineEdit, QSpinBox {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 8px 14px;
            color: #0F172A;
            font-size: 13px;
        }
        QLineEdit:focus, QSpinBox:focus { border: 2px solid #0284C7; }
        QLineEdit::placeholder { color: #94A3B8; }

        /* 主操作按钮 (科技天青蓝) */
        QPushButton#PrimaryActionBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #0369A1);
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: bold;
            min-height: 48px;
            max-width: 320px;
        }
        QPushButton#PrimaryActionBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369A1, stop:1 #075985); }
        QPushButton#PrimaryActionBtn:pressed { background-color: #0C4A6E; }
        QPushButton#PrimaryActionBtn:disabled { background: #CBD5E1; color: #F1F5F9; }

        /* 危险/停止按钮 */
        QPushButton#DangerActionBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:1 #DC2626);
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: bold;
            min-height: 48px;
            max-width: 260px;
        }
        QPushButton#DangerActionBtn:hover { background: #B91C1C; }

        /* 次要/线框按钮 */
        QPushButton#SecondaryBtn {
            background-color: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; border-radius: 8px; padding: 8px 16px; font-weight: bold;
        }
        QPushButton#SecondaryBtn:hover { background-color: #F8FAFC; color: #0F172A; }

        /* 表格内微型操作按钮 (无边框轻量化设计) */
        QPushButton#TableEditBtn {
            background-color: #E0F2FE; color: #0284C7; border: none; border-radius: 6px; padding: 6px 12px; font-weight: bold;
        }
        QPushButton#TableEditBtn:hover { background-color: #BAE6FD; }
        
        QPushButton#TableDeleteBtn {
            background-color: #FEF2F2; color: #EF4444; border: none; border-radius: 6px; padding: 6px 12px; font-weight: bold;
        }
        QPushButton#TableDeleteBtn:hover { background-color: #FECACA; }

        /* 单选框与进度条 */
        QRadioButton { spacing: 10px; font-weight: 600; color: #334155; font-size: 14px; }
        QRadioButton::indicator { width: 16px; height: 16px; border-radius: 8px; border: 2px solid #CBD5E1; background: #FFFFFF; }
        QRadioButton::indicator:checked { border: 2px solid #0284C7; background-color: #0284C7; }

        /* 表格控件 */
        QTableWidget {
            background-color: #FFFFFF;
            alternate-background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            gridline-color: transparent;
        }
        QTableWidget::item { padding: 4px 14px; border-bottom: 1px solid #F1F5F9; }
        QTableWidget::item:selected { background-color: #F1F5F9; color: #0F172A; }
        QHeaderView::section { background-color: #F8FAFC; color: #475569; padding: 10px 14px; border: none; border-bottom: 2px solid #E2E8F0; font-weight: bold; }
        
        QProgressBar { text-align: center; font-weight: bold; border-radius: 6px; background-color: #F8FAFC; border: 1px solid #E2E8F0; color: #475569;}
        QProgressBar::chunk { background-color: #0284C7; border-radius: 5px; }

        /* 终端控制台 */
        QTextEdit#ConsoleBox {
            background-color: #0B0F19; border: 1px solid #1E293B; border-radius: 10px; color: #38BDF8; font-family: "JetBrains Mono", "Consolas", monospace; font-size: 12px; padding: 12px;
        }
        QScrollBar:vertical { border: none; background: transparent; width: 8px; margin: 0px; }
        QScrollBar::handle:vertical { background: #CBD5E1; min-height: 20px; border-radius: 4px; }
        QScrollBar::handle:vertical:hover { background: #94A3B8; }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arducam Precision Studio")
        self.resize(1080, 800)
        self.setStyleSheet(self.STYLE_SHEET)
        
        self.data_records = DataEngine.fetch_records()
        self.active_in_test_sku = None 
        self.staged_target_sku = None 
        
        # 进程管理器
        self.cam_job = QProcess()
        self.cam_job.readyReadStandardOutput.connect(lambda: self._proc_std(self.cam_job, False))
        self.cam_job.readyReadStandardError.connect(lambda: self._proc_std(self.cam_job, True))
        self.cam_job.finished.connect(self._on_cam_job_finished)
        
        self.task_job = QProcess()
        self.task_job.finished.connect(self._task_end)
        self.task_job.readyReadStandardOutput.connect(lambda: self._proc_std(self.task_job, False))
        self.task_job.readyReadStandardError.connect(lambda: self._proc_std(self.task_job, True))

        self.test_engine = QProcess()
        self.test_engine.finished.connect(self._age_iteration_fin)
        self.test_engine.readyReadStandardOutput.connect(lambda: self._proc_std(self.test_engine, False))
        self.test_engine.readyReadStandardError.connect(lambda: self._proc_std(self.test_engine, True))
        
        self.a_tot = 0; self.a_cur = 0; self.a_ok = 0; self.a_fail = 0; self.a_sig = False
        self._construct_canvas()

    def out_print(self, msg_str, severity_clr="#38BDF8"):
        time_pref = datetime.datetime.now().strftime("[%H:%M:%S]")
        formatted = f'<span style="color:{severity_clr};">{time_pref} {msg_str}</span>'
        self.logs.append(formatted)
        self.logs.verticalScrollBar().setValue(self.logs.verticalScrollBar().maximum())
         
    def _proc_std(self, proc_node, is_error):
        color = "#EF4444" if is_error else "#CBD5E1"
        content = proc_node.readAllStandardError() if is_error else proc_node.readAllStandardOutput()
        msg = content.data().decode("utf-8", "ignore").strip()
        if msg: self.out_print(msg, color)

    def _create_brand_logo(self):
        logo_container = QWidget()
        l_layout = QHBoxLayout(logo_container)
        l_layout.setContentsMargins(0, 0, 8, 0)
        
        brand_lbl = QLabel("""
            <div style='line-height:100%; margin-top:2px;'>
                <span style='font-size:20px; font-weight:800; color:#0284C7;'>Ardu</span><span style='font-size:20px; font-weight:800; color:#0F172A;'>cam</span>
                <span style='font-size:11px; font-weight:bold; color:#0F172A; margin-left:6px; padding:2px 6px; background:#E2E8F0; border-radius:4px;'>STUDIO</span>
            </div>
        """)
        l_layout.addWidget(brand_lbl)
        return logo_container

    def _construct_canvas(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        topdown_grid = QVBoxLayout(widget)
        topdown_grid.setContentsMargins(16, 16, 16, 16)
        topdown_grid.setSpacing(14)

        if not RPiSystemManager.check_permissions():
            hint_q = QLabel("系统权限提示: 当前未以 Root 启动，驱动配置烧录功能将受限。")
            hint_q.setStyleSheet("background-color: #FEF2F2; color: #DC2626; font-weight: bold; padding: 8px 14px; border-radius: 8px; border: 1px solid #FCA5A5;")
            topdown_grid.addWidget(hint_q)

        # -----------------------------------------------------------------
        # FIX: 彻底去掉“切换SKU”文字，升级为 Mac Spotlight 风格大胶囊搜索栏
        # -----------------------------------------------------------------
        banner = QHBoxLayout()
        banner.addWidget(self._create_brand_logo())

        self.top_current_sku_badge = QLabel("正在初始化状态...")
        self.top_current_sku_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.top_current_sku_badge.setFixedHeight(34)
        banner.addWidget(self.top_current_sku_badge)

        banner.addStretch() 
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("GlobalSearchBar")
        self.search_input.setPlaceholderText("搜索并快速切换 SKU 或 芯片型号...")
        self.search_input.setTextMargins(-8, 0, 0, 0)
        self.search_input.setFixedSize(400, 38)
        self.search_input.addAction(QIcon.fromTheme("edit-find"), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setFixedSize(400, 38)

        self.search_model = QStringListModel()
        self.completer = QCompleter(self.search_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_input.setCompleter(self.completer)
        self.completer.activated.connect(self._on_search_selected)

        banner.addWidget(self.search_input)
        topdown_grid.addLayout(banner)

        # 核心工作区
        self.dash_tab = QTabWidget()
        self._tab_init()        
        self._tab_quality()      
        self._tab_foto()      
        self._tab_qa_age()      
        self._tab_catalog()       
        topdown_grid.addWidget(self.dash_tab, stretch=56)
        
        # 控制台
        term = QGroupBox("运行日志 (Runtime Logs)")
        lgy = QVBoxLayout()
        lgy.setContentsMargins(14, 14, 14, 14)
        
        self.logs = QTextEdit()
        self.logs.setObjectName("ConsoleBox")
        self.logs.setReadOnly(True)
        
        clr_box = QHBoxLayout()
        clr_box.addStretch()
        clr_btn = QPushButton("清除日志")
        clr_btn.setObjectName("SecondaryBtn")
        clr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clr_btn.clicked.connect(self.logs.clear)
        clr_box.addWidget(clr_btn)

        lgy.addWidget(self.logs)
        lgy.addLayout(clr_box)
        term.setLayout(lgy)
        topdown_grid.addWidget(term, stretch=44)
        
        self._sync_app_state()
        self.out_print("Arducam Precision Studio 界面系统初始化完成。", "#059669")

    def _sync_app_state(self):
        """同步数据到模型及UI状态"""
        completion_str_list = [f"{item['sku']} | {item['sensor'].upper()} - {item['desc']}" for item in self.data_records]
        self.search_model.setStringList(completion_str_list)
        
        saved_sku = AppSettings.get_last_sku()
        saved_item = next((d for d in self.data_records if d['sku'] == saved_sku), None)
        
        if saved_item:
            self.active_in_test_sku = saved_item
            self.top_current_sku_badge.setText(f"● 正在测试模组：{saved_item['sku']} ({saved_item['sensor'].upper()})")
            self.top_current_sku_badge.setObjectName("StatusBadge")
        else:
            self.top_current_sku_badge.setText("○ 未配置挂载目标")
            self.top_current_sku_badge.setObjectName("StatusBadgeEmpty")
            
        self.top_current_sku_badge.style().unpolish(self.top_current_sku_badge)
        self.top_current_sku_badge.style().polish(self.top_current_sku_badge)

    def _on_search_selected(self, text):
        sku_val = text.split('|')[0].strip()
        matched = next((item for item in self.data_records if item['sku'] == sku_val), None)
        
        if matched:
            self.staged_target_sku = matched
            if hasattr(self, 'target_card_sku_lbl'):
                self.target_card_sku_lbl.setText(f"{matched['sku']} · {matched['sensor'].upper()}")
                self.target_card_detail_lbl.setText(f"映射驱动: dtoverlay={matched['overlay']}  |  {matched['desc']}")
                self.out_print(f"已暂存配置目标: {sku_val}，请前往[驱动配置]页点击应用。", "#38BDF8")

        QTimer.singleShot(0, self.search_input.clear)
        QTimer.singleShot(0, self.search_input.clearFocus)

    def __check_res(self):
        if self.cam_job.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.warning(self, "资源冲突", "相机被预览进程占用，请先停止画面质检。")
            return False 
        return True

    # ---------- 1. 驱动配置 ----------
    def _tab_init(self):
        ui_q = QWidget()
        y = QVBoxLayout(ui_q)
        y.setContentsMargins(18, 18, 18, 18)
        
        y.addStretch(1) 
        
        card_container = QHBoxLayout()
        card_container.addStretch()
        
        hero_card = QFrame()
        hero_card.setObjectName("HeroCard")
        hero_card.setMinimumWidth(500)
        hero_card.setMaximumWidth(600)
        h_layout = QVBoxLayout(hero_card)
        h_layout.setSpacing(12)
        
        self.target_card_sku_lbl = QLabel("请在右上角搜索并选择SKU")
        self.target_card_sku_lbl.setObjectName("HeroTitle")
        self.target_card_sku_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.target_card_detail_lbl = QLabel("等待指定配置...")
        self.target_card_detail_lbl.setObjectName("HeroSubtitle")
        self.target_card_detail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        h_layout.addWidget(self.target_card_sku_lbl)
        h_layout.addWidget(self.target_card_detail_lbl)
        
        card_container.addWidget(hero_card)
        card_container.addStretch()
        y.addLayout(card_container)
        
        y.addSpacing(32) 
        
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        
        btn_go = QPushButton("✔ 确定")
        btn_go.setObjectName("PrimaryActionBtn")
        btn_go.setFixedSize(320, 48)
        btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_go.clicked.connect(self._run_rewrite_rpi_sys)
        btn_container.addWidget(btn_go)
        btn_container.addStretch()
        
        y.addLayout(btn_container)
        y.addStretch(2) 
        
        self.dash_tab.addTab(ui_q, "1. 驱动配置")
         
    def _run_rewrite_rpi_sys(self):
        if not self.staged_target_sku:
            QMessageBox.warning(self, "提示", "请先在右上角搜索并选中目标 SKU！")
            return

        target = self.staged_target_sku
        code, resp = RPiSystemManager.enforce_driver_target(target['overlay'])
        if not code: 
            QMessageBox.critical(self, "写入失败", f"无法修改系统配置文件，请检查 Root 权限:\n{resp}")
        else:
            AppSettings.set_last_sku(target['sku'])
            self._sync_app_state()
            
            ok = QMessageBox.question(self, "配置完成", f"驱动已成功更新为: dtoverlay={target['overlay']}\n\n是否立即重启设备以生效？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ok == QMessageBox.StandardButton.Yes: 
                QProcess.startDetached("sudo", ["reboot"])
# ---------- 2. 画面质检 (全画幅与预览分辨率高阶控制) ----------
    def _tab_quality(self):
        pan = QWidget()
        vlay = QVBoxLayout(pan)
        vlay.setContentsMargins(18, 16, 18, 16)
        vlay.setSpacing(16)
        
        # === Group 1: 显示窗口配置 ===
        grp_display = QGroupBox("1. 显示窗口配置 (Display Mode)")
        ly_disp = QHBoxLayout()
        ly_disp.setContentsMargins(20, 24, 20, 24)
        
        self.rad_w = QRadioButton("标准窗口模式 (Default)")
        self.rad_w.setChecked(True)
        self.rad_f = QRadioButton("全屏模式 (Fullscreen)")
        
        ly_disp.addWidget(self.rad_w)
        ly_disp.addWidget(self.rad_f)
        ly_disp.addStretch()
        grp_display.setLayout(ly_disp)
        vlay.addWidget(grp_display)
        
        # === Group 2: 视场角与预览分辨率配置 ===
        grp_res = QGroupBox("2. 视场角与预览分辨率预设 (Preview Resolution)")
        ly_res = QVBoxLayout()
        ly_res.setContentsMargins(20, 20, 20, 20)
        ly_res.setSpacing(14)
        
        self.rad_res_max = QRadioButton("全画幅最大分辨率 (Full FOV Max - 默认原生画幅)")
        self.rad_res_max.setChecked(True)
        self.rad_res_bin = QRadioButton("2x2 Binning 模式 (Full FOV - 提升预览帧率)")
        self.rad_res_1080 = QRadioButton("标准 1080P 模式 (1920x1080)")
        self.rad_res_custom = QRadioButton("高级自定义 / 硬件原生模式 (Hardware Native)")
        
        # 绑定单选切换事件，控制自定义面板的启停
        self.rad_res_custom.toggled.connect(self._toggle_custom_panel)
        
        ly_res.addWidget(self.rad_res_max)
        ly_res.addWidget(self.rad_res_bin)
        ly_res.addWidget(self.rad_res_1080)
        ly_res.addWidget(self.rad_res_custom)
        
        # --- 自定义/原生模式探索面板 ---
        self.custom_panel = QWidget()
        self.custom_panel.setEnabled(False) # 默认禁用，选中自定义时开启
        ly_custom = QHBoxLayout(self.custom_panel)
        ly_custom.setContentsMargins(28, 0, 0, 0) # 往右缩进产生层级感
        ly_custom.setSpacing(12)
        
        self.btn_fetch_modes = QPushButton("读取当前相机原生模式")
        self.btn_fetch_modes.setObjectName("SecondaryBtn")
        self.btn_fetch_modes.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fetch_modes.clicked.connect(self._fetch_camera_modes)
        
        self.cb_native_modes = QComboBox()
        self.cb_native_modes.setMinimumWidth(180)
        
        self.inp_custom_w = QLineEdit()
        self.inp_custom_w.setPlaceholderText("宽(W)")
        self.inp_custom_w.setValidator(QIntValidator(100, 10000))
        self.inp_custom_w.setFixedWidth(70)
        
        lbl_x = QLabel("x")
        lbl_x.setStyleSheet("color: #64748B; font-weight: bold;")
        
        self.inp_custom_h = QLineEdit()
        self.inp_custom_h.setPlaceholderText("高(H)")
        self.inp_custom_h.setValidator(QIntValidator(100, 10000))
        self.inp_custom_h.setFixedWidth(70)
        
        # 联动下拉框与手动输入框
        self.cb_native_modes.currentTextChanged.connect(self._on_native_mode_selected)
        
        ly_custom.addWidget(self.btn_fetch_modes)
        ly_custom.addWidget(self.cb_native_modes)
        ly_custom.addSpacing(10)
        ly_custom.addWidget(QLabel("手动覆盖:"))
        ly_custom.addWidget(self.inp_custom_w)
        ly_custom.addWidget(lbl_x)
        ly_custom.addWidget(self.inp_custom_h)
        ly_custom.addStretch()
        
        ly_res.addWidget(self.custom_panel)
        grp_res.setLayout(ly_res)
        vlay.addWidget(grp_res)
        
        vlay.addSpacing(24)
        
        # === 底部操作大按钮区域 ===
        btn_box = QVBoxLayout()
        btn_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_act = QPushButton("启动实时画面流")
        self.btn_act.setObjectName("PrimaryActionBtn")
        self.btn_act.setFixedSize(340, 50) 
        self.btn_act.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_act.clicked.connect(self._fire_cam_visual)
        
        hint_lbl = QLabel("提示：全画幅模式可确保 100% 物理视场角；全屏预览时可按键盘【Alt】+ 【F4】退出。")
        hint_lbl.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500; margin-top: 8px;")
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_box.addWidget(self.btn_act)
        btn_box.addWidget(hint_lbl)
        
        vlay.addLayout(btn_box)
        vlay.addStretch()
        
        self.dash_tab.addTab(pan, "2. 画面质检")

    def _toggle_custom_panel(self, checked):
        """控制自定义分辨率输入面板的激活状态"""
        self.custom_panel.setEnabled(checked)

    def _on_native_mode_selected(self, text):
        """当用户在下拉框选择硬件模式时，自动填入后方的输入框"""
        if "x" in text:
            parts = text.split("x")
            self.inp_custom_w.setText(parts[0].strip())
            self.inp_custom_h.setText(parts[1].strip())

    def _fetch_camera_modes(self):
        """调用 rpicam-hello 获取底层驱动支持的 Sensor 原生 Mode 列表"""
        self.cb_native_modes.clear()
        self.btn_fetch_modes.setText("读取中...")
        self.btn_fetch_modes.setEnabled(False)
        self.out_print("开始探测硬件底层原生传感器模式 (Hardware Mode Probing)...", "#0284C7")
        
        try:
            result = subprocess.run(['rpicam-hello', '--list-cameras'], capture_output=True, text=True, timeout=5)
            output = result.stdout
            
            # 正则提取形如 '4656x3496' 的分辨率串
            modes = re.findall(r'(\d+)x(\d+)\s+\[', output)
            
            if not modes:
                QMessageBox.warning(self, "探测失败", "未能解析到硬件原生模式，请确保相机已正确连接并配置。")
                self.out_print("硬件探测失败，未找到可用 Mode。", "#EF4444")
            else:
                # 剔除重复项并按面积降序排列
                unique_modes = sorted(list(set(modes)), key=lambda x: int(x[0])*int(x[1]), reverse=True)
                for w, h in unique_modes:
                    self.cb_native_modes.addItem(f"{w}x{h}")
                self.out_print(f"探测成功！共发现 {len(unique_modes)} 种原生模式。", "#059669")
                
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"探测命令执行失败:\n{str(e)}")
            self.out_print(f"探测异常: {str(e)}", "#EF4444")
            
        finally:
            self.btn_fetch_modes.setText("读取当前相机原生模式")
            self.btn_fetch_modes.setEnabled(True)

    def _fire_cam_visual(self):
        """组装参数并启动预览流"""
        if self.cam_job.state() == QProcess.ProcessState.NotRunning:
            opts = ["-t", "0"]
            
            # 1. 窗口模式组装
            if self.rad_f.isChecked(): 
                opts.append("--fullscreen")
            
            # 2. 预览分辨率组装 (使用 --viewfinder-mode 控制预览通道尺寸)
            if self.rad_res_max.isChecked():
                # 强行破解底层限制：静默探测相机的物理最大分辨率，并强制要求预览通道使用该分辨率
                self.out_print("正在探查底层物理最大分辨率...", "#64748B")
                max_w, max_h = self._get_max_resolution_silently()
                
                if max_w and max_h:
                    opts.extend(["--viewfinder-mode", f"{max_w}:{max_h}"])
                    self.out_print(f"请求画面流：[全画幅最大分辨率] 已强制锁定原生画幅 {max_w}x{max_h}", "#38BDF8")
                else:
                    self.out_print("警告: 物理画幅探测失败，交由底层自适应调度", "#F59E0B")
                
            elif self.rad_res_bin.isChecked():
                # 指定一个通用的 2x2 binning 级别预览分辨率
                opts.extend(["--viewfinder-mode", "2028:1520"]) 
                self.out_print("请求画面流：[Binning 高帧率模式]", "#38BDF8")
                
            elif self.rad_res_1080.isChecked():
                opts.extend(["--viewfinder-mode", "1920:1080"])
                self.out_print("请求画面流：[标准 1080P]", "#38BDF8")
                
            elif self.rad_res_custom.isChecked():
                cw = self.inp_custom_w.text().strip()
                ch = self.inp_custom_h.text().strip()
                if not cw or not ch:
                    QMessageBox.warning(self, "参数缺失", "请手动输入宽度和高度，或从原生模式下拉框中选择。")
                    return
                opts.extend(["--viewfinder-mode", f"{cw}:{ch}"])
                self.out_print(f"请求画面流：[自定义/原生模式] {cw}x{ch}", "#38BDF8")

            # 启动子进程
            self.cam_job.start("rpicam-still", opts)
            
            self.btn_act.setText("停止画面流 (Terminate)")
            self.btn_act.setObjectName("DangerActionBtn")
            self.btn_act.setStyle(self.btn_act.style())
            
        else:
            # 安全终止进程
            self.cam_job.terminate()
            self.cam_job.waitForFinished(1000)
            if self.cam_job.state() != QProcess.ProcessState.NotRunning: 
                self.cam_job.kill() 
                
            self.btn_act.setText("启动实时画面流")
            self.btn_act.setObjectName("PrimaryActionBtn")
            self.btn_act.setStyle(self.btn_act.style())
            self.out_print("画面流已被用户终止。", "#64748B")
    def _on_cam_job_finished(self, exit_code, exit_status):
        """无论进程是自然结束还是被 Alt+F4 强杀，都会触发此函数，安全重置按钮状态"""
        self.btn_act.setText("启动实时画面流")
        self.btn_act.setObjectName("PrimaryActionBtn")
        self.btn_act.setStyle(self.btn_act.style())
        self.out_print("画面流进程已结束 (窗口已关闭)。", "#64748B")

    def _fire_cam_visual(self):
        """组装参数并启动预览流"""
        if self.cam_job.state() == QProcess.ProcessState.NotRunning:
            opts = ["-t", "0"]
            if self.rad_f.isChecked(): opts.append("--fullscreen")
            
            if self.rad_res_max.isChecked():
                self.out_print("正在探查底层物理最大分辨率...", "#64748B")
                max_w, max_h = self._get_max_resolution_silently()
                if max_w and max_h:
                    opts.extend(["--viewfinder-mode", f"{max_w}:{max_h}"])
                    self.out_print(f"请求画面流：[全画幅最大分辨率] {max_w}x{max_h}", "#38BDF8")
                else:
                    self.out_print("警告: 物理画幅探测失败，交由底层自适应调度", "#F59E0B")
            elif self.rad_res_bin.isChecked():
                opts.extend(["--viewfinder-mode", "2028:1520"]) 
                self.out_print("请求画面流：[Binning 模式]", "#38BDF8")
            elif self.rad_res_1080.isChecked():
                opts.extend(["--viewfinder-mode", "1920:1080"])
                self.out_print("请求画面流：[标准 1080P]", "#38BDF8")
            elif self.rad_res_custom.isChecked():
                cw = self.inp_custom_w.text().strip()
                ch = self.inp_custom_h.text().strip()
                if not cw or not ch:
                    QMessageBox.warning(self, "参数缺失", "请手动输入宽度和高度。")
                    return
                opts.extend(["--viewfinder-mode", f"{cw}:{ch}"])
                self.out_print(f"请求画面流：[自定义] {cw}x{ch}", "#38BDF8")

            self.cam_job.start("rpicam-still", opts)
            self.btn_act.setText("停止画面流 (Terminate)")
            self.btn_act.setObjectName("DangerActionBtn")
            self.btn_act.setStyle(self.btn_act.style())
        else:
            # 安全终止进程，终止后会自动触发 _on_cam_job_finished 恢复按钮状态
            self.cam_job.terminate()
            self.cam_job.waitForFinished(1000)
            if self.cam_job.state() != QProcess.ProcessState.NotRunning: 
                self.cam_job.kill()

    def _get_max_resolution_silently(self):
        """后台静默获取相机的最大支持分辨率"""
        try:
            import subprocess
            import re
            # 执行底层探测指令
            result = subprocess.run(['rpicam-hello', '--list-cameras'], capture_output=True, text=True, timeout=3)
            modes = re.findall(r'(\d+)x(\d+)\s+\[', result.stdout)
            
            if modes:
                # 算出面积最大的那个模式
                unique_modes = sorted(list(set(modes)), key=lambda x: int(x[0])*int(x[1]), reverse=True)
                return unique_modes[0][0], unique_modes[0][1] # 返回最大 宽, 高
        except Exception:
            pass
        return None, None
    
    # ---------- 3. 单张拍照 (全面升级分辨率控制与动态命名) ----------
    def _tab_foto(self):
        u = QWidget()
        a = QVBoxLayout(u)
        a.setContentsMargins(18, 18, 18, 18)
        
        # === 捕获分辨率配置 ===
        grp_res = QGroupBox("1. 捕获分辨率预设 (Capture Resolution)")
        ly_res = QVBoxLayout()
        ly_res.setContentsMargins(20, 20, 20, 20)
        ly_res.setSpacing(14)
        
        self.rad_cap_max = QRadioButton("全画幅最大分辨率 (Full FOV Max)")
        self.rad_cap_max.setChecked(True)
        self.rad_cap_bin = QRadioButton("2x2 Binning 模式 (提升信噪比/夜视能力)")
        self.rad_cap_1080 = QRadioButton("标准 1080P 模式 (1920x1080)")
        
        # 自定义分辨率行
        cap_custom_ly = QHBoxLayout()
        self.rad_cap_custom = QRadioButton("自定义分辨率:")
        self.inp_cap_w = QLineEdit()
        self.inp_cap_w.setPlaceholderText("宽(W)")
        self.inp_cap_w.setValidator(QIntValidator(100, 10000))
        self.inp_cap_w.setFixedWidth(70)
        self.inp_cap_h = QLineEdit()
        self.inp_cap_h.setPlaceholderText("高(H)")
        self.inp_cap_h.setValidator(QIntValidator(100, 10000))
        self.inp_cap_h.setFixedWidth(70)
        lbl_x = QLabel("x")
        lbl_x.setStyleSheet("color: #64748B; font-weight: bold;")
        
        cap_custom_ly.addWidget(self.rad_cap_custom)
        cap_custom_ly.addWidget(self.inp_cap_w)
        cap_custom_ly.addWidget(lbl_x)
        cap_custom_ly.addWidget(self.inp_cap_h)
        cap_custom_ly.addStretch()
        
        ly_res.addWidget(self.rad_cap_max)
        ly_res.addWidget(self.rad_cap_bin)
        ly_res.addWidget(self.rad_cap_1080)
        ly_res.addLayout(cap_custom_ly)
        grp_res.setLayout(ly_res)
        a.addWidget(grp_res)
        
        # === 图像保存配置 ===
        self.pt = QLineEdit(os.path.expanduser("/home/pi/Pictures/QA_Captures"))
        self.dl = QSpinBox()
        self.dl.setRange(20, 60000)
        self.dl.setValue(1000) 
        # 💡 新增 {width} 和 {height} 智能占位符
        self.nt = QLineEdit("{sensor}_{width}x{height}_{time}.jpg")
        
        gp = QGridLayout()
        gp.setContentsMargins(20, 24, 20, 24)
        gp.setHorizontalSpacing(16)
        gp.setVerticalSpacing(16)
        
        gp.addWidget(QLabel("图片保存路径:"), 0, 0)
        bb = QPushButton("浏览...")
        bb.setObjectName("SecondaryBtn")
        bb.setCursor(Qt.CursorShape.PointingHandCursor)
        bb.clicked.connect(self._go_br_folder)
        f_l = QHBoxLayout()
        f_l.addWidget(self.pt, stretch=3)
        f_l.addWidget(bb, stretch=1)
        gp.addLayout(f_l, 0, 1)
        
        gp.addWidget(QLabel("预览时间 (ms):"), 1, 0)
        gp.addWidget(self.dl, 1, 1)
        
        gp.addWidget(QLabel("智能命名规则:"), 2, 0)
        gp.addWidget(self.nt, 2, 1)
        
        gg = QGroupBox("2. 图像保存设置 (File Settings)")
        gg.setLayout(gp)
        a.addWidget(gg)
        
        a.addSpacing(20)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        bo = QPushButton("打开文件夹")
        bo.setObjectName("SecondaryBtn")
        bo.setFixedSize(140, 48)
        bo.setCursor(Qt.CursorShape.PointingHandCursor)
        bo.clicked.connect(lambda: QProcess.startDetached("xdg-open", [self.pt.text()]) if os.path.exists(self.pt.text()) else None)
        
        self.bp = QPushButton("执行单帧抓拍")
        self.bp.setObjectName("PrimaryActionBtn")
        self.bp.setFixedSize(260, 48)
        self.bp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bp.clicked.connect(self._go_s_click)
        
        btn_box.addWidget(bo)
        btn_box.addSpacing(16)
        btn_box.addWidget(self.bp)
        btn_box.addStretch()
        
        a.addLayout(btn_box)
        a.addStretch()
        self.dash_tab.addTab(u, "3. 单张拍照")
    
    def _go_br_folder(self):
        res = QFileDialog.getExistingDirectory(self, "选择保存目录", self.pt.text())
        if res: self.pt.setText(res)

    def _go_s_click(self):
        if not self.__check_res(): return
            
        sensor_tag = self.active_in_test_sku['sensor'] if self.active_in_test_sku else "camera"
        os.makedirs(self.pt.text(), exist_ok=True)
        
        # 1. 解析目标分辨率
        opts = ["-t", str(self.dl.value())]
        cap_w, cap_h = "MAX", "MAX" # 兜底名
        
        if self.rad_cap_max.isChecked():
            # 静默获取物理分辨率以精准命名
            cw, ch = self._get_max_resolution_silently()
            if cw and ch:
                cap_w, cap_h = cw, ch
                opts.extend(["--width", cw, "--height", ch])
        elif self.rad_cap_bin.isChecked():
            cap_w, cap_h = "2028", "1520"
            opts.extend(["--width", cap_w, "--height", cap_h])
        elif self.rad_cap_1080.isChecked():
            cap_w, cap_h = "1920", "1080"
            opts.extend(["--width", cap_w, "--height", cap_h])
        elif self.rad_cap_custom.isChecked():
            cap_w = self.inp_cap_w.text().strip()
            cap_h = self.inp_cap_h.text().strip()
            if not cap_w or not cap_h:
                QMessageBox.warning(self, "参数缺失", "请手动输入自定义的宽和高。")
                return
            opts.extend(["--width", cap_w, "--height", cap_h])

        # 2. 动态替换文件名占位符
        targ_str = self.nt.text().replace("{sensor}", sensor_tag)\
                                 .replace("{width}", str(cap_w))\
                                 .replace("{height}", str(cap_h))\
                                 .replace("{time}", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        dest_n = os.path.join(self.pt.text(), targ_str)
        opts.extend(["-o", dest_n])
        
        self.task_job.start("rpicam-still", opts)
        self.bp.setEnabled(False)
        self.bp.setText("图像捕获中...")
        self.last_target_n = dest_n

    def _task_end(self, stat):
        self.bp.setEnabled(True)
        self.bp.setText("执行单帧抓拍")
        if stat == 0: 
            self.out_print(f"图像已保存至: {self.last_target_n}", "#059669")
        else:
            QMessageBox.critical(self, "执行失败", "抓拍进程异常，请查看日志。")
            self.out_print("捕获任务失败。", "#DC2626")

    # ---------- 4. 压力测试 ----------
    def _tab_qa_age(self):
        c = QWidget()
        y = QVBoxLayout(c)
        y.setContentsMargins(18, 18, 18, 18)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        self.age_bs = QButtonGroup(self)
        
        self.r_opt_10 = QRadioButton("10 次 (快速抽检)")
        self.r_opt_10.setProperty('ov', 10)
        self.r_opt_50 = QRadioButton("50 次 (标准产测)")
        self.r_opt_50.setProperty('ov', 50)
        self.r_opt_50.setChecked(True)
        self.r_opt_500 = QRadioButton("500 次 (极限老化)")
        self.r_opt_500.setProperty('ov', 500)
        
        self.age_bs.addButton(self.r_opt_10)
        self.age_bs.addButton(self.r_opt_50)
        self.age_bs.addButton(self.r_opt_500)

        top_row.addWidget(self.r_opt_10)
        top_row.addWidget(self.r_opt_50)
        top_row.addWidget(self.r_opt_500)
        
        self.r_custom = QRadioButton("自定义轮数:")
        self.spin_b = QSpinBox()
        self.spin_b.setRange(1, 10000)
        self.spin_b.setValue(100)
        self.age_bs.addButton(self.r_custom)
        
        top_row.addWidget(self.r_custom)
        top_row.addWidget(self.spin_b)
        
        opt_group = QGroupBox("老化测试策略")
        opt_group.setLayout(top_row)
        y.addWidget(opt_group)

        s_dash = QFrame()
        s_dash.setObjectName("CardPanel")
        l1 = QVBoxLayout(s_dash)
        l1.setContentsMargins(20, 24, 20, 24)
        l1.setSpacing(14)
        
        self.da_st = QLabel("引擎状态: 待机中")
        self.da_st.setStyleSheet("color: #64748B; font-weight: bold; font-size: 14px;")
        self.da_st.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.da_no = QLabel("进度：0 / 0  |  通过：0  |  失败：0")
        self.da_no.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.da_no.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        
        self.bar = QProgressBar()
        self.bar.setFixedHeight(14)
        
        l1.addWidget(self.da_st)
        l1.addWidget(self.da_no)
        l1.addWidget(self.bar)
        y.addWidget(s_dash)
        
        y.addSpacing(16)

        ch = QHBoxLayout()
        ch.addStretch()
        
        self.stg = QPushButton("中止测试")
        self.stg.setObjectName("DangerActionBtn")
        self.stg.setFixedSize(140, 48)
        self.stg.setEnabled(False)
        self.stg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stg.clicked.connect(self._sstop_chain)
        
        self.bg = QPushButton("开始执行压力测试")
        self.bg.setObjectName("PrimaryActionBtn")
        self.bg.setFixedSize(260, 48)
        self.bg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bg.clicked.connect(self._boot_age_chain)
        
        ch.addWidget(self.stg)
        ch.addSpacing(16)
        ch.addWidget(self.bg)
        ch.addStretch()
        
        y.addLayout(ch)
        y.addStretch()
        self.dash_tab.addTab(c, "4. 压力测试")

    def _boot_age_chain(self):
        if not self.__check_res(): return
        self.a_tot = 50
        for x in self.age_bs.buttons():
            if x.isChecked():
                self.a_tot = self.spin_b.value() if x == self.r_custom else x.property('ov')
                break

        self.a_sig = False; self.a_cur = 0; self.a_ok = 0; self.a_fail = 0
        self.bg.setEnabled(False); self.stg.setEnabled(True)
        self.bar.setMaximum(self.a_tot)
        self.bar.setValue(0)
        self.da_st.setText("引擎状态: 测试执行中...")
        self.da_st.setStyleSheet("color: #0284C7; font-weight: bold; font-size: 14px;")
        self.out_print(f"> 压力测试启动，设定轮数: {self.a_tot}", "#0284C7")
        self._cyc_next_loop()

    def _cyc_next_loop(self):
        if self.a_sig or self.a_cur >= self.a_tot: 
            self._conclu_chain(); return
        self.a_cur += 1 
        self.test_engine.start("rpicam-still", ["-t", "800", "-n"]) 

    def _age_iteration_fin(self, c_code):
        if c_code == 0: self.a_ok += 1
        else:
            self.a_fail += 1
            self.out_print(f"> 错误: 第 {self.a_cur} 轮进程异常 (Exit Code: {c_code})", "#DC2626")
        
        fstr = f"<span style='color:{'#DC2626' if self.a_fail>0 else '#64748B'};'>失败：{self.a_fail}</span>"
        self.da_no.setText(f"进度：{self.a_cur} / {self.a_tot}  |  通过：<span style='color:#059669;'>{self.a_ok}</span>  |  {fstr}")
        self.bar.setValue(self.a_cur)
        self._cyc_next_loop()

    def _sstop_chain(self):
        self.a_sig = True 
        self.da_st.setText("引擎状态: 人工介入终止")
        self.da_st.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 14px;")
        
    def _conclu_chain(self):
        self.bg.setEnabled(True); self.stg.setEnabled(False)
        if not self.a_sig:
            self.da_st.setText("引擎状态: 任务已完成")
            self.da_st.setStyleSheet("color: #059669; font-weight: bold; font-size: 14px;")
        self.out_print(f"> 任务终结 | 达成: {self.a_ok} 轮，故障: {self.a_fail} 轮。", "#059669")

    # ---------- 5. 型号库管理 (修复挤压，加入编辑功能) ----------
    def _tab_catalog(self):
        q = QWidget()
        vb = QVBoxLayout(q)
        vb.setContentsMargins(18, 16, 18, 16)
        vb.setSpacing(14)
        
        # === 表单区域 (上层，固定高度) ===
        u = QGroupBox("产品档案注册与编辑")
        gl = QGridLayout()
        gl.setContentsMargins(20, 24, 20, 24)
        gl.setHorizontalSpacing(16)
        gl.setVerticalSpacing(16)
        
        gl.addWidget(QLabel("产品 SKU:"), 0, 0)
        self.ks = QLineEdit()
        self.ks.setPlaceholderText("例如: B0165")
        gl.addWidget(self.ks, 0, 1)
        
        gl.addWidget(QLabel("芯片型号:"), 0, 2)
        self.sn = QLineEdit()
        self.sn.setPlaceholderText("例如: ov9281")
        gl.addWidget(self.sn, 0, 3)

        self.ovt = QLabel("系统驱动映射:")
        self.ovt.setStyleSheet("color: #0369A1; font-weight: bold;")
        gl.addWidget(self.ovt, 1, 0, 1, 2)
        self.sn.textChanged.connect(lambda txt: self.ovt.setText(f"系统驱动映射: dtoverlay={deduce_overlay(txt.strip())}"))

        gl.addWidget(QLabel("备注说明:"), 1, 2)
        self.cd = QLineEdit()
        self.cd.setPlaceholderText("选填，描述该模组特性")
        gl.addWidget(self.cd, 1, 3)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        abb = QPushButton("确认归档入库")
        abb.setObjectName("PrimaryActionBtn")
        abb.setFixedSize(260, 44)
        abb.setCursor(Qt.CursorShape.PointingHandCursor)
        abb.clicked.connect(self._ad_r_btn_event)
        btn_box.addWidget(abb)
        btn_box.addStretch()
        
        gl.addLayout(btn_box, 2, 0, 1, 4)
        u.setLayout(gl)
        vb.addWidget(u) # 默认添加，不给 stretch，防止压扁下面的表
        
        # === 底部表格区域 (下层，填满剩余空间) ===
        ggb = QGroupBox("系统设备映射库")
        gly = QVBoxLayout()
        gly.setContentsMargins(14, 18, 14, 16)
        gly.setSpacing(12)
        
        header_bar = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("表格筛选 (输入 SKU 或芯片名称)")
        self.filter_input.addAction(QIcon.fromTheme("edit-find"), QLineEdit.ActionPosition.LeadingPosition)
        self.filter_input.setTextMargins(-8, 0, 0, 0)
        self.filter_input.setFixedSize(300, 32)
        self.filter_input.textChanged.connect(self._filter_table)
        header_bar.addWidget(self.filter_input)
        
        header_bar.addStretch()
        
        rsb = QPushButton("恢复出厂库")
        rsb.setObjectName("SecondaryBtn")
        rsb.setCursor(Qt.CursorShape.PointingHandCursor)
        rsb.clicked.connect(self._fc_rr_)
        header_bar.addWidget(rsb)
        gly.addLayout(header_bar)
        
        self.ts = QTableWidget()
        self.ts.setColumnCount(4)
        self.ts.setHorizontalHeaderLabels(["SKU / 硬件芯片", "底层驱动 (Overlay)", "特性描述", "操作"])
        
        # 修复2: 指定明确的列宽拉伸策略，确保操作列有足够空间展示2个按钮
        header = self.ts.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.ts.setColumnWidth(3, 140) # 预留足够宽度给 [编辑][删除] 两个按钮
        
        self.ts.verticalHeader().setDefaultSectionSize(44)
        self.ts.verticalHeader().setVisible(False) 
        self.ts.setAlternatingRowColors(True)
        self.ts.setShowGrid(False)
        self.ts.setMinimumHeight(180) # 防挤压底线
        
        gly.addWidget(self.ts, stretch=1)
        ggb.setLayout(gly)
        
        # 把表格盒子分配 stretch=1 充满剩余高度
        vb.addWidget(ggb, stretch=1)
        
        self._rely()
        self.dash_tab.addTab(q, "5. 型号库管理")

    def _filter_table(self, text):
        search_str = text.lower()
        for row in range(self.ts.rowCount()):
            match = False
            for col in range(self.ts.columnCount() - 1):
                item = self.ts.item(row, col)
                if item and search_str in item.text().lower():
                    match = True
                    break
            self.ts.setRowHidden(row, not match)
            
    # 【新增功能】点击编辑按钮，回填数据到表单
    def _edit_record(self, item):
        self.ks.setText(item['sku'])
        self.sn.setText(item['sensor'])
        self.cd.setText(item['desc'])
        self.ks.setFocus() # 光标聚焦，引导用户

    def _ad_r_btn_event(self):
        sk = self.ks.text().upper().strip()
        sns = self.sn.text().lower().strip()
        ds = self.cd.text().strip()
        
        if not sk or not sns: 
            QMessageBox.critical(self, "输入校验", "SKU 和 芯片型号必须完整填写。")
            return 
        
        exist_h = -1
        for x, itms in enumerate(self.data_records):
            if itms['sku'] == sk:
                exist_h = x
                break
        
        npck = {"sku": sk, "sensor": sns, "overlay": deduce_overlay(sns), "desc": ds}
        
        # 如果存在则替换 (即更新)，不存在则插入顶部
        if exist_h >= 0: 
            self.data_records.pop(exist_h)
        self.data_records.insert(0, npck)
            
        DataEngine.commit_records(self.data_records)
        self._rely()
        self._sync_app_state()
        
        self.ks.clear()
        self.sn.clear()
        self.cd.clear()
        self.filter_input.clear() 
        QMessageBox.information(self, "归档成功", f"模组档案 {sk} 已成功保存/更新至系统。")

    def _fc_rr_(self):
        aa = QMessageBox.question(self, "安全确认", "此操作将抹除所有自定义记录并恢复默认库，是否继续？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if aa == QMessageBox.StandardButton.Yes: 
            self.data_records = generate_default_data() 
            DataEngine.commit_records(self.data_records)
            self._rely()
            self._sync_app_state()
            QMessageBox.information(self, "恢复完成", "系统库已重置为出厂状态。")
              
    def _rely(self):
        self.ts.setRowCount(0)
        for rx, o in enumerate(self.data_records):
            self.ts.insertRow(rx)
            self.ts.setItem(rx, 0, QTableWidgetItem(f"{o['sku']} [{o['sensor'].upper()}]"))
            self.ts.setItem(rx, 1, QTableWidgetItem(o['overlay']))
            self.ts.setItem(rx, 2, QTableWidgetItem(o['desc']))
            
            # 【修复3】：使用水平布局优雅包装“编辑”和“删除”两个按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(8, 4, 8, 4) # 合理边距防压扁
            action_layout.setSpacing(8)
            
            # 编辑按钮
            btn_edit = QPushButton("编辑")
            btn_edit.setObjectName("TableEditBtn") 
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, item=o: self._edit_record(item))
            
            # 删除按钮
            btn_del = QPushButton("删除")
            btn_del.setObjectName("TableDeleteBtn") 
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda _, target_i=o['sku']: self.__del_k(target_i))
            
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_del)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.ts.setCellWidget(rx, 3, action_widget)
            
        self._filter_table(self.filter_input.text())
              
    def __del_k(self, the_val):
        rp = QMessageBox.question(self, "删除授权", f"是否从设备映射库中永久移除 {the_val} ？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rp == QMessageBox.StandardButton.Yes:
            self.data_records = [x for x in self.data_records if x['sku'] != the_val]
            DataEngine.commit_records(self.data_records)
            self._rely()
            self._sync_app_state()