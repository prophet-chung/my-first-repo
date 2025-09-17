import sys
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QToolBar, QLineEdit, QLabel, QScrollArea
)
from PyQt6.QtGui import QAction, QPixmap, QImage
from PyQt6.QtCore import Qt


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 浏览器 - 稳定版 (带缩放)")

        self.doc = None
        self.current_page = 0
        self.scale_mode = "actual"  # actual / fit_width / fit_page
        self.zoom_factor = 2.0  # 默认放大 2 倍渲染

        # 显示区域
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.image_label)
        self.setCentralWidget(self.scroll)

        # 工具栏
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)

        open_action = QAction("打开 PDF", self)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        prev_action = QAction("上一页", self)
        prev_action.triggered.connect(self.prev_page)
        toolbar.addAction(prev_action)

        next_action = QAction("下一页", self)
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        self.page_input = QLineEdit(self)
        self.page_input.setFixedWidth(60)
        self.page_input.returnPressed.connect(self.go_to_page)
        toolbar.addWidget(QLabel("跳转页:"))
        toolbar.addWidget(self.page_input)

        # 缩放模式
        fit_width_action = QAction("适应宽度", self)
        fit_width_action.triggered.connect(lambda: self.set_scale_mode("fit_width"))
        toolbar.addAction(fit_width_action)

        fit_page_action = QAction("适应整页", self)
        fit_page_action.triggered.connect(lambda: self.set_scale_mode("fit_page"))
        toolbar.addAction(fit_page_action)

        actual_action = QAction("实际大小", self)
        actual_action.triggered.connect(lambda: self.set_scale_mode("actual"))
        toolbar.addAction(actual_action)

    # ========= 功能 =========

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开 PDF 文件", "", "PDF Files (*.pdf)")
        if file_path:
            self.doc = fitz.open(file_path)
            self.current_page = 0
            self.show_page()

    def set_scale_mode(self, mode):
        self.scale_mode = mode
        self.show_page()

    def show_page(self):
        if not self.doc:
            return
        page = self.doc.load_page(self.current_page)

        # 获取窗口大小
        view_w = self.scroll.viewport().width()
        view_h = self.scroll.viewport().height()
        page_w, page_h = page.rect.width, page.rect.height

        # 计算缩放比例
        if self.scale_mode == "fit_width":
            scale = view_w / page_w
        elif self.scale_mode == "fit_page":
            scale = min(view_w / page_w, view_h / page_h)
        else:  # actual
            scale = self.zoom_factor

        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)

        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(image))

        self.page_input.setText(str(self.current_page + 1))
        self.setWindowTitle(f"PDF 浏览器 - 第 {self.current_page+1}/{self.doc.page_count} 页")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page()

    def next_page(self):
        if self.doc and self.current_page < self.doc.page_count - 1:
            self.current_page += 1
            self.show_page()

    def go_to_page(self):
        if not self.doc:
            return
        try:
            page = int(self.page_input.text()) - 1
        except ValueError:
            return
        if 0 <= page < self.doc.page_count:
            self.current_page = page
            self.show_page()


def main():
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.resize(1200, 900)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
