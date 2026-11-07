[app]
title = Zaimon the Mote Shahzade
package.name = zaimon
package.domain = com.zaimon.downloader

source.dir = .
source.include_exts = py,json,png,jpg
source.exclude_dirs = bin,.buildozer,__pycache__,.git,.github
source.exclude_patterns = *_reference.png, README*, *.txt

# App icon (points to your app_logo.png)
icon.filename = %(source.dir)s/app_logo.png

# Python requirements
requirements = python3,kivy==2.3.0,yt-dlp,certifi,androidstorage4kivy

# Display
orientation = portrait
fullscreen = 0

# Android configuration
android.api = 34
android.minapi = 23
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.archs = arm64-v8a
android.allow_backup = False
android.accept_sdk_license = True

# Python-for-Android
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1