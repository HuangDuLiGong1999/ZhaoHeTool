# -*- coding: utf-8 -*-
# @Author  : XieSiR
# @Time    : 2025/3/26 18:11
# @Function: 截图工具，注意本人使用mac受rentina屏分辨率影响 坐标需要*2，windows电脑自行调整

import subprocess
import pyautogui
import os
from PIL import ImageGrab
from datetime import datetime
from pynput import keyboard
img = ImageGrab.grab()
print("截图大小:", img.size)
# ========== Step 1: 设置 QuickTime 窗口位置和大小 ==========
print("🛠️ 正在设置 QuickTime Player 窗口为 (0, 0) 大小 960x2088...")

applescript = '''
tell application "System Events"
    tell application process "QuickTime Player"
        set frontmost to true
        set position of window 1 to {0, 0}
        set size of window 1 to {960, 2088}
    end tell
end tell
'''
subprocess.run(['osascript', '-e', applescript])
print("✅ 窗口设置完成。\n")

# ========== Step 2: 模板采集准备 ==========
template_dir = "templates"
os.makedirs(template_dir, exist_ok=True)

coords = []

def save_template():
    scale_factor = 2  # Retina 屏通常是 2x
    x1, y1 = coords[0]
    x2, y2 = coords[1]

    # 校正坐标为真实像素位置
    x1 *= scale_factor
    y1 *= scale_factor
    x2 *= scale_factor
    y2 *= scale_factor

    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(template_dir, f"template_{timestamp}.png")
    img.save(filepath)
    print(f"\n✅ 模板已保存到: {filepath}\n")

def on_press(key):
    global coords
    try:
        if key.char == 's':
            pos = pyautogui.position()
            coords.append(pos)
            print(f"📍 第 {len(coords)} 个点记录：{pos}")

            if len(coords) == 2:
                save_template()
                coords = []  # 重置坐标记录
                print("🎯 继续采集请按 's' 标记下一个区域...\n")

    except AttributeError:
        pass

# ========== Step 3: 开始监听按键 ==========
print("📌 使用说明：")
print("- 将鼠标移动到截图区域的【左上角】，按下 's'")
print("- 再移动到【右下角】，再次按下 's'")
print("- 系统将自动截图并保存模板到 'templates/' 文件夹中")
print("- 可重复操作采集多个模板，按 Ctrl+C 退出\n")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

