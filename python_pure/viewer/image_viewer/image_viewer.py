#!/usr/bin/env python3
"""
简单的 PyQt5 图片浏览器（单文件）
在 Windows x64 上用 Python 运行：
  pip install pyqt5
然后运行：
  python simple_pyqt_image_viewer.py

功能：打开单张图片或文件夹，上一张/下一张，放大/缩小/适应窗口，使用键盘左右键切换。
默认状态：适应窗口，窗口大小改变时自动重新适应。
"""
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QScrollArea, QFileDialog,
    QAction, QToolBar, QMessageBox
)
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtCore import Qt


IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('简单图片浏览器')
        self.resize(900, 600)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setBackgroundRole(QLabel().backgroundRole())
        self.image_label.setScaledContents(False)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.setCentralWidget(self.scroll_area)

        self.toolbar = QToolBar('工具')
        self.addToolBar(self.toolbar)

        open_file_act = QAction('打开文件', self)
        open_file_act.setShortcut(QKeySequence.Open)
        open_file_act.triggered.connect(self.open_file)

        open_folder_act = QAction('打开文件夹', self)
        open_folder_act.triggered.connect(self.open_folder)

        prev_act = QAction('上一张', self)
        prev_act.setShortcut('Left')
        prev_act.triggered.connect(self.prev_image)

        next_act = QAction('下一张', self)
        next_act.setShortcut('Right')
        next_act.triggered.connect(self.next_image)

        fit_act = QAction('适应窗口', self)
        fit_act.triggered.connect(self.fit_to_window)

        normal_act = QAction('实际大小', self)
        normal_act.triggered.connect(self.normal_size)

        zoom_in_act = QAction('放大', self)
        zoom_in_act.setShortcut('+')
        zoom_in_act.triggered.connect(lambda: self.zoom(1.25))

        zoom_out_act = QAction('缩小', self)
        zoom_out_act.setShortcut('-')
        zoom_out_act.triggered.connect(lambda: self.zoom(0.8))

        for act in (open_file_act, open_folder_act, prev_act, next_act,
                    fit_act, normal_act, zoom_in_act, zoom_out_act):
            self.toolbar.addAction(act)

        self.statusBar().showMessage('就绪')

        # data
        self.image_list = []
        self.current_index = -1
        self.scale_factor = 1.0
        self.fit_mode = True  # 是否处于适应窗口模式
        self.original_pixmap = None  # 保存原始图像

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, '打开图片', os.path.expanduser('~'))
        if path:
            folder = os.path.dirname(path)
            self.load_folder_or_file(folder, focus=path)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择图片文件夹', os.path.expanduser('~'))
        if folder:
            self.load_folder_or_file(folder)

    def load_folder_or_file(self, folder, focus=None):
        try:
            files = sorted(os.listdir(folder))
        except Exception as e:
            QMessageBox.warning(self, '错误', f'无法打开文件夹: {e}')
            return
        images = [os.path.join(folder, f) for f in files if f.lower().endswith(IMAGE_EXTS)]
        if not images:
            QMessageBox.information(self, '提示', '文件夹中没有支持的图片格式')
            return
        self.image_list = images
        if focus and focus in images:
            self.current_index = images.index(focus)
        else:
            self.current_index = 0
        self.show_image()

    def show_image(self):
        if not (0 <= self.current_index < len(self.image_list)):
            return
        path = self.image_list[self.current_index]
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, '错误', f'无法加载图片: {path}')
            return
        # 保存原始图像
        self.original_pixmap = pix
        if self.fit_mode:
            self.fit_to_window()
        else:
            self.adjust_image_to_label()
        self.statusBar().showMessage(f"{os.path.basename(path)}  ({self.current_index+1}/{len(self.image_list)})")

    def adjust_image_to_label(self):
        if self.original_pixmap is None:
            return
        new_size = self.original_pixmap.size() * self.scale_factor
        scaled = self.original_pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())

    def next_image(self):
        if not self.image_list:
            return
        self.current_index = (self.current_index + 1) % len(self.image_list)
        self.show_image()

    def prev_image(self):
        if not self.image_list:
            return
        self.current_index = (self.current_index - 1) % len(self.image_list)
        self.show_image()

    def fit_to_window(self):
        if self.original_pixmap is None:
            return
        area_size = self.scroll_area.viewport().size()
        w_ratio = area_size.width() / self.original_pixmap.width()
        h_ratio = area_size.height() / self.original_pixmap.height()
        self.scale_factor = min(w_ratio, h_ratio, 1.0)
        self.fit_mode = True
        self.adjust_image_to_label()

    def normal_size(self):
        if self.original_pixmap is None:
            return
        self.scale_factor = 1.0
        self.fit_mode = False
        self.adjust_image_to_label()

    def zoom(self, factor):
        if self.original_pixmap is None:
            return
        self.scale_factor *= factor
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
        self.fit_mode = False
        self.adjust_image_to_label()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key_Left:
            self.prev_image()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom(1.25)
        elif event.key() in (Qt.Key_Minus,):
            self.zoom(0.8)
        elif event.key() == Qt.Key_F:
            self.fit_to_window()
        elif event.key() == Qt.Key_0:
            self.normal_size()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_mode and self.original_pixmap is not None:
            self.fit_to_window()


def main():
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
