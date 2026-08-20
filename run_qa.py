import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui.qa_app import QATestCenter

def exception_hook(type, value, tb):
    """全局级别安全防护拦截体系阻止黑屏闪退异常退出"""
    msg = "".join(traceback.format_exception(type, value, tb))
    print(f"CRITICAL APP FAULT OCCURRED:\n{msg}")

if __name__ == "__main__":
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    
    # 将此作为工业终端大屏应用运行 渲染等启动策略 
    root_window = QATestCenter()
    root_window.show()

    # 应用保护循环策略！主引擎事件循环开启等!
    sys.exit(app.exec())
