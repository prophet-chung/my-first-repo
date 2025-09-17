#!/usr/bin/env python3
# simple_word_viewer.py
# 简单版 Word 文档浏览器（仅浏览，不编辑/复制/搜索）
# 依赖: pip install pyqt5 python-docx

import sys, os
from pathlib import Path
from PyQt5 import QtWidgets
import docx

def read_docx(filepath: str) -> str:
    doc = docx.Document(filepath)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return "\n".join(text)

class SimpleWordViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Word Viewer")
        self.resize(800, 600)

        self.text_area = QtWidgets.QTextEdit()
        self.text_area.setReadOnly(True)
        self.setCentralWidget(self.text_area)

        open_btn = QtWidgets.QPushButton("打开文档")
        open_btn.clicked.connect(self.open_file)
        toolbar = self.addToolBar("Main")
        toolbar.addWidget(open_btn)

    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "打开 Word 文档", str(Path.home()), "Word 文件 (*.docx)"
        )
        if not path:
            return
        try:
            text = read_docx(path)
            self.text_area.setPlainText(text)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", str(e))

def main():
    app = QtWidgets.QApplication(sys.argv)
    viewer = SimpleWordViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
