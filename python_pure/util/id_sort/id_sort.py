import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QCheckBox, QLineEdit, QMessageBox, QFrame, QHBoxLayout, QScrollArea
)
from PyQt5.QtCore import Qt


class ExcelSplitter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("九联电力ID拆分器V0.2版")
        self.resize(700, 600)
        self.setAcceptDrops(True)  # ✅ 启用拖拽

        self.file_path = None
        self.sheet_name = None
        self.df = None
        self.headers = []
        self.checkboxes = []
        self.chip_checkbox = None
        self.spin_boxes = []
        self.n_parts = 0

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 文件提示
        self.label_file = QLabel("拖动 Excel 文件到此处，或点击按钮选择")
        self.layout.addWidget(self.label_file)

        # 按钮 - 选择文件
        self.btn_file = QPushButton("选择 Excel 文件")
        self.btn_file.clicked.connect(self.load_file_dialog)
        self.layout.addWidget(self.btn_file)

        # sheet 选择
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self.load_headers)
        self.layout.addWidget(QLabel("选择 Sheet:"))
        self.layout.addWidget(self.sheet_combo)

        # 表头选择（可滚动）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.headers_frame = QFrame()
        self.headers_layout = QVBoxLayout()
        self.headers_frame.setLayout(self.headers_layout)
        self.scroll_area.setWidget(self.headers_frame)
        self.layout.addWidget(self.scroll_area)

        # 芯片ID选项
        self.chip_checkbox = QCheckBox("仅保留芯片ID前48个字符")
        self.layout.addWidget(self.chip_checkbox)
        self.chip_checkbox.hide()  # 默认隐藏

        # 拆分设置
        split_frame = QHBoxLayout()
        split_frame.addWidget(QLabel("拆分份数 N:"))
        self.entry_n = QLineEdit()
        self.entry_n.setFixedWidth(60)
        split_frame.addWidget(self.entry_n)
        self.btn_set_n = QPushButton("确认")
        self.btn_set_n.clicked.connect(self.set_n_parts)
        split_frame.addWidget(self.btn_set_n)
        self.layout.addLayout(split_frame)

        self.parts_frame = QVBoxLayout()
        self.layout.addLayout(self.parts_frame)

        # 开始按钮
        self.btn_split = QPushButton("开始拆分")
        self.btn_split.clicked.connect(self.split_excel)
        self.btn_split.setEnabled(False)
        self.layout.addWidget(self.btn_split)

    # 拖拽进入
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # 拖拽释放
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith((".xls", ".xlsx")):
                self.load_file(file_path)

    # 按钮选择文件
    def load_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Excel 文件", "", "Excel Files (*.xls *.xlsx)")
        if file_path:
            self.load_file(file_path)

    # 公共加载文件
    def load_file(self, file_path):
        self.file_path = file_path
        self.label_file.setText(f"已选择文件: {os.path.basename(file_path)}")
        try:
            xls = pd.ExcelFile(self.file_path)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(xls.sheet_names)
            if xls.sheet_names:
                self.sheet_combo.setCurrentIndex(0)
                self.load_headers()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取 Excel 文件: {str(e)}")

    # 加载表头
    def load_headers(self):
        try:
            self.sheet_name = self.sheet_combo.currentText()
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, dtype=str)  # ✅ 全部读为字符串
            self.headers = list(self.df.columns)

            # 清空旧的
            for i in reversed(range(self.headers_layout.count())):
                self.headers_layout.itemAt(i).widget().deleteLater()
            self.checkboxes.clear()

            # 生成复选框
            for col in self.headers:
                chk = QCheckBox(col)
                chk.setChecked(True)
                self.headers_layout.addWidget(chk)
                self.checkboxes.append((col, chk))

            # 芯片ID选项
            if "芯片ID" in self.headers:
                self.chip_checkbox.show()
            else:
                self.chip_checkbox.hide()

            self.btn_split.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取表头: {str(e)}")

    # 设置份数
    def set_n_parts(self):
        try:
            self.n_parts = int(self.entry_n.text())
            # 清空旧控件
            for i in reversed(range(self.parts_frame.count())):
                self.parts_frame.itemAt(i).widget().deleteLater()
            self.spin_boxes.clear()

            for i in range(self.n_parts - 1):  # ✅ 只输入前 N-1 份
                row = QHBoxLayout()
                row.addWidget(QLabel(f"第 {i+1} 份:"))
                entry = QLineEdit()
                entry.setFixedWidth(80)
                row.addWidget(entry)
                self.parts_frame.addLayout(row)
                self.spin_boxes.append(entry)
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效整数")

    # 拆分
    def split_excel(self):
        if not self.df is None and self.n_parts > 0:
            try:
                # 选择列
                selected_cols = [col for col, chk in self.checkboxes if chk.isChecked()]
                df = self.df[selected_cols].copy()

                # 芯片ID处理
                if self.chip_checkbox.isVisible() and self.chip_checkbox.isChecked():
                    df["芯片ID"] = df["芯片ID"].astype(str).str.slice(0, 48)

                # ✅ 所有列转成字符串，避免科学计数法
                df = df.astype(str)

                total_rows = len(df)
                specified_rows = [int(e.text()) for e in self.spin_boxes if e.text().isdigit()]
                last_rows = total_rows - sum(specified_rows)  # ✅ 自动计算最后一份

                if last_rows <= 0:
                    QMessageBox.critical(self, "错误", "行数分配不合理")
                    return

                row_counts = specified_rows + [last_rows]
                base_name, _ = os.path.splitext(os.path.basename(self.file_path))
                output_dir = os.path.dirname(self.file_path)

                start = 0
                for i, rows in enumerate(row_counts, 1):
                    df_part = df.iloc[start:start + rows]
                    start += rows
                    output_file = os.path.join(output_dir, f"{base_name}_split_{i}_{rows}.xlsx")
                    counter = 1
                    while os.path.exists(output_file):
                        output_file = os.path.join(output_dir, f"{base_name}_split_{i}_{rows}_{counter}.xlsx")
                        counter += 1
                    df_part.to_excel(output_file, index=False, engine="openpyxl")

                QMessageBox.information(self, "完成", "Excel 拆分完成！")
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
        else:
            QMessageBox.warning(self, "警告", "请先选择文件并设置拆分份数")


if __name__ == "__main__":
    app = QApplication([])
    win = ExcelSplitter()
    win.show()
    app.exec_()
