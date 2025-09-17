#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binary Viewer - 通用二进制文件浏览器
Features:
- 打开任意二进制文件 (不限后缀)
- 以 hex + ASCII 并排格式显示
- 可调整每行显示的字节数 (bytes per line)
- 查找（支持输入 hex bytes like "DE AD BE EF" 或文本 like "hello"）
- 跳转到偏移 (goto offset)
- 在状态栏显示当前光标所在字节的文件偏移
- 另存为 (保存当前文件的副本)
"""
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import os
import re

HEX_PREFIX_WIDTH = 10  # e.g. "00000000: "

class BinaryViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binary Viewer")
        self.resize(1000, 700)

        self.bytes_per_line = 16
        self.data = bytearray()
        self.current_path = None

        # --- widgets
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        font = QtGui.QFont("Courier New")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(10)
        self.text.setFont(font)
        self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text.cursorPositionChanged.connect(self.on_cursor_moved)

        self.setCentralWidget(self.text)

        # toolbar
        tb = self.addToolBar("Main")
        tb.setMovable(False)

        open_action = QtWidgets.QAction("打开", self)
        open_action.triggered.connect(self.open_file)
        tb.addAction(open_action)

        saveas_action = QtWidgets.QAction("另存为", self)
        saveas_action.triggered.connect(self.save_as)
        tb.addAction(saveas_action)

        tb.addSeparator()
        tb.addWidget(QtWidgets.QLabel("每行字节:"))
        self.spin_bpl = QtWidgets.QSpinBox()
        self.spin_bpl.setRange(4, 32)
        self.spin_bpl.setValue(self.bytes_per_line)
        self.spin_bpl.valueChanged.connect(self.on_bpl_changed)
        tb.addWidget(self.spin_bpl)

        tb.addSeparator()
        tb.addWidget(QtWidgets.QLabel("查找:"))
        self.find_edit = QtWidgets.QLineEdit()
        self.find_edit.setPlaceholderText("输入 hex (eg: DE AD BE EF) 或文本 (eg: hello)")
        self.find_edit.returnPressed.connect(self.on_find)
        tb.addWidget(self.find_edit)
        find_btn = QtWidgets.QPushButton("查找")
        find_btn.clicked.connect(self.on_find)
        tb.addWidget(find_btn)

        goto_btn = QtWidgets.QPushButton("跳转(offset)")
        goto_btn.clicked.connect(self.on_goto)
        tb.addWidget(goto_btn)

        tb.addSeparator()
        tb.addWidget(QtWidgets.QLabel("文件:"))
        self.path_label = QtWidgets.QLabel("(未打开)")
        tb.addWidget(self.path_label)

        # status bar
        self.status = self.statusBar()
        self.offset_label = QtWidgets.QLabel("Offset: -")
        self.status.addPermanentWidget(self.offset_label)
        self.size_label = QtWidgets.QLabel("Size: 0")
        self.status.addPermanentWidget(self.size_label)

        # find results area
        self.find_results = []

    # ---------- core ----------
    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "打开二进制文件", os.getcwd(), "All Files (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                self.data = bytearray(f.read())
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"无法打开文件:\n{e}")
            return
        self.current_path = path
        self.path_label.setText(path)
        self.update_title()
        self.refresh_view()

    def save_as(self):
        if not self.data:
            QtWidgets.QMessageBox.information(self, "提示", "当前没有打开文件")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "另存为", os.path.basename(self.current_path or "untitled.bin")
        )
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(self.data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"保存失败:\n{e}")
            return
        QtWidgets.QMessageBox.information(self, "完成", f"已保存为: {path}")

    def on_bpl_changed(self, v):
        self.bytes_per_line = v
        self.refresh_view()

    def update_title(self):
        name = self.current_path or "(unnamed)"
        self.setWindowTitle(f"Binary Viewer - {os.path.basename(name)}")

    def refresh_view(self):
        """把 self.data 按当前 bytes_per_line 渲染到 self.text"""
        bpl = self.bytes_per_line
        lines = []
        size = len(self.data)
        for base in range(0, size, bpl):
            chunk = self.data[base: base + bpl]
            hex_bytes = ' '.join(f"{b:02X}" for b in chunk)
            pad_len = (bpl - len(chunk)) * 3
            hex_padded = hex_bytes + ' ' * pad_len
            ascii_repr = ''.join((chr(b) if 32 <= b <= 126 else '.') for b in chunk)
            lines.append(f"{base:08X}: {hex_padded}  {ascii_repr}")
        text = '\n'.join(lines) if lines else ''
        self.text.setPlainText(text)
        self.size_label.setText(f"Size: {len(self.data)} bytes")
        self.offset_label.setText("Offset: -")
        self.find_results = []

    # ---------- cursor/offset mapping ----------
    def on_cursor_moved(self):
        cursor = self.text.textCursor()
        block = cursor.block()
        line_no = block.blockNumber()
        col = cursor.positionInBlock()
        bpl = self.bytes_per_line
        hex_start = HEX_PREFIX_WIDTH
        hex_area_len = bpl * 3
        ascii_start = hex_start + hex_area_len + 2
        offset = None
        if hex_start <= col < (hex_start + hex_area_len):
            idx_in_hex = col - hex_start
            byte_index = idx_in_hex // 3
            offset = line_no * bpl + byte_index
        elif col >= ascii_start:
            idx_in_ascii = col - ascii_start
            byte_index = idx_in_ascii
            offset = line_no * bpl + byte_index
        else:
            offset = None
        if offset is None or offset >= len(self.data):
            self.offset_label.setText("Offset: -")
        else:
            self.offset_label.setText(f"Offset: {offset} (0x{offset:08X})")

    # ---------- find ----------
    def parse_find_query(self, s: str):
        s = s.strip()
        if not s:
            return None, None
        if re.fullmatch(r"[0-9A-Fa-f\s]+", s) and re.search(r"[0-9A-Fa-f]", s):
            raw = re.sub(r"\s+", "", s)
            if len(raw) % 2 != 0:
                return None, None
            try:
                b = bytes.fromhex(raw)
                return "hex", b
            except Exception:
                return None, None
        else:
            return "text", s.encode('utf-8', errors='ignore')

    def on_find(self):
        q = self.find_edit.text()
        mode, patt = self.parse_find_query(q)
        if mode is None:
            QtWidgets.QMessageBox.warning(self, "查找", "查找字符串无法识别为 hex 或 文本")
            return
        self.find_results = []
        start = 0
        while True:
            idx = self.data.find(patt, start)
            if idx == -1:
                break
            self.find_results.append(idx)
            start = idx + 1
        if not self.find_results:
            QtWidgets.QMessageBox.information(self, "查找", "未找到匹配项")
            return
        self.goto_and_highlight(self.find_results[0])

    def goto_and_highlight(self, offset: int):
        bpl = self.bytes_per_line
        line = offset // bpl
        doc = self.text.document()
        block = doc.findBlockByNumber(line)
        if not block.isValid():
            return
        cursor = QtGui.QTextCursor(block)
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        self.text.setTextCursor(cursor)
        self.text.centerCursor()

    # ---------- goto ----------
    def on_goto(self):
        if not self.data:
            QtWidgets.QMessageBox.information(self, "提示", "请先打开一个文件")
            return
        text, ok = QtWidgets.QInputDialog.getText(self, "跳转到偏移", "输入偏移 (十进制或 0x 十六进制):")
        if not ok or not text:
            return
        text = text.strip()
        try:
            if text.lower().startswith("0x"):
                val = int(text, 16)
            else:
                val = int(text, 10)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "错误", "无法解析偏移值")
            return
        if val < 0 or val >= len(self.data):
            QtWidgets.QMessageBox.warning(self, "错误", "偏移超出范围")
            return
        self.goto_and_highlight(val)

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = BinaryViewer()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
