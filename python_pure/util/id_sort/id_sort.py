import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QHBoxLayout, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt


class SplitExcelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("九联电力ID拆分工具")
        self.resize(500, 400)
        self.setAcceptDrops(True)  # 开启拖拽支持

        self.layout = QVBoxLayout()

        # 文件状态显示
        self.file_label = QLabel("请拖拽 Excel 文件到窗口中")
        self.file_label.setStyleSheet("color: blue; font-weight: bold;")
        self.layout.addWidget(self.file_label)

        # 输入 N
        self.n_label = QLabel("请输入要拆分的表格数量 N：")
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("例如：3")
        self.layout.addWidget(self.n_label)
        self.layout.addWidget(self.n_input)

        # 确认按钮
        self.btn_next = QPushButton("生成输入框")
        self.btn_next.clicked.connect(self.prepare_inputs)
        self.layout.addWidget(self.btn_next)

        # 行数输入区
        self.inputs_layout = QVBoxLayout()
        self.layout.addLayout(self.inputs_layout)

        # 是否裁剪芯片ID
        self.chk_trim_chipid = QCheckBox("仅保留芯片ID前48个字符")
        self.layout.addWidget(self.chk_trim_chipid)

        # 拆分按钮
        self.btn_split = QPushButton("开始拆分")
        self.btn_split.clicked.connect(self.split_excel)
        self.layout.addWidget(self.btn_split)

        self.setLayout(self.layout)

        # 状态变量
        self.filepath = None
        self.data = None
        self.line_inputs = []
        self.col_chipid = None  # 芯片ID列索引

    # 拖拽进入
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # 拖拽放下
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath.endswith((".xls", ".xlsx")):
                self.load_file(filepath)
            else:
                QMessageBox.warning(self, "错误", "仅支持 Excel 文件（.xls, .xlsx）")

    def load_file(self, filepath):
        try:
            self.filepath = filepath
            self.data = pd.read_excel(filepath, header=None)  # 不自动识别表头

            # 识别芯片ID列
            header_row = self.data.iloc[0].astype(str).tolist()
            self.col_chipid = None
            for idx, name in enumerate(header_row):
                if "芯片ID" in name:
                    self.col_chipid = idx
                    break

            total = len(self.data) - 1
            msg = f"已加载文件：{filepath}\n总数据行数：{total}"
            if self.col_chipid is not None:
                msg += f"\n识别到芯片ID列：第 {self.col_chipid+1} 列"
            else:
                msg += "\n⚠️ 未识别到芯片ID列"
            self.file_label.setText(msg)

        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"无法读取文件：{e}")

    def prepare_inputs(self):
        # 清空旧的输入框
        for i in reversed(range(self.inputs_layout.count())):
            widget = self.inputs_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.line_inputs = []

        try:
            n = int(self.n_input.text())
            if n < 2:
                QMessageBox.warning(self, "错误", "N 必须 >= 2")
                return
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的整数 N")
            return

        # 创建 N-1 个输入框
        for i in range(n - 1):
            row = QHBoxLayout()
            label = QLabel(f"子表格 {i+1} 行数：")
            line_edit = QLineEdit()
            row.addWidget(label)
            row.addWidget(line_edit)
            self.inputs_layout.addLayout(row)
            self.line_inputs.append(line_edit)

    def split_excel(self):
        if not self.filepath or self.data is None:
            QMessageBox.warning(self, "错误", "请先拖拽 Excel 文件！")
            return

        try:
            n = int(self.n_input.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的 N")
            return

        total_rows = len(self.data) - 1  # 数据行数（去掉表头）
        sizes = []

        # 读取前 N-1 个输入框
        for i, line_edit in enumerate(self.line_inputs):
            try:
                val = int(line_edit.text())
                if val <= 0:
                    raise ValueError
                sizes.append(val)
            except ValueError:
                QMessageBox.warning(self, "错误", f"子表格 {i+1} 行数输入无效")
                return

        sum_sizes = sum(sizes)
        last_size = total_rows - sum_sizes
        if last_size <= 0:
            QMessageBox.warning(self, "错误", f"行数分配错误，总行数为 {total_rows}")
            return
        sizes.append(last_size)

        # 拆分数据
        header = self.data.iloc[[0]]
        df_data = self.data.iloc[1:].copy()

        # 如果勾选了裁剪芯片ID，并且识别到了芯片ID列
        if self.chk_trim_chipid.isChecked():
            if self.col_chipid is not None:
                try:
                    df_data.iloc[:, self.col_chipid] = (
                        df_data.iloc[:, self.col_chipid].astype(str).str.slice(0, 48)
                    )
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"裁剪芯片ID时出错：{e}")
            else:
                QMessageBox.warning(self, "警告", "未识别到芯片ID列，无法裁剪")

        start = 0
        for i, size in enumerate(sizes):
            part = df_data.iloc[start:start+size]
            part_df = pd.concat([header, part])
            save_path = self.filepath.replace(".xlsx", f"_part{i+1}.xlsx").replace(".xls", f"_part{i+1}.xlsx")
            part_df.to_excel(save_path, index=False, header=False)
            start += size

        QMessageBox.information(self, "完成", f"成功拆分为 {n} 个文件！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SplitExcelApp()
    window.show()
    sys.exit(app.exec_())
