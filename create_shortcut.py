import os
import stat

def create_desktop_shortcut():
    # 1. 自动获取当前项目的绝对路径 (ArducamQA_Sys 文件夹)
    project_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 🎯 已经为你修改为你的总枢纽文件：run_qa.py
    main_script = os.path.join(project_dir, "run_qa.py") 
    
    if not os.path.exists(main_script):
        print(f"❌ 错误：找不到 {main_script}！请确保本脚本放在 ArducamQA_Sys 根目录下。")
        return

    # 2. 寻找图标 (如果有 logo.png 就用它，没有就用系统自带的相机图标)
    icon_path = os.path.join(project_dir, "logo.png")
    if not os.path.exists(icon_path):
        icon_path = "camera-photo"

    # 3. 编写快捷方式配置 
    
    desktop_file_content = f"""[Desktop Entry]
Name=Arducam QA Studio
Comment=Arducam 产线自动测试工具
Exec=sudo -E python3 {main_script}
Icon={icon_path}
Terminal=false
Type=Application
Categories=Utility;HardwareSettings;
"""

    # 4. 定位到当前用户的桌面目录
    desktop_dir = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop_dir):
        # 兼容中文系统的桌面路径
        desktop_dir = os.path.expanduser("~/桌面")
        if not os.path.exists(desktop_dir):
            os.makedirs(os.path.expanduser("~/Desktop"))
            desktop_dir = os.path.expanduser("~/Desktop")

    shortcut_path = os.path.join(desktop_dir, "Arducam_QA_Studio.desktop")

    # 5. 写入文件
    with open(shortcut_path, "w", encoding="utf-8") as f:
        f.write(desktop_file_content)

    # 6. 赋予可执行权限（Linux 桌面快捷方式必须要有运行权限）
    st = os.stat(shortcut_path)
    os.chmod(shortcut_path, st.st_mode | stat.S_IEXEC)

    print("========================================")
    print("✅ 成功！快捷方式已生成在桌面。")
    print(f"📍 快捷方式路径: {shortcut_path}")
    print("🧑‍🏭 产线人员现在可以直接在桌面双击【Arducam QA Studio】图标打开软件了！")
    print("========================================")

if __name__ == "__main__":
    create_desktop_shortcut()