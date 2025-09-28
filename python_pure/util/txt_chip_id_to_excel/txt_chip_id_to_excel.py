import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt


class TxtToExcel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("九联电力芯片ID转换工具")
        self.resize(400, 200)
        self.setAcceptDrops(True)  # ✅ 支持拖拽

        self.file_path = None

        layout = QVBoxLayout()

        self.label = QLabel("拖拽 TXT 文件到这里，或点击按钮选择")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.btn_select = QPushButton("选择 TXT 文件")
        self.btn_select.clicked.connect(self.load_file_dialog)
        layout.addWidget(self.btn_select)

        self.chk_limit = QCheckBox("仅保留芯片ID前48个字符")
        layout.addWidget(self.chk_limit)

        self.btn_export = QPushButton("导出 Excel")
        self.btn_export.clicked.connect(self.export_excel)
        self.btn_export.setEnabled(False)
        layout.addWidget(self.btn_export)

        self.setLayout(layout)

    # 拖拽进入
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # 拖拽释放
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(".txt"):
                self.load_file(file_path)

    def load_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 TXT 文件", "", "Text Files (*.txt)")
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        self.file_path = file_path
        self.label.setText(f"已选择文件: {os.path.basename(file_path)}")
        self.btn_export.setEnabled(True)

    def export_excel(self):
        if not self.file_path:
            QMessageBox.warning(self, "错误", "请先选择 TXT 文件")
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                chip_ids = [line.strip() for line in f if line.strip()]

            if self.chk_limit.isChecked():
                chip_ids = [cid[:48] for cid in chip_ids]

            df = pd.DataFrame(chip_ids, columns=["芯片ID"])

            base_name, _ = os.path.splitext(self.file_path)
            output_file = base_name + ".xlsx"

            counter = 1
            while os.path.exists(output_file):
                output_file = f"{base_name}_{counter}.xlsx"
                counter += 1

            df.to_excel(output_file, index=False, engine="openpyxl")
            QMessageBox.information(self, "完成", f"Excel 导出成功！\n{output_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TxtToExcel()
    win.show()
    sys.exit(app.exec_())
