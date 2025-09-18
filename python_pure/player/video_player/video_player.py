# video_player_with_combo.py
import sys
import os
import vlc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QFileDialog, QSlider, QLabel, QFrame, QComboBox, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer

class ComboVideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频播放器")
        self.resize(800, 520)

        # --- Windows VLC dll 路径 ---
        vlc_path = r"C:\Program Files\VideoLAN\VLC"
        if os.name == "nt" and os.path.exists(vlc_path):
            try:
                os.add_dll_directory(vlc_path)
            except Exception:
                pass

        # VLC 实例
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # 视频区域
        self.video_frame = QFrame()
        self.video_frame.setFrameShape(QFrame.Box)
        self.video_frame.setStyleSheet("background: black;")

        # 下拉框：选择本地文件 / 网络URL
        self.source_combo = QComboBox()
        self.source_combo.addItems(["本地文件", "网络URL"])
        self.source_combo.currentIndexChanged.connect(self.switch_source)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入视频URL…")
        self.url_input.setVisible(False)

        self.open_btn = QPushButton("打开")

        # 播放控制
        self.play_btn = QPushButton("播放")
        self.stop_btn = QPushButton("停止")

        # 进度条
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.time_label = QLabel("00:00 / 00:00")

        # 音量
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.player.audio_set_volume(50)

        # 布局
        top_row = QHBoxLayout()
        top_row.addWidget(self.source_combo)
        top_row.addWidget(self.url_input, 1)
        top_row.addWidget(self.open_btn)

        control_row = QHBoxLayout()
        control_row.addWidget(self.play_btn)
        control_row.addWidget(self.stop_btn)
        control_row.addWidget(QLabel("音量"))
        control_row.addWidget(self.volume_slider)
        control_row.addStretch()

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.position_slider, 1)
        bottom_row.addWidget(self.time_label)

        layout = QVBoxLayout()
        layout.addWidget(self.video_frame, 1)
        layout.addLayout(bottom_row)
        layout.addLayout(control_row)
        layout.addLayout(top_row)
        self.setLayout(layout)

        # 信号槽
        self.open_btn.clicked.connect(self.open_source)
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.stop)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.valueChanged.connect(self.set_volume)

        # 定时器
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

    def switch_source(self, index):
        """切换输入模式"""
        if index == 0:  # 本地文件
            self.url_input.setVisible(False)
        else:  # 网络URL
            self.url_input.setVisible(True)

    def open_source(self):
        """根据下拉框选择加载本地文件或URL"""
        if self.source_combo.currentIndex() == 0:  # 本地
            path, _ = QFileDialog.getOpenFileName(
                self, "选择视频文件", "",
                "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm *.ts);;所有文件 (*)")
            if not path:
                return
        else:  # URL
            path = self.url_input.text().strip()
            if not path:
                return

        media = self.instance.media_new(path)
        self.player.set_media(media)
        self._set_video_window()
        self.player.play()
        self.play_btn.setText("暂停")

    def _set_video_window(self):
        if sys.platform.startswith("win"):
            self.player.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform.startswith("linux"):
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(int(self.video_frame.winId()))

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setText("播放")
        else:
            self._set_video_window()
            self.player.play()
            self.play_btn.setText("暂停")

    def stop(self):
        self.player.stop()
        self.play_btn.setText("播放")

    def set_volume(self, value):
        self.player.audio_set_volume(value)

    def set_position(self, slider_value):
        pos = slider_value / 1000.0
        self.player.set_position(pos)

    def update_ui(self):
        media = self.player.get_media()
        if media is None:
            return

        length = self.player.get_length()
        cur = self.player.get_time()

        pos = self.player.get_position()
        if pos >= 0:
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(int(pos * 1000))
            self.position_slider.blockSignals(False)

        if length > 0:
            self.time_label.setText(f"{self.ms_to_str(cur)} / {self.ms_to_str(length)}")
        else:
            self.time_label.setText(f"{self.ms_to_str(cur)} / --:--")

    def ms_to_str(self, ms):
        if ms <= 0:
            return "00:00"
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02}:{m:02}:{s:02}"
        else:
            return f"{m:02}:{s:02}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = ComboVideoPlayer()
    player.show()
    sys.exit(app.exec_())
