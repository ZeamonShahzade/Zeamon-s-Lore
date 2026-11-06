import os
import threading
import json
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

try:
    import yt_dlp
except Exception:
    yt_dlp = None

KV = r"""
#:import dp kivy.metrics.dp
<RootUI>:
    orientation: "vertical"
    padding: dp(18)
    spacing: dp(12)
    canvas.before:
        Color:
            rgba: 0.035, 0.035, 0.055, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(62)
        spacing: dp(10)
        BoxLayout:
            orientation: "vertical"
            spacing: dp(1)
            Label:
                text: "[b]ZAIMON[/b] [color=#B58CFF]THE MOTE SHAHZADE[/color]"
                markup: True
                font_size: "17sp"
                halign: "left"
                valign: "middle"
                text_size: self.size
            Label:
                text: "A little download magic. A lot of cat attitude."
                font_size: "11sp"
                color: 0.63, 0.62, 0.70, 1
                halign: "left"
                valign: "top"
                text_size: self.size
        Label:
            text: "ฅ^•ﻌ•^ฅ"
            font_size: "28sp"
            size_hint_x: None
            width: dp(72)
            color: 0.78, 0.62, 1, 1

    BoxLayout:
        size_hint_y: None
        height: dp(42)
        canvas.before:
            Color:
                rgba: 0.10, 0.09, 0.15, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: "VIDEO & AUDIO DOWNLOADER"
            color: 0.80, 0.73, 0.95, 1
            bold: True
            font_size: "12sp"

    Label:
        text: "Paste a video or reel link"
        size_hint_y: None
        height: dp(24)
        halign: "left"
        text_size: self.size
        color: 0.88, 0.86, 0.93, 1

    TextInput:
        id: url_input
        hint_text: "https://..."
        multiline: False
        size_hint_y: None
        height: dp(48)
        padding: [dp(12), dp(13), dp(12), dp(10)]
        background_normal: ""
        background_active: ""
        background_color: 0.10, 0.10, 0.15, 1
        foreground_color: 1, 1, 1, 1
        cursor_color: 0.75, 0.55, 1, 1
        hint_text_color: 0.48, 0.47, 0.55, 1

    BoxLayout:
        size_hint_y: None
        height: dp(42)
        spacing: dp(8)
        Spinner:
            id: mode
            text: "MP4 Video"
            values: ["MP4 Video", "MP3 Audio"]
            background_normal: ""
            background_color: 0.19, 0.14, 0.28, 1
            color: 1, 1, 1, 1
        Spinner:
            id: quality
            text: "Best quality"
            values: ["Best quality", "1080p", "720p", "480p", "360p"]
            background_normal: ""
            background_color: 0.19, 0.14, 0.28, 1
            color: 1, 1, 1, 1

    Button:
        text: "CHOOSE DOWNLOAD FOLDER"
        size_hint_y: None
        height: dp(42)
        background_normal: ""
        background_color: 0.13, 0.12, 0.19, 1
        color: 0.86, 0.79, 1, 1
        on_release: app.show_folder_info()

    Label:
        text: root.folder_label
        size_hint_y: None
        height: dp(30)
        font_size: "10sp"
        color: 0.62, 0.61, 0.69, 1
        halign: "left"
        text_size: self.size

    Button:
        id: download_btn
        text: "↓   DOWNLOAD"
        size_hint_y: None
        height: dp(52)
        background_normal: ""
        background_color: 0.48, 0.27, 0.78, 1
        color: 1, 1, 1, 1
        bold: True
        on_release: app.start_download(url_input.text, mode.text, quality.text)

    ProgressBar:
        id: progress
        max: 100
        value: root.progress_value
        size_hint_y: None
        height: dp(8)

    Label:
        text: root.status_text
        size_hint_y: None
        height: dp(36)
        font_size: "12sp"
        color: 0.82, 0.79, 0.88, 1
        halign: "left"
        text_size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(34)
        Label:
            text: "RECENT DOWNLOADS"
            bold: True
            font_size: "11sp"
            color: 0.72, 0.61, 0.91, 1
            halign: "left"
            text_size: self.size
        Button:
            text: "Refresh"
            size_hint_x: None
            width: dp(82)
            background_normal: ""
            background_color: 0.13, 0.12, 0.19, 1
            on_release: app.refresh_history()

    ScrollView:
        do_scroll_x: False
        GridLayout:
            id: history_box
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(6)
"""

class RootUI(BoxLayout):
    status_text = StringProperty("Ready when you are.")
    progress_value = NumericProperty(0)
    folder_label = StringProperty("Saved inside app storage: Downloads/Zaimon")

class ZaimonApp(App):
    def build(self):
        self.title = "Zaimon the Mote Shahzade"
        self.download_dir = os.path.join(self.user_data_dir, "Downloads", "Zaimon")
        os.makedirs(self.download_dir, exist_ok=True)
        self.history_file = os.path.join(self.user_data_dir, "history.json")
        Builder.load_string(KV)
        self.ui = RootUI()
        Clock.schedule_once(lambda *_: self.refresh_history(), 0.2)
        return self.ui

    def show_folder_info(self):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        Popup(
            title="Download location",
            content=Label(
                text="Files are saved in this app's private storage:\\n"
                     + self.download_dir
                     + "\\n\\nAndroid restricts access to some app folders. "
                       "A future version can add an Android folder picker/export."
            ),
            size_hint=(0.88, 0.42)
        ).open()

    def _progress_hook(self, data):
        if data.get("status") == "downloading":
            percent = data.get("_percent_str", "0%").strip()
            try:
                value = float(percent.replace("%", "").replace("\x1b[0;94m", "").replace("\x1b[0m", ""))
            except Exception:
                value = 0
            Clock.schedule_once(lambda dt: self._set_progress(value, "Downloading... " + percent), 0)
        elif data.get("status") == "finished":
            Clock.schedule_once(lambda dt: self._set_progress(100, "Processing file..."), 0)

    def _set_progress(self, value, message):
        self.ui.progress_value = max(0, min(100, value))
        self.ui.status_text = message

    def start_download(self, link, mode, quality):
        link = (link or "").strip()
        if not link:
            self.ui.status_text = "Paste a link first."
            return
        if not link.startswith(("https://", "http://")):
            self.ui.status_text = "Please enter a valid http:// or https:// link."
            return
        if yt_dlp is None:
            self.ui.status_text = "Download engine is unavailable in this build."
            return

        self.ui.ids.download_btn.disabled = True
        self.ui.progress_value = 0
        self.ui.status_text = "Starting download..."
        threading.Thread(
            target=self._download_worker,
            args=(link, mode, quality),
            daemon=True
        ).start()

    def _download_worker(self, link, mode, quality):
        try:
            if mode == "MP3 Audio":
                options = {
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(self.download_dir, "%(title).100s.%(ext)s"),
                    "progress_hooks": [self._progress_hook],
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                # MP3 conversion requires FFmpeg. If it is not bundled, preserve the
                # original audio format rather than failing the entire download.
                options["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            else:
                if quality == "Best quality":
                    fmt = "best[ext=mp4]/best"
                else:
                    height = quality.replace("p", "")
                    fmt = f"best[height<={height}][ext=mp4]/best[height<={height}]/best"
                options = {
                    "format": fmt,
                    "outtmpl": os.path.join(self.download_dir, "%(title).100s.%(ext)s"),
                    "progress_hooks": [self._progress_hook],
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                }
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([link])
            self._save_history(link, mode)
            Clock.schedule_once(lambda dt: self._download_done(), 0)
        except Exception as exc:
            message = str(exc)[:180]
            Clock.schedule_once(lambda dt, m=message: self._download_error(m), 0)

    def _download_done(self):
        self.ui.status_text = "Download finished. Check the Zaimon downloads folder."
        self.ui.progress_value = 100
        self.ui.ids.download_btn.disabled = False
        self.refresh_history()

    def _download_error(self, message):
        self.ui.status_text = "Download failed: " + message
        self.ui.ids.download_btn.disabled = False

    def _save_history(self, link, mode):
        try:
            rows = []
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    rows = json.load(f)
            rows.insert(0, {
                "link": link,
                "mode": mode,
                "date": datetime.now().strftime("%d %b %Y, %I:%M %p")
            })
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(rows[:30], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def refresh_history(self):
        box = self.ui.ids.history_box
        box.clear_widgets()
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                rows = json.load(f)
        except Exception:
            rows = []
        from kivy.uix.label import Label
        if not rows:
            box.add_widget(Label(
                text="No downloads yet. Your first catch goes here.",
                size_hint_y=None, height=34, color=(0.56, 0.54, 0.63, 1),
                font_size="11sp"
            ))
        else:
            for item in rows[:10]:
                title = item.get("link", "")
                if len(title) > 58:
                    title = title[:55] + "..."
                box.add_widget(Label(
                    text=f"{item.get('mode', 'File')}  •  {item.get('date', '')}\\n{title}",
                    size_hint_y=None, height=48, color=(0.78, 0.75, 0.85, 1),
                    font_size="10sp", halign="left", valign="middle",
                    text_size=(self.ui.width - 40, None)
                ))

if __name__ == "__main__":
    ZaimonApp().run()