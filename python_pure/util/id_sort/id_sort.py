import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QHBoxLayout, QMessageBox, QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt


class SplitExcelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel 拆分工具（拖拽 + 自动识别芯片ID + 序号_大小命名）")
        self.resize(540, 420)
        self.setAcceptDrops(True)

        self.layout = QVBoxLayout()

        # 文件状态显示
        self.file_label = QLabel("请拖拽 Excel 文件到窗口中（支持 .xls/.xlsx）\n输出文件统一为 .xlsx 格式")
        self.file_label.setStyleSheet("color: blue; font-weight: bold;")
        self.layout.addWidget(self.file_label)

        # 输入 N
        self.n_label = QLabel("请输入要拆分的表格数量 N：")
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("例如：2 或 3")
        self.layout.addWidget(self.n_label)
        self.layout.addWidget(self.n_input)

        # 生成输入框按钮
        self.btn_next = QPushButton("生成行数输入框")
        self.btn_next.clicked.connect(self.prepare_inputs)
        self.layout.addWidget(self.btn_next)

        # 行数输入区（动态）
        self.inputs_layout = QVBoxLayout()
        self.layout.addLayout(self.inputs_layout)

        # 👉 占位符：芯片ID复选框稍后动态创建
        self.chk_trim_chipid = None

        # 拆分按钮
        self.btn_split = QPushButton("开始拆分")
        self.btn_split.clicked.connect(self.split_excel)
        self.layout.addWidget(self.btn_split)

        self.setLayout(self.layout)

        # 状态
        self.filepath = None
        self.data = None
        self.line_inputs = []
        self.col_chipid = None  # 识别到的芯片ID列索引

    # 拖拽进入
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # 拖拽放下
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        filepath = urls[0].toLocalFile()
        if filepath.lower().endswith((".xls", ".xlsx")):
            self.load_file(filepath)
        else:
            QMessageBox.warning(self, "错误", "仅支持 Excel 文件（.xls, .xlsx）")

    def load_file(self, filepath):
        try:
            self.filepath = filepath
            self.data = pd.read_excel(filepath, header=None)

            # 识别芯片ID列
            header_row = self.data.iloc[0].astype(str).tolist()
            self.col_chipid = None
            for idx, name in enumerate(header_row):
                if "芯片ID" in name:
                    self.col_chipid = idx
                    break

            total = max(len(self.data) - 1, 0)
            msg = f"已加载：{filepath}\n总数据行（不含表头）：{total}"

            # 👉 如果有芯片ID，就显示复选框；没有就移除
            if self.col_chipid is not None:
                msg += f"\n识别到芯片ID列：第 {self.col_chipid + 1} 列"
                if not self.chk_trim_chipid:
                    self.chk_trim_chipid = QCheckBox("仅保留芯片ID前48个字符（勾选则裁剪）")
                    self.layout.insertWidget(self.layout.count() - 1, self.chk_trim_chipid)
            else:
                msg += "\n⚠️ 未识别到‘芯片ID’列"
                if self.chk_trim_chipid:
                    self.layout.removeWidget(self.chk_trim_chipid)
                    self.chk_trim_chipid.deleteLater()
                    self.chk_trim_chipid = None

            self.file_label.setText(msg)

        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"无法读取文件：{e}")

    def prepare_inputs(self):
        while self.inputs_layout.count():
            item = self.inputs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.line_inputs = []

        try:
            n = int(self.n_input.text())
            if n < 2:
                QMessageBox.warning(self, "错误", "N 必须 >= 2")
                return
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的整数 N")
            return

        for i in range(n - 1):
            row = QHBoxLayout()
            label = QLabel(f"子表格 {i + 1} 行数：")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("输入正整数（例如：5000）")
            row.addWidget(label)
            row.addWidget(line_edit)
            self.inputs_layout.addLayout(row)
            self.line_inputs.append(line_edit)

    def split_excel(self):
        if not self.filepath or self.data is None:
            QMessageBox.warning(self, "错误", "请先拖拽并加载 Excel 文件！")
            return

        try:
            n = int(self.n_input.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的 N")
            return

        total_rows = len(self.data) - 1
        if total_rows <= 0:
            QMessageBox.warning(self, "错误", "文件中没有有效数据行")
            return

        sizes = []
        for i, line_edit in enumerate(self.line_inputs):
            try:
                val = int(line_edit.text())
                if val <= 0:
                    raise ValueError
                sizes.append(val)
            except Exception:
                QMessageBox.warning(self, "错误", f"子表格 {i+1} 行数输入无效")
                return

        sum_sizes = sum(sizes)
        last_size = total_rows - sum_sizes
        if last_size <= 0:
            QMessageBox.warning(self, "错误", f"行数分配错误：总数据行数为 {total_rows}，已分配 {sum_sizes}")
            return
        sizes.append(last_size)

        header = self.data.iloc[[0]]
        df_data = self.data.iloc[1:].copy()

        # 👉 仅当复选框存在且勾选时，才裁剪
        if self.chk_trim_chipid and self.chk_trim_chipid.isChecked():
            try:
                df_data.iloc[:, self.col_chipid] = df_data.iloc[:, self.col_chipid].astype(str).str.slice(0, 48)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"裁剪芯片ID时出错：{e}")

        saved_files = []
        start = 0
        base_no_ext = os.path.splitext(self.filepath)[0]

        for i, size in enumerate(sizes, start=1):
            part = df_data.iloc[start:start + size]
            part_df = pd.concat([header, part])
            save_path = f"{base_no_ext}_split_{i}_{size}.xlsx"

            if os.path.exists(save_path):
                k = 1
                while True:
                    alt = f"{base_no_ext}_split_{i}_{size}_dup{k}.xlsx"
                    if not os.path.exists(alt):
                        save_path = alt
                        break
                    k += 1

            part_df.to_excel(save_path, index=False, header=False)
            saved_files.append(save_path)
            start += size

        msg = "拆分完成，生成文件：\n" + "\n".join(saved_files)
        QMessageBox.information(self, "完成", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SplitExcelApp()
    window.show()
    sys.exit(app.exec_())
