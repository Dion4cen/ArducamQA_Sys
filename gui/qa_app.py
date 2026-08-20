import os
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QTabWidget, QTextEdit, QMessageBox, QRadioButton, 
    QButtonGroup, QLineEdit, QSpinBox, QFileDialog, QProgressBar, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QProcess

from core.def_database import DataEngine, generate_default_data, deduce_overlay
from core.config_writer import RPiSystemManager

class QATestCenter(QMainWindow):
    # 工业暗色系通用样式
    FACTORY_STYLESHEET = """
        QMainWindow { background-color: #212529; color: #f8f9fa;}
        QWidget { color: #f8f9fa; font-family: 'Noto Sans CJK SC', 'Segoe UI', sans-serif;}
        
        QGroupBox {
            border: 1px solid #495057; border-radius: 6px; 
            margin-top: 15px; font-weight: bold; 
            background-color: #343A40;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; top: -8px; color: #CED4DA;}
        
        QLineEdit, QSpinBox, QComboBox {
            background-color: #495057; border: 1px solid #6C757D; border-radius: 4px; 
            padding: 5px; height: 32px; color: #f8f9fa;
        }
        
        QPushButton {
            background-color: #0D6EFD; color: white; border-radius: 5px; 
            padding: 8px; font-weight: bold; font-size: 14px; min-height: 40px;
        }
        QPushButton:hover { background-color: #3B71CA; }
        QPushButton:pressed { background-color: #1958b8; }
        QPushButton#BtnAlert { background-color: #DC3545; }
        QPushButton#BtnAlert:hover { background-color: #C82333; }
        QPushButton#BtnSuccess { background-color: #198754; }
        QPushButton#BtnSuccess:hover { background-color: #157347; }
        QPushButton:disabled { background-color: #6C757D; color: #ADB5BD; }
        
        QTabWidget::pane { border: 1px solid #495057; background: #343A40; border-radius: 4px; }
        QTabBar::tab { 
            background: #212529; color: #ADB5BD; padding: 10px 20px; margin: 1px;
            border-bottom: 2px solid transparent; 
        }
        QTabBar::tab:selected { background: #343A40; color: #0D6EFD; border-bottom: 2px solid #0D6EFD; }
        
        QTextEdit { background-color: #111; color: #A3E635; font-family: monospace; border: 1px solid #000; }
        QTableWidget { background-color: #343A40; border: 1px solid #495057; gridline-color: #495057;}
        QHeaderView::section { background-color: #212529; padding: 6px; font-weight: bold;}
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arducam Production QA Tool V1.2.0")
        self.resize(1024, 768)
        self.setStyleSheet(self.FACTORY_STYLESHEET)
        
        self.data_records = DataEngine.fetch_records()
        self.select_focus = None 
        
        # QProcess 异步进程对象
        self.cam_job = QProcess()
        self.cam_job.readyReadStandardOutput.connect(lambda: self._proc_std(self.cam_job, False))
        self.cam_job.readyReadStandardError.connect(lambda: self._proc_std(self.cam_job, True))
        
        self.task_job = QProcess()
        self.task_job.finished.connect(self._task_end)
        self.task_job.readyReadStandardOutput.connect(lambda: self._proc_std(self.task_job, False))
        self.task_job.readyReadStandardError.connect(lambda: self._proc_std(self.task_job, True))

        self.test_engine = QProcess()
        self.test_engine.finished.connect(self._age_iteration_fin)
        self.a_tot = 0; self.a_cur = 0; self.a_ok = 0; self.a_fail = 0; self.a_sig = False
        
        self._construct_canvas()

    def out_print(self, msg_str, severity_clr="#00FF00"):
        time_pref = datetime.datetime.now().strftime("[%H:%M:%S]")
        formatted = f'<span style="color:{severity_clr};">{time_pref} {msg_str}</span>'
        self.logs.append(formatted)
        self.logs.verticalScrollBar().setValue(self.logs.verticalScrollBar().maximum())
         
    def _proc_std(self, proc_node, is_error):
        color = "#F44336" if is_error else "#D4D4D8"
        content_payload = proc_node.readAllStandardError() if is_error else proc_node.readAllStandardOutput()
        msg = content_payload.data().decode("utf-8", "ignore").strip()
        if msg: 
            self.out_print(msg, color)

    def _construct_canvas(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        topdown_grid = QVBoxLayout(widget)

        # 权限警告
        if not RPiSystemManager.check_permissions():
            hint_q = QLabel("⚠️ Warning: Non-root user. Modifying /boot/config.txt requires sudo privileges.")
            hint_q.setStyleSheet("background-color: #FFC107; color: #000; font-weight: bold; padding: 8px; border-radius: 4px;")
            topdown_grid.addWidget(hint_q)

        # Top Bar
        banner = QHBoxLayout()
        _, dev_s = RPiSystemManager.auto_scan_status()
        self.top_os_sensor_lbl = QLabel(f"{dev_s}")
        self.top_os_sensor_lbl.setStyleSheet("color: #0DCAF0; font-weight: bold;")
        
        sku_indict = QLabel("选择被测型号 (Select SKU):")
        self.box_camsel = QComboBox()
        self.box_camsel.setMinimumWidth(320)
        self.box_camsel.currentIndexChanged.connect(self._selection_reacting_call)
        
        banner.addWidget(self.top_os_sensor_lbl, stretch=2)
        banner.addWidget(sku_indict)
        banner.addWidget(self.box_camsel)
        topdown_grid.addLayout(banner)

        # Tabs
        self.dash_tab = QTabWidget()
        self._tab_init()        
        self._tab_quality()      
        self._tab_foto()      
        self._tab_qa_age()      
        self._tab_catalog()       
        topdown_grid.addWidget(self.dash_tab, stretch=7)
        
        # Bottom Console
        term = QGroupBox("控制台日志 (Console Logs)")
        lgy = QVBoxLayout()
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        clear_b = QPushButton("清空日志 (Clear Log)")
        clear_b.setMinimumHeight(30)
        clear_b.clicked.connect(self.logs.clear)
        lgy.addWidget(self.logs)
        lgy.addWidget(clear_b)
        term.setLayout(lgy)
        topdown_grid.addWidget(term, stretch=2)
        
        self._push_cb_data_init()
        self.out_print("System initialized successfully.", "#28A745")

    def _push_cb_data_init(self):
        self.box_camsel.blockSignals(True)
        self.box_camsel.clear()
        for idx in self.data_records:
            self.box_camsel.addItem(f"{idx['sku']} | {idx['sensor'].upper()} - {idx['desc']}", userData=idx)
        self.box_camsel.blockSignals(False)
        self.box_camsel.setCurrentIndex(0)
        self._selection_reacting_call()

    def _selection_reacting_call(self):
        if self.box_camsel.count() <= 0: 
            return 
        d = self.box_camsel.currentData()
        self.select_focus = d
        if hasattr(self, 'label_bind'):
            self.label_bind.setText(f"当前选中: SKU [{d['sku']}] | Sensor [{d['sensor'].upper()}]\n即将写入指令: dtoverlay={d['overlay']}")

    def __check_res(self):
        if self.cam_job.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.warning(self, "Device Busy", "相机正在被预览占用，请先停止预览再执行此操作。")
            return False 
        return True

    # ---------- Tab 1 : Driver Config ----------
    def _tab_init(self):
        ui_q = QWidget()
        y = QVBoxLayout(ui_q)
        area = QGroupBox("系统驱动配置 (Driver Setup)")
        ay = QVBoxLayout()
        self.label_bind = QLabel("")
        self.label_bind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_bind.setStyleSheet("font-size: 15px; margin: 15px 0; color: #FFF;")
        
        btn_go = QPushButton("⚙️ 写入系统驱动 (Write config.txt)")
        btn_go.setObjectName("BtnSuccess")
        btn_go.clicked.connect(self._run_rewrite_rpi_sys)
        
        desp = QLabel("说明: 写入配置前会自动备份原文件为 .bak。修改后必须重启树莓派方可点亮相机。")
        desp.setStyleSheet("color: #ADB5BD;")
        
        ay.addWidget(self.label_bind)
        ay.addWidget(desp)
        ay.addWidget(btn_go)
        area.setLayout(ay)
        y.addWidget(area)
        y.addStretch()
        self.dash_tab.addTab(ui_q, "1. 驱动配置 (Driver)")
         
    def _run_rewrite_rpi_sys(self):
        code, resp = RPiSystemManager.enforce_driver_target(self.select_focus['overlay'])
        if not code: 
            QMessageBox.critical(self, "Error", f"写入失败:\n{resp}")
        else:
            ok = QMessageBox.question(self, "Success", f"{resp}\n驱动写入成功！是否立即重启树莓派？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ok == QMessageBox.StandardButton.Yes: 
                QProcess.startDetached("sudo", ["reboot"])

    # ---------- Tab 2 : Preview QA ----------
    def _tab_quality(self):
        pan = QWidget()
        vlay = QVBoxLayout(pan)
        cfg_r = QGroupBox("预览模式选择 (Preview Mode)")
        ly = QHBoxLayout()
        
        self.rad_w = QRadioButton("窗口预览 (Window Mode: rpicam-still -t 0)")
        self.rad_w.setChecked(True)
        self.rad_f = QRadioButton("全屏质检 (Fullscreen Mode: rpicam-still -t 0 -f)")
        
        ly.addWidget(self.rad_w)
        ly.addWidget(self.rad_f)
        cfg_r.setLayout(ly)
        vlay.addWidget(cfg_r)
        
        self.btn_act = QPushButton("▶ 开启实时画面预览 (Start Preview)")
        self.btn_act.setObjectName("BtnSuccess")
        self.btn_act.setMinimumHeight(55)
        self.btn_act.clicked.connect(self._fire_cam_visual)
        vlay.addWidget(self.btn_act)
        vlay.addStretch()
        
        self.dash_tab.addTab(pan, "2. 画面质检 (Preview)")
        
    def _fire_cam_visual(self):
        if self.cam_job.state() == QProcess.ProcessState.NotRunning:
            opts = ["-t", "0"]
            if self.rad_f.isChecked(): 
                opts.append("-f")
            self.cam_job.start("rpicam-still", opts)
            self.btn_act.setText("⏹ 停止画面预览 (Stop Preview)")
            self.btn_act.setObjectName("BtnAlert")
            self.btn_act.setStyle(self.btn_act.style())
        else:
            self.cam_job.terminate()
            self.cam_job.waitForFinished(1000)
            if self.cam_job.state() != QProcess.ProcessState.NotRunning: 
                self.cam_job.kill() 
            self.btn_act.setText("▶ 开启实时画面预览 (Start Preview)")
            self.btn_act.setObjectName("BtnSuccess")
            self.btn_act.setStyle(self.btn_act.style())

    # ---------- Tab 3 : Capture Image ----------
    def _tab_foto(self):
        u = QWidget()
        a = QVBoxLayout(u)
        self.pt = QLineEdit(os.path.expanduser("~/Pictures/QA_Captures"))
        self.dl = QSpinBox()
        self.dl.setRange(20, 60000)
        self.dl.setValue(1000) 
        self.nt = QLineEdit("{sensor}_{time}.jpg")
        
        gp = QGridLayout()
        gp.addWidget(QLabel("保存目录 (Save Directory):"), 0, 0)
        bb = QPushButton("浏览 (Browse...)")
        bb.clicked.connect(self._go_br_folder)
        f_l = QHBoxLayout()
        f_l.addWidget(self.pt, stretch=3)
        f_l.addWidget(bb, stretch=1)
        gp.addLayout(f_l, 0, 1)
        
        gp.addWidget(QLabel("曝光等待延时 (Delay ms):"), 1, 0)
        gp.addWidget(self.dl, 1, 1)
        
        gp.addWidget(QLabel("文件名规则 (File Name):"), 2, 0)
        gp.addWidget(self.nt, 2, 1)
        
        gg = QGroupBox("拍照参数配置 (Capture Settings)")
        gg.setLayout(gp)
        
        self.bp = QPushButton("📸 执行单张拍照 (Capture Once)")
        self.bp.setObjectName("BtnSuccess")
        self.bp.clicked.connect(self._go_s_click)
        
        bo = QPushButton("📁 打开保存文件夹 (Open Folder)")
        bo.clicked.connect(lambda: QProcess.startDetached("xdg-open", [self.pt.text()]) if os.path.exists(self.pt.text()) else None)

        a.addWidget(gg)
        a.addWidget(self.bp)
        a.addWidget(bo)
        a.addStretch()
        self.dash_tab.addTab(u, "3. 单张拍照 (Capture)")
    
    def _go_br_folder(self):
        res = QFileDialog.getExistingDirectory(self, "Select Directory", self.pt.text())
        if res: 
            self.pt.setText(res)

    def _go_s_click(self):
        if not self.__check_res(): 
            return
        os.makedirs(self.pt.text(), exist_ok=True)
        targ_str = self.nt.text().replace("{sensor}", self.select_focus['sensor']).replace("{time}", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        dest_n = os.path.join(self.pt.text(), targ_str)
        self.task_job.start("rpicam-still", ["-t", str(self.dl.value()), "-o", dest_n])
        self.bp.setEnabled(False)
        self.bp.setText("Capturing...")
        self.last_target_n = dest_n

    def _task_end(self, stat):
        self.bp.setEnabled(True)
        self.bp.setText("📸 执行单张拍照 (Capture Once)")
        if stat == 0: 
            self.out_print(f"Image saved: {self.last_target_n}", "#28A745")
        else:
            QMessageBox.critical(self, "Error", "拍照失败，请查看控制台报错输出。")
            self.out_print("Capture failed.", "#DC3545")

    # ---------- Tab 4 : Stress Test (Burn-in) ----------
    def _tab_qa_age(self):
        c = QWidget()
        y = QVBoxLayout(c)
        o_group = QGroupBox("测试轮次配置 (Cycle Settings)")
        o_g = QHBoxLayout()
        self.age_bs = QButtonGroup(self)
        
        self.r_opt_10 = QRadioButton("10 次 (Quick QA)")
        self.r_opt_10.setProperty('ov', 10)
        self.r_opt_50 = QRadioButton("50 次 (Standard)")
        self.r_opt_50.setProperty('ov', 50)
        self.r_opt_50.setChecked(True)
        self.r_opt_500 = QRadioButton("500 次 (Burn-in)")
        self.r_opt_500.setProperty('ov', 500)
        
        self.age_bs.addButton(self.r_opt_10)
        self.age_bs.addButton(self.r_opt_50)
        self.age_bs.addButton(self.r_opt_500)

        o_g.addWidget(self.r_opt_10)
        o_g.addWidget(self.r_opt_50)
        o_g.addWidget(self.r_opt_500)
        
        self.r_custom = QRadioButton("自定义 (Custom):")
        self.spin_b = QSpinBox()
        self.spin_b.setRange(1, 10000)
        self.spin_b.setValue(100)
        self.age_bs.addButton(self.r_custom)
        
        o_g.addWidget(self.r_custom)
        o_g.addWidget(self.spin_b)
        o_group.setLayout(o_g)
        y.addWidget(o_group)

        # 实时看板
        s_dash = QWidget()
        s_dash.setStyleSheet("background-color: #212529; border: 1px solid #6C757D; border-radius: 6px;")
        l1 = QVBoxLayout(s_dash)
        
        self.da_st = QLabel("状态: 待机空闲 (Idle)")
        self.da_st.setStyleSheet("color: #FFC107; font-weight: bold; font-size: 16px;")
        self.da_st.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.da_no = QLabel("进度: 0 / 0 | 成功 (Pass): 0 | 失败 (Fail): 0")
        self.da_no.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.da_no.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        
        self.bar = QProgressBar()
        self.bar.setFixedHeight(26)
        self.bar.setStyleSheet("QProgressBar { text-align: center; font-weight: bold; } QProgressBar::chunk { background: #198754; }")
        
        l1.addWidget(self.da_st)
        l1.addWidget(self.da_no)
        l1.addWidget(self.bar)
        y.addWidget(s_dash)

        # 控制按钮
        ch = QHBoxLayout()
        self.bg = QPushButton("▶ 开始压力测试 (Start Stress Test)")
        self.bg.setObjectName("BtnSuccess")
        self.stg = QPushButton("⏹ 强制停止 (Stop)")
        self.stg.setObjectName("BtnAlert")
        self.stg.setEnabled(False)

        self.bg.clicked.connect(self._boot_age_chain)
        self.stg.clicked.connect(self._sstop_chain)
        ch.addWidget(self.bg, stretch=2)
        ch.addWidget(self.stg, stretch=1)
        y.addLayout(ch)

        self.dash_tab.addTab(c, "4. 压力测试 (Stress Test)")

    def _boot_age_chain(self):
        if not self.__check_res(): 
            return
        
        self.a_tot = 50
        for x in self.age_bs.buttons():
            if x.isChecked():
                self.a_tot = self.spin_b.value() if x == self.r_custom else x.property('ov')
                break

        self.a_sig = False
        self.a_cur = 0
        self.a_ok = 0
        self.a_fail = 0
        
        self.bg.setEnabled(False)
        self.stg.setEnabled(True)
        self.bar.setMaximum(self.a_tot)
        self.bar.setValue(0)
        
        self.da_st.setText("状态: 正在测试中 (Testing...)")
        self.da_st.setStyleSheet("color: #0DCAF0; font-weight: bold; font-size: 16px;")
        self.out_print(f"=== Stress Test Started: Total {self.a_tot} Cycles ===", "#0DCAF0")
        self._cyc_next_loop()

    def _cyc_next_loop(self):
        if self.a_sig or self.a_cur >= self.a_tot: 
            self._conclu_chain()
            return
        self.a_cur += 1 
        self.test_engine.start("rpicam-still", ["-t", "800", "-n"]) 

    def _age_iteration_fin(self, c_code):
        if c_code == 0: 
            self.a_ok += 1
        else:
            self.a_fail += 1
            self.out_print(f"Cycle {self.a_cur} Failed with exit code {c_code}", "#F44336")
        
        self.da_no.setText(f"进度: {self.a_cur} / {self.a_tot} | 成功 (Pass): {self.a_ok} | 失败 (Fail): {self.a_fail}")
        self.bar.setValue(self.a_cur)
        self._cyc_next_loop()

    def _sstop_chain(self):
        self.a_sig = True 
        self.da_st.setText("状态: 已被人工终止 (Stopped by User)")
        self.da_st.setStyleSheet("color: #DC3545; font-weight: bold; font-size: 16px;")
        
    def _conclu_chain(self):
        self.bg.setEnabled(True)
        self.stg.setEnabled(False)
        self.da_st.setText("状态: 测试完成 (Finished)")
        self.da_st.setStyleSheet("color: #198754; font-weight: bold; font-size: 16px;")
        self.out_print(f"=== Stress Test Finished. Pass: {self.a_ok}, Fail: {self.a_fail} ===", "#198754")

    # ---------- Tab 5 : SKU Database Manager ----------
    def _tab_catalog(self):
        q = QWidget()
        vb = QVBoxLayout(q)
        
        # Form
        u = QGroupBox("录入新相机型号 (Add New SKU)")
        gl = QGridLayout()
        
        gl.addWidget(QLabel("产品 SKU (必填):"), 0, 0)
        self.ks = QLineEdit()
        self.ks.setPlaceholderText("如: B0165")
        gl.addWidget(self.ks, 0, 1)
        
        gl.addWidget(QLabel("Sensor 型号 (必填):"), 0, 2)
        self.sn = QLineEdit()
        self.sn.setPlaceholderText("如: ov9281")
        gl.addWidget(self.sn, 0, 3)

        self.ovt = QLabel("dtoverlay: (自动生成)")
        self.ovt.setStyleSheet("color: #0DCAF0;")
        gl.addWidget(self.ovt, 1, 0, 1, 2)
        self.sn.textChanged.connect(lambda txt: self.ovt.setText(f"dtoverlay: {deduce_overlay(txt.strip())}")) 

        gl.addWidget(QLabel("中文说明:"), 1, 2)
        self.cd = QLineEdit()
        self.cd.setPlaceholderText("如: OV9281 黑白全局快门")
        gl.addWidget(self.cd, 1, 3)
        
        abb = QPushButton("💾 保存到数据库 (Save to DB)")
        abb.setObjectName("BtnSuccess")
        abb.clicked.connect(self._ad_r_btn_event)
        gl.addWidget(abb, 2, 0, 1, 4)
        u.setLayout(gl)
        vb.addWidget(u)
        
        # Table
        ggb = QGroupBox("当前相机型号库 (Camera Database)")
        gly = QVBoxLayout()
        self.ts = QTableWidget()
        self.ts.setColumnCount(4)
        self.ts.setHorizontalHeaderLabels(["SKU / 芯片", "驱动 (Overlay)", "中文描述", "操作"])
        self.ts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        rsb = QPushButton("🔄 恢复出厂默认型号库 (Reset Factory DB)")
        rsb.setObjectName("BtnAlert")
        rsb.clicked.connect(self._fc_rr_)
        
        gly.addWidget(self.ts)
        gly.addWidget(rsb)
        ggb.setLayout(gly)
        vb.addWidget(ggb)
        
        self._rely()
        self.dash_tab.addTab(q, "5. 型号库管理 (SKU Manager)")

    def _ad_r_btn_event(self):
        sk = self.ks.text().upper().strip()
        sns = self.sn.text().lower().strip()
        ds = self.cd.text().strip()
        
        if not sk or not sns: 
            QMessageBox.critical(self, "Error", "SKU 和 Sensor 均不能为空！")
            return 
        
        exist_h = -1
        for x, itms in enumerate(self.data_records):
            if itms['sku'] == sk:
                exist_h = x
                break
        
        npck = {"sku": sk, "sensor": sns, "overlay": deduce_overlay(sns), "desc": ds}
        if exist_h >= 0: 
            self.data_records[exist_h] = npck
        else: 
            self.data_records.insert(0, npck)
            
        DataEngine.commit_records(self.data_records)
        self._rely()
        self._push_cb_data_init()
        self.ks.clear()
        self.sn.clear()
        self.cd.clear()
        QMessageBox.information(self, "Success", f"型号 {sk} 保存成功！")

    def _fc_rr_(self):
        aa = QMessageBox.question(self, "Confirm Reset", "确定要清空自定义数据，恢复到出厂默认的型号库吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if aa == QMessageBox.StandardButton.Yes: 
            self.data_records = generate_default_data() 
            DataEngine.commit_records(self.data_records)
            self._rely()
            self._push_cb_data_init()
            QMessageBox.information(self, "Success", "数据库已恢复出厂设置。")
              
    def _rely(self):
        self.ts.setRowCount(0)
        for rx, o in enumerate(self.data_records):
            self.ts.insertRow(rx)
            self.ts.setItem(rx, 0, QTableWidgetItem(f"{o['sku']} [{o['sensor'].upper()}]"))
            self.ts.setItem(rx, 1, QTableWidgetItem(o['overlay']))
            self.ts.setItem(rx, 2, QTableWidgetItem(o['desc']))
            
            bk = QPushButton("删除 (Delete)")
            bk.setStyleSheet("background-color: #DC3545; color: white; font-weight: bold;")
            bk.clicked.connect(lambda _, target_i=o['sku']: self.__del_k(target_i))
            self.ts.setCellWidget(rx, 3, bk)
              
    def __del_k(self, the_val):
        rp = QMessageBox.question(self, "Confirm Delete", f"确定要从数据库中删除型号: {the_val} 吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rp == QMessageBox.StandardButton.Yes:
            self.data_records = [x for x in self.data_records if x['sku'] != the_val]
            DataEngine.commit_records(self.data_records)
            self._rely()
            self._push_cb_data_init()
