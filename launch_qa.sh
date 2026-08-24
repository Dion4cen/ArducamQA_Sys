#!/bin/bash
cd "/home/pi/ArducamQA_Sys"

# 1. 强制使用 X11 渲染，解决 Wayland 环境的警告
export QT_QPA_PLATFORM=xcb

# 2. 静默授权画图权限
xhost +local: > /dev/null 2>&1

# 3. 将 GUI 程序彻底扔进系统后台静默运行，丢弃所有无用日志
nohup sudo -E XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" WAYLAND_DISPLAY="$WAYLAND_DISPLAY" DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" python3 "/home/pi/ArducamQA_Sys/run_qa.py" > /dev/null 2>&1 &
