# char_viewer.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPlainTextEdit,
    QComboBox, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QTimer

# optional detectors
try:
    from charset_normalizer import from_bytes as cn_from_bytes
    _HAS_CHARSET_NORMALIZER = True
except Exception:
    _HAS_CHARSET_NORMALIZER = False

try:
    import chardet
    _HAS_CHARDET = True
except Exception:
    _HAS_CHARDET = False


def detect_encoding_bytes(b):
    """尝试用 charset-normalizer 或 chardet 检测编码，返回 (encoding, confidence)"""
    if _HAS_CHARSET_NORMALIZER:
        try:
            results = cn_from_bytes(b)
            if results:
                best = results.best()
                if best:
                    enc = best.encoding
                    conf = getattr(best, "confidence", 0.9)
                    return enc, conf
        except Exception:
            pass
    if _HAS_CHARDET:
        try:
            r = chardet.detect(b)
            enc = r.get("encoding")
            conf = r.get("confidence", 0)
            if enc:
                return enc, conf
        except Exception:
            pass
    return None, 0.0


def printable_and_chinese_score(text):
    """
    计算简单启发式评分：
    - printable_ratio: 非替代字符、非控制字符的比例
    - chinese_ratio: 常用汉字比例
    - score = printable_ratio + 0.5 * chinese_ratio
    """
    if not text:
        return 0.0, 0.0, 0.0
    length = len(text)
    replace_char = '\ufffd'
    replace_count = text.count(replace_char)
    control_count = sum(1 for ch in text if ord(ch) < 32 and ch not in '\n\r\t')
    printable_count = length - replace_count - control_count
    printable_ratio = printable_count / length
    han_count = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    chinese_ratio = han_count / length
    score = printable_ratio + 0.5 * chinese_ratio
    return score, printable_ratio, chinese_ratio


def read_as_text(path, force_encoding=None, sample_size=4096):
    """
    可靠地读取文件并选出合理编码
    返回： (text, used_encoding, detected_encoding_or_none)
    逻辑要点：
      - 先用字节判断 BOM（只有有 BOM 时才直接用 UTF-16/32）
      - 如果用户手动强制编码则直接按手动的
      - 优先尝试 UTF-8 / UTF-8-SIG
      - 使用检测器获得 detected_enc（可无）
      - 构造候选编码集合（优先中文友好编码），对每个解码结果评分并选择最佳；
      - 额外规则：如果检测为 cp949 或 utf-16，但 GBK 解码结果可读性与汉字比例明显更好，则自动改用 GBK（并把 detected 编码返回为 orig）
    """
    with open(path, "rb") as f:
        data = f.read()

    if not data:
        return "", "utf-8", None

    b = data

    # 只在确实有 BOM 的情况下直接使用对应 Unicode 编码：
    if b.startswith(b'\xef\xbb\xbf'):
        return b.decode('utf-8-sig'), 'utf-8-sig', 'utf-8-sig'
    if b.startswith(b'\xff\xfe\x00\x00') or b.startswith(b'\x00\x00\xfe\xff'):
        try:
            return b.decode('utf-32'), 'utf-32', 'utf-32'
        except Exception:
            pass
    if b.startswith(b'\xff\xfe') or b.startswith(b'\xfe\xff'):
        try:
            return b.decode('utf-16'), 'utf-16', 'utf-16'
        except Exception:
            pass

    # 如果用户手动指定编码（下拉框），直接使用（errors='replace' 保证不会抛）
    if force_encoding and force_encoding != "自动检测":
        try:
            return b.decode(force_encoding, errors='replace'), force_encoding, None
        except Exception:
            return b.decode('utf-8', errors='replace'), 'utf-8', None

    # 尝试常见的 UTF-8 先行
    try:
        txt = b.decode('utf-8')
        return txt, 'utf-8', 'utf-8'
    except Exception:
        pass
    try:
        txt = b.decode('utf-8-sig')
        return txt, 'utf-8-sig', 'utf-8-sig'
    except Exception:
        pass

    # 自动检测（可得 None）
    detected_enc, conf = detect_encoding_bytes(b[:sample_size])

    # 构造候选编码列表：优先中文友好编码，再把检测到的以及其它常见编码补上
    preferred = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'cp936']
    others = ['big5', 'shift_jis', 'cp949', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin1', 'iso-8859-1']
    candidates = []
    for p in preferred:
        if p not in candidates:
            candidates.append(p)
    if detected_enc and detected_enc not in candidates:
        candidates.append(detected_enc)
    for o in others:
        if o not in candidates:
            candidates.append(o)

    # 对候选做评分，选最高分。并对中文编码进行适当加权；对 cp949 有偏好修正
    best_score = -1.0
    best_enc = None
    best_text = None
    scores = {}
    for enc in candidates:
        if not enc:
            continue
        try:
            txt = b.decode(enc, errors='replace')
        except Exception:
            continue
        sc, pr, hr = printable_and_chinese_score(txt)
        # 对中文相关编码在出现汉字时加权
        if enc.lower() in ('gbk', 'cp936', 'gb18030') and hr > 0.01:
            sc += 0.2 + hr
        # 如果检测器给出的是 cp949，则对 GBK 类候选稍微加分（避免把中文误判为韩文）
        if detected_enc and detected_enc.lower() == 'cp949' and enc.lower() in ('gbk', 'cp936', 'gb18030'):
            sc += 0.5 * hr
        scores[enc] = (sc, pr, hr, txt)
        if sc > best_score:
            best_score = sc
            best_enc = enc
            best_text = txt

    # 额外判断：如果检测器认为是 utf-16，但 GBK 的评分明显优于 utf-16（且 GBK 汉字比例较高），则改用 GBK
    if detected_enc and detected_enc.lower().startswith('utf-16'):
        utf16_score = scores.get(detected_enc, (-1, 0, 0, None))[0]
        gbk_score, gbk_pr, gbk_hr, gbk_text = scores.get('gbk', (-1, 0, 0, None))
        if gbk_score is not None and gbk_score > utf16_score and gbk_hr > 0.15 and gbk_pr > 0.6:
            return gbk_text, 'gbk', detected_enc

    # 如果 best_enc 是 None，回退到 utf-8 replace
    if best_enc is None:
        return b.decode('utf-8', errors='replace'), 'utf-8', detected_enc

    # 如果检测出的编码（detected_enc）与最终使用编码不同，并且 detected_enc 是 cp949 → 如果我们选择了 gbk，需要标记修正
    return best_text, best_enc, detected_enc


# ----------------- GUI 部分 -----------------
class CharViewer(QMainWindow):
    def __init__(self, filepath=None):
        super().__init__()
        self.setWindowTitle("通用字符浏览器")
        self.resize(920, 700)

        self.filepath = None
        self.last_pos = 0
        self.follow_mode = False
        self.encoding = "utf-8"
        self.detected_encoding = None

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)

        layout = QVBoxLayout()
        topbar = QHBoxLayout()

        self.open_btn = QPushButton("打开文件")
        self.open_btn.clicked.connect(self.open_file)
        topbar.addWidget(self.open_btn)

        self.follow_btn = QPushButton("跟随关闭")
        self.follow_btn.clicked.connect(self.toggle_follow)
        topbar.addWidget(self.follow_btn)

        # 手动编码下拉
        self.enc_box = QComboBox()
        self.enc_box.addItems([
            "自动检测", "utf-8", "utf-8-sig", "gbk", "gb18030", "cp936",
            "big5", "shift_jis", "cp949", "utf-16", "utf-16-le", "utf-16-be", "latin1"
        ])
        self.enc_box.currentIndexChanged.connect(self.on_enc_change)
        topbar.addWidget(self.enc_box)

        topbar.addStretch()
        layout.addLayout(topbar)
        layout.addWidget(self.text)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 状态栏：显示当前生效编码与修正信息
        self.status = self.statusBar()
        self.status_label = QLabel("未打开文件")
        self.status.addPermanentWidget(self.status_label)

        # 定时器（tail -f）
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_update)

        if filepath:
            self.load_file(filepath)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*)")
        if path:
            self.load_file(path)

    def load_file(self, path):
        self.filepath = path
        self.setWindowTitle(f"通用字符浏览器 - {path}")
        self.last_pos = 0
        # 打开时默认回到“自动检测”
        self.enc_box.blockSignals(True)
        self.enc_box.setCurrentIndex(0)
        self.enc_box.blockSignals(False)
        self.reload_file()

    def reload_file(self, force_encoding=None):
        if not self.filepath:
            return
        try:
            text, used_enc, detected_enc = read_as_text(self.filepath, force_encoding)
            self.text.setPlainText(text)
            self.encoding = used_enc
            self.detected_encoding = detected_enc
            self.last_pos = os.path.getsize(self.filepath)

            # 状态栏显示具体信息
            if detected_enc and detected_enc.lower() == "cp949" and used_enc.lower().startswith("gb"):
                self.status_label.setText(f"编码: {used_enc} (由 {detected_enc} 自动修正)")
            elif detected_enc and detected_enc.lower().startswith("utf-16") and used_enc.lower().startswith("gb"):
                self.status_label.setText(f"编码: {used_enc} (由 {detected_enc} 自动修正)")
            elif detected_enc and detected_enc.lower() != used_enc.lower():
                self.status_label.setText(f"编码: {used_enc} (检测: {detected_enc})")
            else:
                self.status_label.setText(f"编码: {used_enc}")

            # 如果是自动检测得到的编码，尽量在下拉框上反映出来（但不改变用户选择）
            if force_encoding is None:
                idx = self.enc_box.findText(used_enc)
                if idx >= 0:
                    self.enc_box.blockSignals(True)
                    self.enc_box.setCurrentIndex(idx)
                    self.enc_box.blockSignals(False)

        except Exception as e:
            self.text.setPlainText(f"读取文件失败: {e}")
            self.status_label.setText("读取失败")

    def on_enc_change(self, idx):
        sel = self.enc_box.currentText()
        if not self.filepath:
            return
        if sel == "自动检测":
            self.reload_file(None)
        else:
            self.reload_file(sel)

    def toggle_follow(self):
        self.follow_mode = not self.follow_mode
        if self.follow_mode:
            self.follow_btn.setText("跟随开启")
            self.timer.start(1000)
        else:
            self.follow_btn.setText("跟随关闭")
            self.timer.stop()

    def check_update(self):
        """tail -f 风格追加（用当前生效编码解码新增字节）"""
        if not self.filepath:
            return
        try:
            # 处理文件被截断（日志轮转）
            try:
                size = os.path.getsize(self.filepath)
                if size < self.last_pos:
                    self.last_pos = 0
            except Exception:
                pass

            with open(self.filepath, "rb") as f:
                f.seek(self.last_pos)
                new_bytes = f.read()
                if new_bytes:
                    try:
                        new_text = new_bytes.decode(self.encoding, errors="replace")
                    except Exception:
                        new_text = new_bytes.decode("utf-8", errors="replace")
                    self.text.appendPlainText(new_text)
                    self.text.moveCursor(QTextCursor.End)
                self.last_pos = f.tell()
        except Exception as e:
            print("刷新出错:", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    path = sys.argv[1] if len(sys.argv) > 1 else None
    win = CharViewer(path)
    win.show()
    sys.exit(app.exec_())
