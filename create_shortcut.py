import os
import stat
import getpass

def create_exe_like_shortcut():
    project_dir = os.path.abspath(os.path.dirname(__file__))
    main_script = os.path.join(project_dir, "run_qa.py") 
    
    # 获取当前真实的用户名（即使你用 sudo 运行这个脚本，也能准确拿到，比如 'pi'）
    current_user = os.environ.get('SUDO_USER', getpass.getuser())
    
    # ========================================================
    # 核心大招：自动配置 Linux 的 Sudo 免密白名单
    # 彻底告别开机第一次需要输入密码 'q' 的烦恼！
    # ========================================================
    print("\n>>> 正在配置系统级免密白名单，为您打造纯净 .exe 体验...")
    print(">>> 【注意】在此步骤中，系统可能会最后一次要求您输入密码（q）进行授权：")
    sudoers_rule = f"{current_user} ALL=(ALL) NOPASSWD: ALL"
    os.system(f"echo '{sudoers_rule}' | sudo tee /etc/sudoers.d/010_qa_nopasswd > /dev/null")

    # ========================================================
    # 生成静默启动跳板脚本 (完全杀掉黑框，后台运行)
    # ========================================================
    launcher_script = os.path.join(project_dir, "launch_qa.sh")
    launcher_content = f"""#!/bin/bash
cd "{project_dir}"

# 1. 强制使用 X11 渲染，解决 Wayland 环境的警告
export QT_QPA_PLATFORM=xcb

# 2. 静默授权画图权限
xhost +local: > /dev/null 2>&1

# 3. 将 GUI 程序彻底扔进系统后台静默运行，丢弃所有无用日志
nohup sudo -E XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" WAYLAND_DISPLAY="$WAYLAND_DISPLAY" DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" python3 "{main_script}" > /dev/null 2>&1 &
"""
    with open(launcher_script, "w", encoding="utf-8") as f:
        f.write(launcher_content)
    os.chmod(launcher_script, os.stat(launcher_script).st_mode | stat.S_IEXEC)


    # ========================================================
    # 生成终极桌面快捷方式
    # ========================================================
    icon_path = os.path.join(project_dir, "logo.png")
    if not os.path.exists(icon_path):
        icon_path = "camera-photo"

    # Terminal=false 彻底关闭黑色终端
    desktop_file_content = f"""[Desktop Entry]
Name=Arducam QA Studio
Comment=Arducam 产线自动测试工具
Exec="{launcher_script}"
Path={project_dir}
Icon={icon_path}
Terminal=false
Type=Application
Categories=Utility;
"""

    desktop_dir = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop_dir):
        desktop_dir = os.path.expanduser("~/桌面")

    shortcut_path = os.path.join(desktop_dir, "Arducam_QA_Studio.desktop")

    with open(shortcut_path, "w", encoding="utf-8") as f:
        f.write(desktop_file_content)
    os.chmod(shortcut_path, os.stat(shortcut_path).st_mode | stat.S_IEXEC)

    print("\n======================================================")
    print("✅ 完美！免密码 .exe 体验版快捷方式生成完毕！")
    

if __name__ == "__main__":
    create_exe_like_shortcut()
