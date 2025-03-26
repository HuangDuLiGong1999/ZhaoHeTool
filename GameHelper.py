# -*- coding: utf-8 -*-
# @Author  : XieSiR
# @Time    : 2025/3/26 18:12
# @Function: 魔王辅助，在命令行输出建议交换位置。目前策略是贪心，感兴趣去Match3Game里改find_best_swap函数
import subprocess
import time
import os
from PIL import ImageGrab
import cv2
import numpy as np
from Match3Game import Cell, GameBoard

# ========== Step 1: 设置 QuickTime Player 窗口 ==========
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

# ========== Step 2: 参数配置 ==========
# 沙盘区域位置（你可以替换成实际值）
sandbox_top_left = (586, 112)
sandbox_bottom_right = (1330, 850)

# 棋盘尺寸
rows, cols = 6, 6

# 模板目录
template_dir = "templates"

# ========== Step 3: 加载模板 ==========
def load_templates():
    templates = []
    for filename in os.listdir(template_dir):
        if filename.endswith(".png"):
            path = os.path.join(template_dir, filename)
            img = cv2.imread(path)
            if img is None:
                continue
            # 假设命名是 A1.png, B3.png 等
            name = os.path.splitext(filename)[0]
            family = name[0]
            level = int(name[1])
            templates.append((family, level, img))
    return templates

templates = load_templates()
print(f"✅ 已加载 {len(templates)} 个模板")

# ========== Step 4: 分割截图为格子 ==========
def crop_cells(image, rows, cols):
    h, w = image.shape[:2]
    cell_h = h // rows
    cell_w = w // cols
    cells = []
    for r in range(rows):
        row = []
        for c in range(cols):
            y1 = r * cell_h
            x1 = c * cell_w
            cell_img = image[y1:y1+cell_h, x1:x1+cell_w]
            row.append(cell_img)
        cells.append(row)
    return cells

# ========== Step 5: 匹配识别单元格 ==========
def recognize_cell(cell_img, templates, threshold=0.8):
    best_score = 0
    best_match = None
    for family, level, tpl in templates:
        tpl_h, tpl_w = tpl.shape[:2]
        if cell_img.shape[0] < tpl_h or cell_img.shape[1] < tpl_w:
            print(family, level, tpl)
            continue  # 跳过尺寸不匹配
        res = cv2.matchTemplate(cell_img, tpl, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val > best_score:
            best_score = max_val
            best_match = (family, level)
    if best_score >= threshold:
        return Cell(family=best_match[0], level=best_match[1])
    else:
        return Cell(family="?", level=0)

# ========== Step 6: 主循环 ==========
print("🔍 开始识别沙盘状态，每隔 8 秒刷新一次...（Ctrl+C 退出）")

try:
    while True:
        time.sleep(3)
        x1, y1 = sandbox_top_left
        x2, y2 = sandbox_bottom_right
        img_pil = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        # 分割格子
        grid_imgs = crop_cells(img_cv, rows, cols)

        # 识别每个格子
        result = []
        for row in grid_imgs:
            result_row = [recognize_cell(cell, templates) for cell in row]
            result.append(result_row)

        # 打印结果
        print("🎯 当前沙盘识别结果：")
        for row in result:
            print(" ".join(str(cell) for cell in row))

        # 构建 GameBoard 并调用推荐逻辑
        board = GameBoard(result)
        swap, combos = board.find_best_swap()

        if swap:
            print(f"💡 推荐交换: {swap}（x行x列，从上到下从左到右）\n可触发合成数: {combos}")
        else:
            print("⚠️ 当前无有效合成交换")
        print("\n---\n")

except KeyboardInterrupt:
    print("🛑 已手动终止识别程序。")