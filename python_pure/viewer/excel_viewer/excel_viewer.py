import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QComboBox, QFileDialog, QTableView, QHBoxLayout, QLabel
)


class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df.index)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        value = self._df.iat[index.row(), index.column()]
        return "" if pd.isna(value) else str(value)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        else:
            return str(section + 1)

    def setDataFrame(self, df):
        self.beginResetModel()
        self._df = df
        self.endResetModel()


class ExcelViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel 浏览器 (简版)")
        self.resize(900, 600)

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top = QHBoxLayout()
        self.open_btn = QPushButton("打开 Excel 文件")
        self.open_btn.clicked.connect(self.open_file)
        top.addWidget(self.open_btn)

        top.addWidget(QLabel("选择 sheet:"))
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self.change_sheet)
        top.addWidget(self.sheet_combo)

        layout.addLayout(top)

        self.table = QTableView()
        self.model = PandasModel()
        self.table.setModel(self.model)
        layout.addWidget(self.table)

        self.sheets = {}
        self.current_file = None

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 Excel 文件", "", "Excel 文件 (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            self.sheets = pd.read_excel(path, sheet_name=None)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(self.sheets.keys())
            if self.sheets:
                self.load_sheet(list(self.sheets.keys())[0])
        except Exception as e:
            print("打开失败:", e)

    def change_sheet(self, index):
        if index >= 0:
            name = self.sheet_combo.itemText(index)
            self.load_sheet(name)

    def load_sheet(self, name):
        df = self.sheets[name]
        self.model.setDataFrame(df)
        self.table.resizeColumnsToContents()


def main():
    app = QApplication(sys.argv)
    win = ExcelViewer()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
