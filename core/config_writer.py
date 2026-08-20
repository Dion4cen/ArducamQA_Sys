import os
import shutil
import re
from datetime import datetime

class RPiSystemManager:
    # 动态匹配现行 OS 中驱动设置的位置 兼容旧版到 Trixie OS 统辖系统配置 
    CFG_PATH = "/boot/firmware/config.txt" if os.path.exists("/boot/firmware/config.txt") else "/boot/config.txt"
    
    @staticmethod
    def check_permissions():
        """提供基于系统的特权使用判定检测"""
        return os.geteuid() == 0

    @staticmethod
    def auto_scan_status():
        """负责扫描当在运行前激活和失效的当前底层参数"""
        try:
            with open(RPiSystemManager.CFG_PATH, 'r') as f:
                content = f.read()
            # 正则截取未屏蔽的相关信息 (不含井号开头的）
            active_mod = re.search(r"^dtoverlay=([a-zA-Z0-9_\-]+)", content, flags=re.MULTILINE)
            active_det = re.search(r"^camera_auto_detect=(0|1)", content, flags=re.MULTILINE)

            res_info = "[诊断]"
            res_info += f" 当前活跃型号节点: dtoverlay={active_mod.group(1)} | " if active_mod else " (暂未检出被指向生效模组) | "
            res_info += f" 设备auto策略开关值: {active_det.group(1)}" if active_det else ""
            return True, res_info
        except Exception as e:
            return False, f"[获取底层状态参数异常]: {e}"

    @staticmethod
    def enforce_driver_target(target_overlay):
        if not RPiSystemManager.check_permissions():
            return False, "系统权限验证驳回(Access Denied)：更改内核挂载请先利用 sudo 等执行最高提权。"
            
        backup_stamp = datetime.now().strftime("%y%m%d%H%M%S")
        backup_f = RPiSystemManager.CFG_PATH + f".qa_bkp_{backup_stamp}"
        try:
            shutil.copy2(RPiSystemManager.CFG_PATH, backup_f)
            
            with open(RPiSystemManager.CFG_PATH, "r") as f:
                 lines = f.readlines()
                 
            updated_doc = []
            for ln in lines:
                 # 去活默认系统设备侦听机制 (树莓系统必须关 0 才强制认自己的新版覆盖逻辑 )
                 if "camera_auto_detect=1" in ln:
                     updated_doc.append("camera_auto_detect=0\n")
                     continue
                 
                 # Regex 阻断旧有的其它残留挂入项目 (不全,但针对通用核心清除屏蔽）  
                 if ln.startswith("dtoverlay=") and ("ov" in ln or "imx" in ln or "arducam" in ln):
                     updated_doc.append(f"# {ln.strip()} (注释自 QA Tool 环境覆盖)\n")
                     continue
                     
                 updated_doc.append(ln)

            # Insert bottom instruction appending 追放目标信息于末端载入 
            updated_doc.append(f"\n# ====== 变更者: 工厂级检测产线治具管理程式 ====\n")
            updated_doc.append(f"dtoverlay={target_overlay}\n")

            with open(RPiSystemManager.CFG_PATH, "w") as f:
                f.writelines(updated_doc)
                
            return True, f"✅ 文件重新指向与应用写配覆合指令完成操作.  备份于 : {backup_f} 下记录生成..."
            
        except Exception as crash:
             return False, str(crash)
