import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QListWidget, QLabel, 
                             QTimeEdit, QHBoxLayout, QMessageBox)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, QTimer, QTime, Qt
from wallpaper_manager import WallpaperManager

class VideoWallpaperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Win11 Dynamic Wallpaper")
        self.resize(700, 500)

        # 核心组件初始化
        self.wp_manager = WallpaperManager()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # 视频渲染窗口 (这个窗口会被嵌入桌面)
        self.video_container = QWidget()
        self.video_container.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 使用布局管理器确保视频widget自动填充容器
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        container_layout.addWidget(self.video_widget)
        
        self.player.setVideoOutput(self.video_widget)
        
        # 默认静音 (壁纸通常不需要声音)
        self.audio_output.setVolume(0) 

        # 状态数据
        self.playlist = [] # 存储结构: [{'path': str, 'time': str(HH:mm)}]
        self.is_wallpaper_mode = False
        
        self.init_ui()
        
        # 定时器1：性能优化 (每1秒检测一次窗口状态)
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.check_performance_optimization)
        self.perf_timer.start(1000)

        # 定时器2：计划任务 (每10秒检测一次时间切换)
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(10000)
        
        # 循环播放逻辑
        self.player.mediaStatusChanged.connect(self.loop_video)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. 播放列表区域
        layout.addWidget(QLabel("<b>壁纸播放列表</b> (包含触发时间):"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # 2. 控制面板区域
        controls_group = QWidget()
        controls_layout = QHBoxLayout(controls_group)
        
        self.btn_add = QPushButton("添加 MP4 视频")
        self.btn_add.clicked.connect(self.add_video)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        
        self.btn_set_schedule = QPushButton("更新选中视频的触发时间")
        self.btn_set_schedule.clicked.connect(self.set_schedule_for_item)

        controls_layout.addWidget(self.btn_add)
        controls_layout.addWidget(QLabel("选择时间:"))
        controls_layout.addWidget(self.time_edit)
        controls_layout.addWidget(self.btn_set_schedule)
        
        layout.addWidget(controls_group)

        # 3. 模式切换开关
        self.btn_toggle = QPushButton("🚀 开启/关闭 动态壁纸模式")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setStyleSheet("QPushButton:checked { background-color: #4CAF50; color: white; }")
        self.btn_toggle.clicked.connect(self.toggle_wallpaper_mode)
        layout.addWidget(self.btn_toggle)
        
        # 4. 说明文本
        info_label = QLabel("提示:\n1. 想要随日出日落更换? 添加两个视频，分别设置时间为 06:00 和 18:00 即可。\n2. 开启模式后，最大化任何窗口时壁纸会自动暂停以节省性能。")
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

    def add_video(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择视频", "", "MP4 Files (*.mp4)")
        for f in files:
            # 默认时间设置为当前时间
            current_time_str = QTime.currentTime().toString("HH:mm")
            item_data = {'path': f, 'time': current_time_str}
            self.playlist.append(item_data)
            self.refresh_list_item(len(self.playlist) - 1)

    def refresh_list_item(self, index):
        if index < 0 or index >= len(self.playlist):
            return
        item_data = self.playlist[index]
        name = os.path.basename(item_data['path'])
        display_text = f"⏰ [{item_data['time']}] - 🎬 {name}"
        
        if index < self.list_widget.count():
            self.list_widget.item(index).setText(display_text)
        else:
            self.list_widget.addItem(display_text)

    def set_schedule_for_item(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            time_str = self.time_edit.time().toString("HH:mm")
            self.playlist[row]['time'] = time_str
            self.refresh_list_item(row)
            QMessageBox.information(self, "成功", f"已更新触发时间为 {time_str}")

    def toggle_wallpaper_mode(self, checked):
        if checked:
            if not self.playlist:
                QMessageBox.warning(self, "列表为空", "请先添加至少一个视频文件！")
                self.btn_toggle.setChecked(False)
                return
            
            # 获取窗口句柄并嵌入桌面 (黑魔法)
            hwnd = int(self.video_container.winId())
            self.wp_manager.set_window_as_wallpaper(hwnd)
            self.video_container.show()
            
            # 启动时检查一次应该放哪个
            self.check_schedule(force_start=True)
            self.is_wallpaper_mode = True
        else:
            self.is_wallpaper_mode = False
            self.player.stop()
            self.video_container.hide()

    def play_video(self, path):
        current_source = self.player.source().toLocalFile()
        # 只有当路径不同，或者当前不在播放时才重新加载
        if current_source != path or self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()

    def loop_video(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.play()

    def check_performance_optimization(self):
        """核心功能2：当有全屏/最大化应用时停止"""
        if not self.is_wallpaper_mode:
            return

        is_maximized = self.wp_manager.is_foreground_maximized()
        
        if is_maximized and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            # 停止播放而不是暂停
            self.player.stop()
        elif not is_maximized and self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            # 从停止状态恢复时重新播放
            self.player.play()

    def check_schedule(self, force_start=False):
        """核心功能3：根据时间更换壁纸"""
        if not self.is_wallpaper_mode or not self.playlist:
            return

        now = QTime.currentTime()
        best_video = None
        min_diff = 24 * 3600

        # 逻辑：寻找当前时间之前最近的一个时间点
        # 例如现在是 13:00，列表有 08:00(A) 和 18:00(B)
        # 应该播放 A
        
        valid_candidates = []
        for item in self.playlist:
            item_time = QTime.fromString(item['time'], "HH:mm")
            if item_time <= now:
                valid_candidates.append((item, item_time))
        
        if valid_candidates:
            # 在所有过去的时间点中，找一个最晚的（也就是离现在最近的）
            valid_candidates.sort(key=lambda x: x[1], reverse=True)
            best_video = valid_candidates[0][0]
        else:
            # 如果当前时间比列表里所有时间都早（例如现在01:00，列表只有08:00），
            # 那么应该播放昨晚最后设定的那个（也就是列表里时间最晚的那个）
            sorted_all = sorted(self.playlist, key=lambda x: QTime.fromString(x['time'], "HH:mm"), reverse=True)
            if sorted_all:
                best_video = sorted_all[0]

        if best_video:
            current_playing = self.player.source().toLocalFile()
            if force_start or current_playing != best_video['path']:
                print(f"切换壁纸: {best_video['path']} (设定时间: {best_video['time']})")
                self.play_video(best_video['path'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoWallpaperApp()
    window.show()
    sys.exit(app.exec())
