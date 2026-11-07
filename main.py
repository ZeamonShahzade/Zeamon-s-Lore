import os
import re
import json
import threading
import sys
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Triangle
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

class YTDLPLogger:
    """Keep yt-dlp messages away from Android's redirected console streams."""
    def debug(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass


try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    from androidstorage4kivy import SharedStorage
except Exception:
    SharedStorage = None


# Zaemon: midnight-purple visual system
BG = (0.018, 0.012, 0.032, 1)
CARD = (0.075, 0.045, 0.105, 1)
CARD_ALT = (0.105, 0.065, 0.145, 1)
PURPLE = (0.64, 0.12, 0.96, 1)
PURPLE_DARK = (0.30, 0.07, 0.43, 1)
PINK = (0.98, 0.22, 0.76, 1)
WHITE = (0.97, 0.94, 1, 1)
MUTED = (0.69, 0.62, 0.76, 1)
GREEN = (0.43, 0.91, 0.67, 1)
RED = (1, 0.36, 0.46, 1)


class Panel(BoxLayout):
    def __init__(self, bg=CARD, radius=18, **kwargs):
        super().__init__(**kwargs)
        self._panel_color = bg
        with self.canvas.before:
            Color(*bg)
            self._shape = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(radius)]
            )
        self.bind(pos=self._sync_shape, size=self._sync_shape)

    def _sync_shape(self, *_):
        self._shape.pos = self.pos
        self._shape.size = self.size


class CrownLogo(Widget):
    """A crisp, scalable crown mark drawn with Kivy canvas shapes."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.crown_color = Color(*PINK)
            self.crown = Triangle(points=[])
            self.base_color = Color(*PURPLE)
            self.base = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(2)])
        self.bind(pos=self._draw_mark, size=self._draw_mark)
        self._draw_mark()

    def _draw_mark(self, *_):
        w, h = self.size
        x, y = self.pos
        self.crown.points = [
            x + w*.12, y + h*.48,
            x + w*.27, y + h*.84,
            x + w*.48, y + h*.58,
            x + w*.70, y + h*.84,
            x + w*.88, y + h*.48,
        ]
        self.base.pos = (x + w*.18, y + h*.28)
        self.base.size = (w*.64, h*.14)


class ZButton(Button):
    def __init__(self, bg=PURPLE, fg=WHITE, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = bg
        self.color = fg
        self.font_size = sp(14)
        self.bold = True
        self.halign = "center"
        self.valign = "middle"


class ZLabel(Label):
    def __init__(self, color=WHITE, size=14, bold=False, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.font_size = sp(size)
        self.bold = bold
        self.halign = kwargs.get("halign", "left")
        self.valign = "middle"
        self.shorten = True
        self.shorten_from = "right"


class ZaemonRoot(BoxLayout):
    status_text = StringProperty("Ready when you are.")
    progress_value = NumericProperty(0)


class ZaemonApp(App):
    def build(self):
        self.title = "Zaemon Mote Shahzade"
        Window.clearcolor = BG
        self.download_dir = os.path.join(
            self.user_data_dir, "Downloads", "Zaemon"
        )
        os.makedirs(self.download_dir, exist_ok=True)
        self.history_path = os.path.join(self.user_data_dir, "history.json")
        self.history = self.load_history()
        self.download_running = False
        self.current_page = "home"
        self.history_filter = "All"

        self.root_ui = ZaemonRoot(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(13), dp(9), dp(13), dp(7)],
        )
        self.build_header()
        self.content = BoxLayout(orientation="vertical")
        self.root_ui.add_widget(self.content)
        self.build_navigation()
        self.navigate("home")
        return self.root_ui

    def build_header(self):
        header = BoxLayout(
            size_hint_y=None, height=dp(70), spacing=dp(10),
            padding=[dp(4), dp(3), dp(4), dp(3)],
        )
        mark = Panel(
            bg=(0.13, 0.045, 0.20, 1),
            size_hint=(None, None), size=(dp(54), dp(54)),
            padding=dp(8),
        )
        mark.add_widget(CrownLogo())
        header.add_widget(mark)

        titles = BoxLayout(orientation="vertical", spacing=dp(0))
        titles.add_widget(ZLabel(
            text="[b]ZAEMON[/b]", size=23, bold=True, markup=True,
        ))
        titles.add_widget(ZLabel(
            text="MOTE SHAHZADE  •  VIDEO DOWNLOADER",
            size=9, color=PINK,
        ))
        header.add_widget(titles)

        badge = Panel(
            bg=(0.20, 0.055, 0.30, 1),
            size_hint=(None, None), size=(dp(38), dp(38)),
            padding=dp(2),
        )
        badge.add_widget(ZLabel(
            text="*", size=24, color=WHITE, halign="center",
        ))
        header.add_widget(badge)
        self.root_ui.add_widget(header)

    def build_navigation(self):
        nav = Panel(
            orientation="horizontal", size_hint_y=None, height=dp(62),
            padding=[dp(5), dp(5)], spacing=dp(5),
            bg=(0.055, 0.030, 0.080, 1),
        )
        self.nav_buttons = {}
        for key, label in (
            ("home", "⌂\nHome"),
            ("downloads", "⇩\nDownloads"),
            ("settings", "⚙\nSettings"),
        ):
            btn = ZButton(
                text=label, bg=(0.14, 0.075, 0.19, 1),
                font_size=sp(11),
            )
            btn.bind(
                on_release=lambda instance, page=key: self.navigate(page)
            )
            self.nav_buttons[key] = btn
            nav.add_widget(btn)
        self.root_ui.add_widget(nav)

    def navigate(self, page):
        self.current_page = page
        for key, btn in self.nav_buttons.items():
            btn.background_color = (
                PURPLE_DARK if key == page else (0.14, 0.075, 0.19, 1)
            )
        self.content.clear_widgets()
        if page == "home":
            self.show_home()
        elif page == "downloads":
            self.show_downloads()
        else:
            self.show_settings()

    def section_title(self, title, subtitle=None):
        box = BoxLayout(
            orientation="vertical", size_hint_y=None,
            height=dp(52 if subtitle else 34), spacing=0,
        )
        box.add_widget(ZLabel(text=title, size=20, bold=True))
        if subtitle:
            box.add_widget(ZLabel(text=subtitle, size=10, color=MUTED))
        return box

    def make_card(self, height=None, padding=dp(12), spacing=dp(8), bg=CARD):
        card = Panel(
            orientation="vertical", padding=padding, spacing=spacing,
            size_hint_y=None, bg=bg,
        )
        if height is not None:
            card.height = dp(height)
        return card

    def make_spinner(self, text, values, bg=CARD_ALT):
        return Spinner(
            text=text, values=values, background_normal="",
            background_color=bg, color=WHITE, font_size=sp(12),
        )

    def show_home(self):
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        body = BoxLayout(
            orientation="vertical", size_hint_y=None,
            spacing=dp(11), padding=[0, dp(3), 0, dp(8)],
        )
        body.bind(minimum_height=body.setter("height"))

        hero = Panel(
            orientation="vertical", size_hint_y=None, height=dp(116),
            padding=[dp(14), dp(10)], spacing=dp(2),
            bg=(0.105, 0.035, 0.16, 1),
        )
        hero.add_widget(ZLabel(
            text="YOUR DOWNLOADS. YOUR KINGDOM.", size=16,
            bold=True, color=WHITE, halign="center",
        ))
        hero.add_widget(ZLabel(
            text="One link. Your favourite media. All in one place.",
            size=10, color=MUTED, halign="center",
        ))
        hero.add_widget(ZLabel(
            text="WELCOME TO ZAEMON  •  MOTE SHAHZADE",
            size=10, color=PINK, halign="center",
        ))
        body.add_widget(hero)

        link_card = self.make_card(height=105, padding=dp(11), spacing=dp(7))
        link_card.add_widget(ZLabel(
            text="PASTE YOUR MEDIA LINK", size=10, color=MUTED, bold=True,
            size_hint_y=None, height=dp(17),
        ))
        row = BoxLayout(size_hint_y=None, height=dp(47), spacing=dp(6))
        self.url_input = TextInput(
            hint_text="Paste video link here...", multiline=False,
            font_size=sp(13), foreground_color=WHITE,
            hint_text_color=MUTED, background_normal="",
            background_active="", background_color=CARD_ALT,
            padding=[dp(10), dp(12)], cursor_color=PINK,
        )
        row.add_widget(self.url_input)
        paste = ZButton(
            text="PASTE", bg=PURPLE_DARK,
            size_hint_x=None, width=dp(72), font_size=sp(11),
        )
        paste.bind(on_release=self.paste_clipboard)
        row.add_widget(paste)
        link_card.add_widget(row)
        body.add_widget(link_card)

        body.add_widget(ZLabel(
            text="CHOOSE YOUR FORMAT", size=11, color=MUTED, bold=True,
            size_hint_y=None, height=dp(18),
        ))
        mode_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(7))
        self.mode_spinner = self.make_spinner(
            "Video (MP4)", ("Video (MP4)", "Audio (MP3)")
        )
        self.quality_spinner = self.make_spinner(
            "Best quality", ("Best quality", "1080p", "720p", "480p", "360p")
        )
        mode_row.add_widget(self.mode_spinner)
        mode_row.add_widget(self.quality_spinner)
        body.add_widget(mode_row)

        self.download_btn = ZButton(
            text="DOWNLOAD", bg=PURPLE,
            size_hint_y=None, height=dp(55), font_size=sp(17),
        )
        self.download_btn.bind(on_release=self.on_download)
        body.add_widget(self.download_btn)

        progress = self.make_card(height=83, padding=dp(11), spacing=dp(6))
        progress.add_widget(ZLabel(
            text="DOWNLOAD STATUS", size=10, color=MUTED, bold=True,
            size_hint_y=None, height=dp(15),
        ))
        self.progress_bar = ProgressBar(
            max=100, value=self.root_ui.progress_value,
            size_hint_y=None, height=dp(9),
        )
        progress.add_widget(self.progress_bar)
        self.status_label = ZLabel(
            text=self.root_ui.status_text, size=10, color=WHITE,
        )
        progress.add_widget(self.status_label)
        body.add_widget(progress)

        body.add_widget(ZLabel(
            text="Only download content you own or have permission to save.",
            size=9, color=MUTED, halign="center",
            size_hint_y=None, height=dp(24),
        ))
        scroll.add_widget(body)
        self.content.add_widget(scroll)

    def paste_clipboard(self, *_):
        try:
            from kivy.core.clipboard import Clipboard
            value = Clipboard.paste()
            if value:
                self.url_input.text = value.strip()
                self.set_status("Link pasted. Ready to download.")
        except Exception:
            self.set_status("Clipboard unavailable. Paste the link manually.")

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
            self.set_status(
                "MP3 conversion needs an Android FFmpeg build. Video mode is ready."
            )
            return

        self.download_running = True
        self.download_btn.disabled = True
        self.root_ui.progress_value = 0
        self.progress_bar.value = 0
        self.set_status("Starting download...")
        threading.Thread(
            target=self.download_worker,
            args=(link, self.quality_spinner.text),
            daemon=True,
        ).start()

    def download_worker(self, link, quality):
        try:
            fmt = "best[ext=mp4]/best"
            if quality != "Best quality":
                height = quality.replace("p", "")
                fmt = (
                    f"best[height<={height}][ext=mp4]/"
                    f"best[height<={height}]/best"
                )
            options = {
                "format": fmt,
                "outtmpl": os.path.join(
                    self.download_dir, "%(title).100s.%(ext)s"
                ),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "logger": YTDLPLogger(),
                "retries": 3,
                "fragment_retries": 3,
                "progress_hooks": [self.progress_hook],
            }
            # Kivy redirects stderr to its own logger stream. yt-dlp may
            # write to stderr internally, so give it a normal file stream
            # while the download runs, then restore Kivy's stream.
            original_stderr = sys.stderr
            error_log_path = os.path.join(
                self.user_data_dir, "yt_dlp_errors.log"
            )
            try:
                with open(error_log_path, "a", encoding="utf-8") as error_log:
                    sys.stderr = error_log
                    with yt_dlp.YoutubeDL(options) as downloader:
                        info = downloader.extract_info(link, download=True)
                        filename = downloader.prepare_filename(info)
            finally:
                sys.stderr = original_stderr

            message = "Download complete. Saved in Zaemon's folder."
            if SharedStorage is not None and os.path.isfile(filename):
                try:
                    shared = SharedStorage().copy_to_shared(filename)
                    if shared:
                        message = "Download complete. Copied to shared storage."
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
            Clock.schedule_once(
                lambda dt, saved=item, msg=message:
                self.finish_download(saved, msg), 0
            )
        except Exception as error:
            message = str(error).replace("\n", " ")[:180]
            Clock.schedule_once(
                lambda dt, msg=message:
                self.finish_download(None, "Download failed: " + msg), 0
            )

    def progress_hook(self, data):
        if data.get("status") == "downloading":
            try:
                value = float(
                    str(data.get("_percent_str", "0%")).replace("%", "").strip()
                )
            except Exception:
                total = (
                    data.get("total_bytes")
                    or data.get("total_bytes_estimate") or 0
                )
                value = (
                    data.get("downloaded_bytes", 0) / total * 100
                    if total else 0
                )
            downloaded = data.get("_downloaded_bytes_str") or ""
            speed = data.get("_speed_str") or ""
            detail = f"{value:.1f}%"
            if speed:
                detail += f"  •  {speed}"
            Clock.schedule_once(
                lambda dt, val=value, text=detail:
                self.update_progress(val, text), 0
            )
        elif data.get("status") == "finished":
            Clock.schedule_once(
                lambda dt: self.update_progress(100, "Processing file..."), 0
            )

    def update_progress(self, value, message=None):
        self.root_ui.progress_value = max(0, min(100, value))
        if hasattr(self, "progress_bar"):
            self.progress_bar.value = self.root_ui.progress_value
        if hasattr(self, "status_label"):
            self.status_label.text = message or f"Downloading... {value:.1f}%"

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
                data = json.load(file)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_history(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as file:
                json.dump(self.history, file, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def show_downloads(self):
        body = BoxLayout(orientation="vertical", spacing=dp(9))
        body.add_widget(self.section_title(
            "Downloads", "Your saved videos and audio in one place."
        ))

        counts = {
            "All": len(self.history),
            "Video": sum(1 for x in self.history if x.get("mode") == "Video"),
            "Audio": sum(1 for x in self.history if x.get("mode") == "Audio"),
        }
        filters = BoxLayout(size_hint_y=None, height=dp(39), spacing=dp(6))
        for key in ("All", "Video", "Audio"):
            btn = ZButton(
                text=f"{key} ({counts[key]})",
                bg=PURPLE_DARK if self.history_filter == key else CARD_ALT,
                font_size=sp(11),
            )
            btn.bind(
                on_release=lambda instance, value=key:
                self.set_history_filter(value)
            )
            filters.add_widget(btn)
        body.add_widget(filters)

        selected = [
            item for item in self.history
            if self.history_filter == "All"
            or item.get("mode", "Video") == self.history_filter
        ]
        if not selected:
            empty = self.make_card(
                height=145, padding=dp(18), spacing=dp(8),
                bg=(0.085, 0.045, 0.12, 1),
            )
            empty.add_widget(ZLabel(
                text="Z", size=31, color=PINK, halign="center",
            ))
            empty.add_widget(ZLabel(
                text="Your library is waiting", size=16, bold=True,
                halign="center",
            ))
            empty.add_widget(ZLabel(
                text="Your downloaded videos will appear here.",
                size=10, color=MUTED, halign="center",
            ))
            body.add_widget(empty)
        else:
            scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
            listing = GridLayout(
                cols=1, spacing=dp(8), size_hint_y=None,
            )
            listing.bind(minimum_height=listing.setter("height"))
            for item in selected:
                card = Panel(
                    orientation="horizontal", size_hint_y=None,
                    height=dp(78), padding=dp(10), spacing=dp(9),
                    bg=CARD,
                )
                icon = Panel(
                    size_hint=(None, None), size=(dp(52), dp(52)),
                    bg=(0.22, 0.07, 0.31, 1), padding=dp(3),
                )
                icon.add_widget(ZLabel(
                    text="A" if item.get("mode") == "Audio" else "V",
                    size=22, color=PINK, halign="center",
                ))
                card.add_widget(icon)
                details = BoxLayout(orientation="vertical", spacing=dp(2))
                details.add_widget(ZLabel(
                    text=item.get("title", "Downloaded file"),
                    size=11, bold=True,
                ))
                details.add_widget(ZLabel(
                    text=item.get("filename", ""),
                    size=9, color=MUTED,
                ))
                details.add_widget(ZLabel(
                    text=item.get("date", "Completed") + "  -  Completed",
                    size=9, color=GREEN,
                ))
                card.add_widget(details)
                listing.add_widget(card)
            scroll.add_widget(listing)
            body.add_widget(scroll)

        self.content.add_widget(body)

    def set_history_filter(self, value):
        self.history_filter = value
        self.navigate("downloads")

    def show_settings(self):
        body = BoxLayout(orientation="vertical", spacing=dp(10))
        body.add_widget(self.section_title(
            "Settings", "Make Zaemon feel at home."
        ))

        storage = self.make_card(padding=dp(14), spacing=dp(6))
        storage.add_widget(ZLabel(
            text="DOWNLOAD LOCATION", size=10, color=MUTED, bold=True,
        ))
        storage.add_widget(ZLabel(
            text=self.download_dir, size=10, color=WHITE,
        ))
        body.add_widget(storage)

        about = self.make_card(padding=dp(14), spacing=dp(6))
        about.add_widget(ZLabel(
            text="ZAEMON THE MOTE SHAHZADE", size=14, bold=True,
        ))
        about.add_widget(ZLabel(
            text="Version 1.3  •  Royal Purple Edition",
            size=10, color=MUTED,
        ))
        about.add_widget(ZLabel(
            text="Video downloads use yt-dlp. Download only content you own "
                 "or have permission to save.",
            size=10, color=MUTED,
        ))
        body.add_widget(about)

        formats = self.make_card(padding=dp(14), spacing=dp(6))
        formats.add_widget(ZLabel(
            text="FORMAT SUPPORT", size=10, color=MUTED, bold=True,
        ))
        formats.add_widget(ZLabel(
            text="MP4 video: enabled\nMP3 audio: requires an Android-compatible "
                 "FFmpeg package and is not enabled in this build.",
            size=11,
        ))
        body.add_widget(formats)
        self.content.add_widget(body)


if __name__ == "__main__":
    ZaemonApp().run()