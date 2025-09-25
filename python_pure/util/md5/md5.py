import sys
import os
import hashlib
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


def calculate_md5(file_path):
    """计算文件的MD5"""
    md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception:
        return None


def get_files_md5(directory):
    """遍历目录，返回 {相对路径: md5}"""
    result = {}
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            md5 = calculate_md5(path)
            if md5:
                relative_path = os.path.relpath(path, directory)
                result[relative_path] = md5
    return result


def save_md5_to_txt(directory, files_dict):
    """保存MD5到目录下的 txt 文件"""
    if not directory or not files_dict:
        return None
    output_path = os.path.join(directory, "md5_list.txt")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("相对路径\tMD5\n")
            for file, md5 in sorted(files_dict.items()):
                f.write(f"{file}\t{md5}\n")
        return output_path
    except Exception:
        return None


class MD5Comparator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("九联电力文件MD5比较器")
        self.resize(1000, 600)

        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        # 左侧按钮
        self.left_btn = QPushButton("选择左侧目录")
        self.left_btn.clicked.connect(self.load_left_directory)
        self.left_export_btn = QPushButton("导出左侧结果")
        self.left_export_btn.clicked.connect(self.export_left)

        # 右侧按钮
        self.right_btn = QPushButton("选择右侧目录")
        self.right_btn.clicked.connect(self.load_right_directory)
        self.right_export_btn = QPushButton("导出右侧结果")
        self.right_export_btn.clicked.connect(self.export_right)

        btn_layout.addWidget(self.left_btn)
        btn_layout.addWidget(self.left_export_btn)
        btn_layout.addWidget(self.right_btn)
        btn_layout.addWidget(self.right_export_btn)

        # 表格
        tables_layout = QHBoxLayout()
        self.left_table = QTableWidget()
        self.left_table.setColumnCount(2)
        self.left_table.setHorizontalHeaderLabels(["文件（相对路径）", "MD5"])

        self.right_table = QTableWidget()
        self.right_table.setColumnCount(2)
        self.right_table.setHorizontalHeaderLabels(["文件（相对路径）", "MD5"])

        tables_layout.addWidget(self.left_table)
        tables_layout.addWidget(self.right_table)

        layout.addLayout(btn_layout)
        layout.addLayout(tables_layout)
        self.setLayout(layout)

        # 数据
        self.left_files = {}
        self.right_files = {}
        self.left_dir = ""
        self.right_dir = ""

    def load_left_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择左侧目录")
        if directory:
            self.left_dir = directory
            self.left_files = get_files_md5(directory)
            self.show_files(self.left_table, self.left_files)
            self.compare_results()

    def load_right_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择右侧目录")
        if directory:
            self.right_dir = directory
            self.right_files = get_files_md5(directory)
            self.show_files(self.right_table, self.right_files)
            self.compare_results()

    def export_left(self):
        if not self.left_dir or not self.left_files:
            QMessageBox.information(self, "导出", "请先选择左侧目录并生成 MD5 列表。")
            return
        path = save_md5_to_txt(self.left_dir, self.left_files)
        if path:
            QMessageBox.information(self, "导出成功", f"左侧结果已导出到：\n{path}")

    def export_right(self):
        if not self.right_dir or not self.right_files:
            QMessageBox.information(self, "导出", "请先选择右侧目录并生成 MD5 列表。")
            return
        path = save_md5_to_txt(self.right_dir, self.right_files)
        if path:
            QMessageBox.information(self, "导出成功", f"右侧结果已导出到：\n{path}")

    def show_files(self, table, files_dict):
        table.setRowCount(0)
        for i, (relpath, md5) in enumerate(sorted(files_dict.items())):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(relpath))
            table.setItem(i, 1, QTableWidgetItem(md5))

    def compare_results(self):
        if not self.left_files or not self.right_files:
            return

        # 获取两边的 MD5 集合
        left_md5_set = set(self.left_files.values())
        right_md5_set = set(self.right_files.values())

        # 左表
        for i in range(self.left_table.rowCount()):
            md5 = self.left_table.item(i, 1).text()
            color = QColor(Qt.GlobalColor.green) if md5 in right_md5_set else QColor(Qt.GlobalColor.red)
            self.left_table.item(i, 0).setBackground(color)
            self.left_table.item(i, 1).setBackground(color)

        # 右表
        for i in range(self.right_table.rowCount()):
            md5 = self.right_table.item(i, 1).text()
            color = QColor(Qt.GlobalColor.green) if md5 in left_md5_set else QColor(Qt.GlobalColor.red)
            self.right_table.item(i, 0).setBackground(color)
            self.right_table.item(i, 1).setBackground(color)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MD5Comparator()
    window.show()
    sys.exit(app.exec())
