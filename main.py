import os
import re
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

try:
    from androidstorage4kivy import SharedStorage
except Exception:
    SharedStorage = None

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
            text: "[b]ZAIMON[/b] [color=#B58CFF]THE MOTE SHAHZADE[/color]\\n[color=#A7A1B5]Your downloads, with a little cat attitude.[/color]"
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
        height: "58dp"
        halign: "left"
        valign: "middle"
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
        text: "Videos: Movies folder  •  Audio: Music folder"
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
        self.download_running = False
        return self.root_widget

    def start_download(self, link, mode, quality):
        link = (link or "").strip()
        if not re.match(r"^https?://", link, re.IGNORECASE):
            self.root_widget.status_text = "Please paste a valid http or https link."
            return
        if yt_dlp is None:
            self.root_widget.status_text = "Download engine is unavailable in this build."
            return
        if self.download_running:
            self.root_widget.status_text = "A download is already running. Please wait."
            return
        if mode == "MP3 Audio":
            self.root_widget.status_text = "MP3 conversion needs FFmpeg. Not enabled in this build yet."
            return

        self.download_running = True
        self.root_widget.progress_value = 0
        self.root_widget.status_text = "Starting download..."
        threading.Thread(target=self.download_worker, args=(link, quality), daemon=True).start()

    def download_worker(self, link, quality):
        try:
            fmt = "best[ext=mp4]/best"
            if quality != "Best quality":
                height = quality.replace("p", "")
                fmt = f"best[height<={height}][ext=mp4]/best[height<={height}]/best"

            options = {
                "format": fmt,
                "outtmpl": os.path.join(self.download_dir, "%(title).100s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "retries": 3,
                "fragment_retries": 3,
                "progress_hooks": [self.progress_hook],
            }
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(link, download=True)
                filename = downloader.prepare_filename(info)

            final_file = filename
            # Publish the completed video to Android shared media storage.
            if SharedStorage is not None and os.path.isfile(final_file):
                shared = SharedStorage().copy_to_shared(final_file)
                if shared:
                    final_message = "Download complete. Saved to your public Movies collection."
                else:
                    final_message = "Downloaded privately, but could not publish to shared storage."
            else:
                final_message = "Download complete in Zaimon's private folder."

            Clock.schedule_once(lambda dt, m=final_message: self.finish(m), 0)
        except Exception as error:
            message = str(error).replace("\n", " ")[:180]
            Clock.schedule_once(lambda dt, m=message: self.finish("Download failed: " + m), 0)

    def progress_hook(self, data):
        if data.get("status") == "downloading":
            percent_text = data.get("_percent_str", "0%").replace("%", "").strip()
            try:
                percent = float(percent_text)
            except Exception:
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                percent = (data.get("downloaded_bytes", 0) / total * 100) if total else 0
            Clock.schedule_once(lambda dt, p=percent: self.set_progress(p), 0)
        elif data.get("status") == "finished":
            Clock.schedule_once(lambda dt: self.set_progress(100), 0)

    def set_progress(self, value):
        self.root_widget.progress_value = max(0, min(100, value))
        self.root_widget.status_text = f"Downloading... {value:.1f}%"

    def finish(self, message):
        self.download_running = False
        self.root_widget.status_text = message
        if message.startswith("Download complete") or message.startswith("Downloaded privately"):
            self.root_widget.progress_value = 100


if __name__ == "__main__":
    ZaimonApp().run()
