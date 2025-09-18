import sys
import os
import vlc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QFileDialog, QSlider, QLabel, QComboBox, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer


class MiniVlcPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音频播放器")
        self.resize(600, 120)

        # 确保能找到 VLC 的 DLL（适配 Windows 64-bit 默认路径）
        vlc_path = r"C:\Program Files\VideoLAN\VLC"
        if os.name == "nt" and os.path.exists(vlc_path):
            os.add_dll_directory(vlc_path)

        # VLC 播放器实例
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # 播放源选择
        self.source_combo = QComboBox()
        self.source_combo.addItems(["本地文件", "网络流媒体"])
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入网络音频地址")
        self.url_input.setEnabled(False)

        # 控件
        self.open_btn = QPushButton("打开")
        self.play_btn = QPushButton("播放")
        self.stop_btn = QPushButton("停止")

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(80)
        self.player.audio_set_volume(50)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)  # VLC 用比例值
        self.time_label = QLabel("00:00 / 00:00")

        # 布局
        top_row = QHBoxLayout()
        top_row.addWidget(self.source_combo)
        top_row.addWidget(self.open_btn)
        top_row.addWidget(self.url_input, 1)
        top_row.addWidget(self.play_btn)
        top_row.addWidget(self.stop_btn)
        top_row.addWidget(QLabel("音量"))
        top_row.addWidget(self.volume_slider)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.position_slider, 1)
        bottom_row.addWidget(self.time_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_row)
        main_layout.addLayout(bottom_row)
        self.setLayout(main_layout)

        # 信号
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        self.open_btn.clicked.connect(self.open_file)
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.stop)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.position_slider.sliderMoved.connect(self.set_position)

        # 定时器刷新 UI
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

    def on_source_changed(self, index):
        self.open_btn.setEnabled(index == 0)
        self.url_input.setEnabled(index == 1)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "",
                                              "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg);;所有文件 (*)")
        if path:
            media = self.instance.media_new(path)
            self.player.set_media(media)
            self.player.play()
            self.play_btn.setText("暂停")

    def toggle_play(self):
        if self.source_combo.currentIndex() == 1:  # 网络流
            url = self.url_input.text().strip()
            if url:
                # ✅ 修复 bug：始终设置新的媒体，而不是只在 get_media() is None 时才设置
                media = self.instance.media_new(url)
                self.player.set_media(media)

        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setText("播放")
        else:
            self.player.play()
            self.play_btn.setText("暂停")

    def stop(self):
        self.player.stop()
        self.play_btn.setText("播放")

    def set_volume(self, value):
        self.player.audio_set_volume(value)

    def set_position(self, value):
        self.player.set_position(value / 1000.0)

    def update_ui(self):
        if self.player is None or self.player.get_media() is None:
            return

        length = self.player.get_length()  # 毫秒
        pos = self.player.get_time()       # 毫秒

        if length > 0:
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(int(self.player.get_position() * 1000))
            self.position_slider.blockSignals(False)
            self.time_label.setText(f"{self.ms_to_str(pos)} / {self.ms_to_str(length)}")
        else:
            # 流媒体没有总时长
            self.time_label.setText(f"{self.ms_to_str(pos)} / --:--")

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
    player = MiniVlcPlayer()
    player.show()
    sys.exit(app.exec_())
