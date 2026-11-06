[app]
title = Zaimon the Mote Shahzade
package.name = zaimon
package.domain = com.zaimon.downloader
source.dir = .
source.include_exts = py,kv,json,png,jpg
version = 1.0.0
requirements = python3,kivy,yt-dlp
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 23
android.ndk = 25b
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.archs = arm64-v8a
android.allow_backup = False
android.accept_sdk_license = True
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
