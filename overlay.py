# -*- coding: utf-8 -*-
# @Author  : XieSiR
# @Time    : 2025/3/27 14:31
# @Function:
# overlay.py
from PyQt5 import QtWidgets, QtGui, QtCore
import sys

class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, rects, timeout=2000):
        super().__init__()
        self.rects = rects
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0,
                         QtWidgets.QApplication.primaryScreen().size().width(),
                         QtWidgets.QApplication.primaryScreen().size().height())

        # 在 timeout 后退出整个 app，而不是仅仅关闭窗口
        QtCore.QTimer.singleShot(timeout, QtWidgets.QApplication.quit)

        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(QtCore.Qt.red, 5)
        painter.setPen(pen)
        for x, y, w, h in self.rects:
            painter.drawRect(x, y, w, h)

def show_overlay(rects):
    app = QtWidgets.QApplication(sys.argv)
    win = OverlayWindow(rects)
    sys.exit(app.exec_())

if __name__ == "__main__":
    import ast

    # PyInstaller / 调用时会传字符串形式的 list
    rects = ast.literal_eval(sys.argv[1])

    app = QtWidgets.QApplication(sys.argv)
    win = OverlayWindow(rects)

    # 连接窗口关闭事件，自动退出应用（防僵尸）
    win.destroyed.connect(app.quit)

    app.exec_()
