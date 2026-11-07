import os
import re
import json
import threading
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget

try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    from androidstorage4kivy import SharedStorage
except Exception:
    SharedStorage = None


BG = (0.025, 0.018, 0.045, 1)
CARD = (0.075, 0.045, 0.105, 1)
CARD_2 = (0.105, 0.065, 0.145, 1)
PURPLE = (0.66, 0.16, 0.98, 1)
PINK = (0.98, 0.20, 0.75, 1)
WHITE = (0.96, 0.93, 1, 1)
MUTED = (0.68, 0.62, 0.75, 1)
GREEN = (0.45, 0.90, 0.67, 1)


class Panel(BoxLayout):
    def __init__(self, bg=CARD, radius=18, **kwargs):
        super().__init__(**kwargs)
        self._bg = bg
        self._radius = radius
        with self.canvas.before:
            Color(*self._bg)
            self._shape = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[dp(self._radius)])
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        self._shape.pos = self.pos
        self._shape.size = self.size


class ZButton(Button):
    def __init__(self, bg=PURPLE, fg=WHITE, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = bg
        self.color = fg
        self.font_size = sp(14)
        self.bold = True


class ZLabel(Label):
    def __init__(self, color=WHITE, size=14, bold=False, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.font_size = sp(size)
        self.bold = bold
        self.halign = "left"
        self.valign = "middle"


class ZaimonRoot(BoxLayout):
    status_text = StringProperty("Ready when you are.")
    progress_value = NumericProperty(0)


class ZaimonApp(App):
    def build(self):
        self.title = "Zaimon the Mote Shahzade"
        Window.clearcolor = BG
        self.download_dir = os.path.join(self.user_data_dir, "Downloads", "Zaimon")
        os.makedirs(self.download_dir, exist_ok=True)
        self.history_path = os.path.join(self.user_data_dir, "history.json")
        self.history = self.load_history()
        self.download_running = False
        self.root_ui = ZaimonRoot(orientation="vertical", spacing=dp(10),
                                  padding=[dp(16), dp(12), dp(16), dp(8)])
        self.build_header()
        self.content = BoxLayout(orientation="vertical")
        self.root_ui.add_widget(self.content)
        self.build_navigation()
        self.show_home()
        return self.root_ui

    def build_header(self):
        header = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(10))
        logo_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(logo_path):
            from kivy.uix.image import Image
            logo = Image(source=logo_path, size_hint=(None, None),
                         size=(dp(54), dp(54)), allow_stretch=True,
                         keep_ratio=True)
            header.add_widget(logo)
        else:
            badge = Panel(bg=(0.20, 0.07, 0.30, 1), size_hint=(None, None),
                          size=(dp(54), dp(54)), padding=dp(5))
            badge.add_widget(ZLabel(text="🐾", size=25, color=PINK,
                                    halign="center"))
            header.add_widget(badge)

        titles = BoxLayout(orientation="vertical", spacing=0)
        titles.add_widget(ZLabel(text="[b]ZAIMON[/b]", markup=True,
                                 size=21, color=WHITE))
        titles.add_widget(ZLabel(text="THE MOTE SHAHZADE  ✦  DOWNLOADER",
                                 size=9, color=MUTED))
        header.add_widget(titles)
        self.root_ui.add_widget(header)

    def section_title(self, title, subtitle=None):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=dp(54 if subtitle else 34), spacing=dp(1))
        box.add_widget(ZLabel(text=title, size=21, bold=True))
        if subtitle:
            box.add_widget(ZLabel(text=subtitle, size=11, color=MUTED))
        return box

    def make_card(self, children=None, height=None, padding=dp(14), spacing=dp(10)):
        card = Panel(orientation="vertical", padding=padding, spacing=spacing,
                     size_hint_y=None)
        if height:
            card.height = dp(height)
        if children:
            for child in children:
                card.add_widget(child)
        return card

    def build_navigation(self):
        nav = Panel(orientation="horizontal", size_hint_y=None,
                    height=dp(62), padding=[dp(6), dp(5)],
                    spacing=dp(5), bg=(0.065, 0.035, 0.095, 1))
        self.nav_buttons = {}
        for key, label in [("home", "⌂  Home"),
                           ("downloads", "⇩  Downloads"),
                           ("settings", "⚙  Settings")]:
            btn = ZButton(text=label, bg=(0.22, 0.08, 0.31, 1),
                          font_size=sp(12))
            btn.bind(on_release=lambda instance, k=key: self.navigate(k))
            self.nav_buttons[key] = btn
            nav.add_widget(btn)
        self.root_ui.add_widget(nav)

    def navigate(self, page):
        for key, btn in self.nav_buttons.items():
            btn.background_color = PURPLE if key == page else (0.22, 0.08, 0.31, 1)
        if page == "home":
            self.show_home()
        elif page == "downloads":
            self.show_downloads()
        else:
            self.show_settings()

    def reset_content(self):
        self.content.clear_widgets()

    def show_home(self):
        self.reset_content()
        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", size_hint_y=None,
                         spacing=dp(12), padding=[0, dp(4), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))
        body.add_widget(self.section_title("Your downloads, your kingdom.",
                                           "Paste a link and let Zaimon handle the rest."))

        url_card = self.make_card(padding=dp(12), spacing=dp(8))
        url_card.height = dp(112)
        url_card.add_widget(ZLabel(text="VIDEO OR AUDIO LINK", size=10,
                                   color=MUTED, bold=True, size_hint_y=None,
                                   height=dp(18)))
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.url_input = TextInput(hint_text="Paste video link here...",
                                   multiline=False, font_size=sp(14),
                                   foreground_color=WHITE,
                                   hint_text_color=MUTED,
                                   background_normal="",
                                   background_active="",
                                   background_color=CARD_2,
                                   padding=[dp(12), dp(13)],
                                   cursor_color=PINK)
        row.add_widget(self.url_input)
        paste = ZButton(text="PASTE", bg=(0.36, 0.10, 0.55, 1),
                        size_hint_x=None, width=dp(76))
        paste.bind(on_release=self.paste_clipboard)
        row.add_widget(paste)
        url_card.add_widget(row)
        body.add_widget(url_card)

        body.add_widget(ZLabel(text="DOWNLOAD AS", size=11, color=MUTED,
                               bold=True, size_hint_y=None, height=dp(20)))
        mode_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.mode_spinner = Spinner(text="Video (MP4)",
                                    values=("Video (MP4)", "Audio (MP3)"),
                                    background_normal="",
                                    background_color=(0.38, 0.10, 0.58, 1),
                                    color=WHITE, font_size=sp(13))
        self.quality_spinner = Spinner(text="Best quality",
                                       values=("Best quality", "1080p", "720p",
                                               "480p", "360p"),
                                       background_normal="",
                                       background_color=CARD_2,
                                       color=WHITE, font_size=sp(13))
        mode_row.add_widget(self.mode_spinner)
        mode_row.add_widget(self.quality_spinner)
        body.add_widget(mode_row)

        self.download_btn = ZButton(text="⇩   DOWNLOAD",
                                    bg=(0.68, 0.10, 0.92, 1),
                                    size_hint_y=None, height=dp(56),
                                    font_size=sp(18))
        self.download_btn.bind(on_release=self.on_download)
        body.add_widget(self.download_btn)

        progress_card = self.make_card(padding=dp(12), spacing=dp(7))
        progress_card.height = dp(92)
        progress_card.add_widget(ZLabel(text="DOWNLOAD PROGRESS", size=10,
                                        color=MUTED, bold=True,
                                        size_hint_y=None, height=dp(16)))
        self.progress_bar = ProgressBar(max=100, value=self.root_ui.progress_value,
                                        size_hint_y=None, height=dp(8))
        progress_card.add_widget(self.progress_bar)
        self.status_label = ZLabel(text=self.root_ui.status_text, size=12)
        progress_card.add_widget(self.status_label)
        body.add_widget(progress_card)

        tip = ZLabel(text="Only download content you own or have permission to save.",
                     size=10, color=MUTED, size_hint_y=None, height=dp(34))
        body.add_widget(tip)
        scroll.add_widget(body)
        self.content.add_widget(scroll)

    def paste_clipboard(self, *_):
        try:
            from kivy.core.clipboard import Clipboard
            value = Clipboard.paste()
            if value:
                self.url_input.text = value.strip()
                self.root_ui.status_text = "Link pasted. Ready to download."
                self.status_label.text = self.root_ui.status_text
        except Exception:
            self.root_ui.status_text = "Clipboard unavailable. Paste the link manually."
            self.status_label.text = self.root_ui.status_text

    def on_download(self, *_):
        link = self.url_input.text.strip()
        if not re.match(r"^https?://", link, re.IGNORECASE):
            self.set_status("Please paste a valid http or https link.")
            return
        if yt_dlp is None:
            self.set_status("Download engine is unavailable in this build.")
            return
        if self.download_running:
            self.set_status("A download is already running. Please wait.")
            return

        mode = self.mode_spinner.text
        if mode == "Audio (MP3)":
            self.set_status("MP3 conversion is not enabled yet. Choose Video (MP4).")
            return

        self.download_running = True
        self.download_btn.disabled = True
        self.root_ui.progress_value = 0
        self.progress_bar.value = 0
        self.set_status("Starting download...")
        threading.Thread(target=self.download_worker,
                         args=(link, self.quality_spinner.text),
                         daemon=True).start()

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

            message = "Download complete. Saved in Zaimon's folder."
            if SharedStorage is not None and os.path.isfile(filename):
                try:
                    shared = SharedStorage().copy_to_shared(filename)
                    if shared:
                        message = "Download complete. Saved to shared storage."
                except Exception:
                    pass

            item = {
                "title": info.get("title") or os.path.basename(filename),
                "filename": os.path.basename(filename),
                "path": filename,
                "mode": "Video",
                "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                "status": "Completed",
            }
            Clock.schedule_once(lambda dt, x=item, m=message: self.finish_download(x, m), 0)
        except Exception as error:
            message = str(error).replace("\n", " ")[:180]
            Clock.schedule_once(lambda dt, m=message: self.finish_download(None, "Download failed: " + m), 0)

    def progress_hook(self, data):
        if data.get("status") == "downloading":
            try:
                value = float(str(data.get("_percent_str", "0%")).replace("%", "").strip())
            except Exception:
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                value = (data.get("downloaded_bytes", 0) / total * 100) if total else 0
            Clock.schedule_once(lambda dt, v=value: self.update_progress(v), 0)
        elif data.get("status") == "finished":
            Clock.schedule_once(lambda dt: self.update_progress(100), 0)

    def update_progress(self, value):
        self.root_ui.progress_value = max(0, min(100, value))
        if hasattr(self, "progress_bar"):
            self.progress_bar.value = self.root_ui.progress_value
        if hasattr(self, "status_label"):
            self.status_label.text = f"Downloading... {value:.1f}%"

    def set_status(self, message):
        self.root_ui.status_text = message
        if hasattr(self, "status_label"):
            self.status_label.text = message

    def finish_download(self, item, message):
        self.download_running = False
        if hasattr(self, "download_btn"):
            self.download_btn.disabled = False
        self.set_status(message)
        if item:
            self.history.insert(0, item)
            self.save_history()
            self.root_ui.progress_value = 100
            if hasattr(self, "progress_bar"):
                self.progress_bar.value = 100

    def load_history(self):
        try:
            with open(self.history_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return []

    def save_history(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as file:
                json.dump(self.history, file, indent=2)
        except Exception:
            pass

    def show_downloads(self):
        self.reset_content()
        body = BoxLayout(orientation="vertical", spacing=dp(10))
        body.add_widget(self.section_title("Downloads", "Your recent Zaimon downloads."))
        if not self.history:
            empty = Panel(orientation="vertical", padding=dp(20),
                          spacing=dp(8))
            empty.add_widget(ZLabel(text="🐾", size=36, color=PINK,
                                    halign="center"))
            empty.add_widget(ZLabel(text="No downloads yet", size=17,
                                    bold=True, halign="center"))
            empty.add_widget(ZLabel(text="Your completed files will appear here.",
                                    size=11, color=MUTED, halign="center"))
            body.add_widget(empty)
        else:
            scroll = ScrollView()
            listing = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
            listing.bind(minimum_height=listing.setter("height"))
            for item in self.history:
                card = Panel(orientation="vertical", size_hint_y=None,
                             height=dp(82), padding=dp(10), spacing=dp(3))
                card.add_widget(ZLabel(text=item.get("title", "Downloaded file"),
                                       size=13, bold=True))
                card.add_widget(ZLabel(text=item.get("filename", ""),
                                       size=10, color=MUTED))
                card.add_widget(ZLabel(text=item.get("date", "Completed"),
                                       size=10, color=GREEN))
                listing.add_widget(card)
            scroll.add_widget(listing)
            body.add_widget(scroll)
        self.content.add_widget(body)

    def show_settings(self):
        self.reset_content()
        body = BoxLayout(orientation="vertical", spacing=dp(12))
        body.add_widget(self.section_title("Settings", "Make Zaimon feel at home."))
        about = self.make_card(padding=dp(16), spacing=dp(8))
        about.add_widget(ZLabel(text="ZAIMON THE MOTE SHAHZADE", size=14,
                                bold=True))
        about.add_widget(ZLabel(text="Version 1.1  •  Purple Royal Edition",
                                size=11, color=MUTED))
        about.add_widget(ZLabel(text="Downloads are stored in the app's private folder. "
                                     "Some Android builds may also copy videos to shared storage.",
                                size=11, color=MUTED))
        body.add_widget(about)
        note = self.make_card(padding=dp(16), spacing=dp(8))
        note.add_widget(ZLabel(text="SUPPORTED FORMAT", size=11, color=MUTED,
                               bold=True))
        note.add_widget(ZLabel(text="MP4 video downloads are enabled. MP3 conversion "
                                    "will be added with an Android-compatible FFmpeg build.",
                                size=12))
        body.add_widget(note)
        self.content.add_widget(body)


if __name__ == "__main__":
    ZaimonApp().run()
