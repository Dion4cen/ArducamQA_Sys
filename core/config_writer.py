import os
import shutil
from datetime import datetime

class RPiSystemManager:
    CFG_PATH = "/boot/firmware/config.txt" if os.path.exists("/boot/firmware/config.txt") else "/boot/config.txt"
    HISTORY_LOG = "driver_change_history.log"
    
    # 显卡、音频等非相机系统 overlay（严禁误删）
    SYSTEM_IGNORE_OVERLAYS = [
        "vc4-kms-v3d", "vc4-fkms-v3d", "vc4-kms-v3d-pi4", "vc4-kms-v3d-pi5", 
        "dwc2", "disable-bt", "disable-wifi", "i2c-rtc", "w1-gpio"
    ]

    @staticmethod
    def check_permissions():
        return os.geteuid() == 0

    @staticmethod
    def auto_scan_status():
        """检索 [all] 区域或全局已生效的相机驱动"""
        try:
            if not os.path.exists(RPiSystemManager.CFG_PATH):
                return False, "[诊断] 未找到 config.txt 配置文件"

            with open(RPiSystemManager.CFG_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_section = "global"
            all_section_overlays = []
            other_camera_overlays = []
            auto_detect = "未知"

            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith("#"):
                    continue

                if clean_line.startswith("[") and clean_line.endswith("]"):
                    current_section = clean_line[1:-1].lower()
                    continue

                if "camera_auto_detect=" in clean_line:
                    auto_detect = clean_line.split("=")[-1].strip()

                if clean_line.startswith("dtoverlay="):
                    overlay_name = clean_line.split("=")[-1].strip()
                    if overlay_name in RPiSystemManager.SYSTEM_IGNORE_OVERLAYS:
                        continue

                    if current_section == "all":
                        all_section_overlays.append(overlay_name)
                    elif any(k in overlay_name.lower() for k in ["imx", "ov", "arducam", "camera"]):
                        other_camera_overlays.append(overlay_name)

            active_cam = all_section_overlays[-1] if all_section_overlays else (other_camera_overlays[-1] if other_camera_overlays else None)

            if active_cam:
                res_info = f"[已生效驱动]: dtoverlay={active_cam} | [自动探测]: {auto_detect}"
            else:
                res_info = f"[已生效驱动]: 无专用相机驱动 | [自动探测]: {auto_detect}"

            return True, res_info
        except Exception as e:
            return False, f"[检测异常]: {e}"

    @staticmethod
    def enforce_driver_target(target_overlay):
        if not RPiSystemManager.check_permissions():
            return False, "权限不足：修改内核配置需要 sudo 权限。"

        try:
            # 1. 记录变更日志到独立文件 (不污染 config.txt)
            with open(RPiSystemManager.HISTORY_LOG, "a", encoding="utf-8") as log_f:
                log_f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 变更驱动 -> dtoverlay={target_overlay}\n")

            # 2. 仅保留单个固定备份文件
            shutil.copy2(RPiSystemManager.CFG_PATH, RPiSystemManager.CFG_PATH + ".bak")

            with open(RPiSystemManager.CFG_PATH, "r", encoding='utf-8') as f:
                lines = f.readlines()

            # 3. 查漏补缺与就地更新 (零备注、零多余废行)
            cleaned_lines = []
            has_auto_detect = False
            has_all_section = False
            current_section = "global"

            for ln in lines:
                raw = ln.strip()

                # 清理历史可能遗留的工具注释行
                if any(tag in raw for tag in ["Arducam 工具写入", "由测试工具覆盖替换", "注释自 QA Tool"]):
                    continue

                if raw.startswith("[") and raw.endswith("]"):
                    current_section = raw[1:-1].lower()
                    if current_section == "all":
                        has_all_section = True

                # 规范化 camera_auto_detect=0
                if raw.startswith("camera_auto_detect="):
                    cleaned_lines.append("camera_auto_detect=0\n")
                    has_auto_detect = True
                    continue

                # 移除旧的相机 overlay (保留显卡驱动)
                if raw.startswith("dtoverlay="):
                    drv = raw.split("=")[-1].strip()
                    if drv not in RPiSystemManager.SYSTEM_IGNORE_OVERLAYS and any(k in drv for k in ["imx", "ov", "arducam", "hawkeye", "pivariety"]):
                        continue  # 移除旧的相机驱动行

                cleaned_lines.append(ln)

            # 4. 组装新配置写入 [all] 分区
            final_lines = []
            target_entry = f"dtoverlay={target_overlay}\n"

            if has_all_section:
                for ln in cleaned_lines:
                    final_lines.append(ln)
                    if ln.strip().lower() == "[all]":
                        if not has_auto_detect:
                            final_lines.append("camera_auto_detect=0\n")
                            has_auto_detect = True
                        final_lines.append(target_entry)
            else:
                final_lines = cleaned_lines
                if not final_lines[-1].endswith("\n"):
                    final_lines.append("\n")
                final_lines.append("\n[all]\n")
                if not has_auto_detect:
                    final_lines.append("camera_auto_detect=0\n")
                final_lines.append(target_entry)

            with open(RPiSystemManager.CFG_PATH, "w", encoding='utf-8') as f:
                f.writelines(final_lines)

            return True, f"驱动配置已更新为: dtoverlay={target_overlay}\n变更已记录至 {RPiSystemManager.HISTORY_LOG}"

        except Exception as crash:
            return False, str(crash)
