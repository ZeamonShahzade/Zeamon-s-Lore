import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout

try:
    import yt_dlp
except Exception:
    yt_dlp = None

KV = """
<RootUI>:
    orientation: "vertical"
    padding: "18dp"
    spacing: "12dp"
    canvas.before:
        Color:
            rgba: .035, .035, .055, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: "66dp"
        Label:
            text: "[b]ZAIMON[/b] [color=#B58CFF]THE MOTE SHAHZADE[/color]\\\\n[color=#A7A1B5]Your downloads, with a little cat attitude.[/color]"
            markup: True
            halign: "left"
            valign: "middle"
            text_size: self.size
        Label:
            text: "ฅ^•ﻌ•^ฅ"
            font_size: "28sp"
            size_hint_x: None
            width: "65dp"
            color: .78, .62, 1, 1

    Label:
        text: "Paste a video or audio link"
        size_hint_y: None
        height: "26dp"
        halign: "left"
        text_size: self.size

    TextInput:
        id: url_input
        hint_text: "https://..."
        multiline: False
        size_hint_y: None
        height: "48dp"
        background_color: .10, .10, .15, 1
        foreground_color: 1, 1, 1, 1

    BoxLayout:
        size_hint_y: None
        height: "44dp"
        spacing: "8dp"
        Spinner:
            id: mode
            text: "MP4 Video"
            values: ["MP4 Video", "MP3 Audio"]
        Spinner:
            id: quality
            text: "Best quality"
            values: ["Best quality", "1080p", "720p", "480p", "360p"]

    Button:
        text: "DOWNLOAD"
        size_hint_y: None
        height: "52dp"
        background_normal: ""
        background_color: .48, .27, .78, 1
        on_release: app.start_download(url_input.text, mode.text, quality.text)

    ProgressBar:
        max: 100
        value: root.progress_value
        size_hint_y: None
        height: "8dp"

    Label:
        text: root.status_text
        size_hint_y: None
        height: "48dp"
        halign: "left"
        text_size: self.size

    Label:
        text: root.folder_label
        size_hint_y: None
        height: "36dp"
        font_size: "10sp"
        color: .65, .62, .72, 1
        halign: "left"
        text_size: self.size

    Label:
        text: "Downloads are stored in this app's private folder."
        font_size: "10sp"
        color: .65, .62, .72, 1
"""

class RootUI(BoxLayout):
    status_text = StringProperty("Ready when you are.")
    progress_value = NumericProperty(0)
    folder_label = StringProperty("Zaimon / Downloads")


class ZaimonApp(App):
    def build(self):
        self.title = "Zaimon the Mote Shahzade"
        self.download_dir = os.path.join(self.user_data_dir, "Downloads", "Zaimon")
        os.makedirs(self.download_dir, exist_ok=True)
        self.root_widget = Builder.load_string(KV)
        return self.root_widget

    def start_download(self, link, mode, quality):
        link = (link or "").strip()
        if not link.startswith(("https://", "http://")):
            self.root_widget.status_text = "Please paste a valid web link."
            return
        if yt_dlp is None:
            self.root_widget.status_text = "Download engine is unavailable in this build."
            return
        self.root_widget.progress_value = 0
        self.root_widget.status_text = "Starting download..."
        threading.Thread(
            target=self.download_worker,
            args=(link, mode, quality),
            daemon=True
        ).start()

    def download_worker(self, link, mode, quality):
        try:
            fmt = "bestaudio/best" if mode == "MP3 Audio" else "best[ext=mp4]/best"
            if mode != "MP3 Audio" and quality != "Best quality":
                height = quality.replace("p", "")
                fmt = f"best[height<={height}][ext=mp4]/best[height<={height}]/best"

            options = {
                "format": fmt,
                "outtmpl": os.path.join(self.download_dir, "%(title).100s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "progress_hooks": [self.progress_hook],
            }
            if mode == "MP3 Audio":
                options["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }]

            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([link])
            Clock.schedule_once(lambda dt: self.finish("Download complete."), 0)
        except Exception as error:
            message = str(error)[:150]
            Clock.schedule_once(lambda dt, m=message: self.finish("Download failed: " + m), 0)

    def progress_hook(self, data):
        if data.get("status") == "downloading":
            try:
                percent = float(data.get("_percent_str", "0%").replace("%", "").strip())
            except Exception:
                percent = 0
            Clock.schedule_once(lambda dt, p=percent: self.set_progress(p), 0)

    def set_progress(self, value):
        self.root_widget.progress_value = max(0, min(100, value))
        self.root_widget.status_text = f"Downloading... {value:.1f}%"

    def finish(self, message):
        self.root_widget.status_text = message
        if message == "Download complete.":
            self.root_widget.progress_value = 100


if __name__ == "__main__":
    ZaimonApp().run()
