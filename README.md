# Zaimon the Mote Shahzade (Android starter project)

A Kivy-based Android downloader interface with a dark purple/cat-inspired visual identity.

## What's included
- MP4 and MP3 mode selector
- Quality selector
- Download progress
- Download history
- Background download thread
- App-private download folder

## Important build and runtime notes
This is an Android **source project**, not a prebuilt APK. Building an APK requires Linux (or WSL2 on Windows), Android SDK/NDK and Buildozer.

The app uses `yt-dlp`. Website support can change over time. Use it only for content you own, have permission to download, or that the platform makes available for downloading. Respect copyright and each site's terms.

### FFmpeg limitation
MP3 extraction and some high-resolution video downloads require FFmpeg to merge or convert streams. This starter project does not bundle an Android FFmpeg binary, so MP3 conversion may fail until an Android-compatible FFmpeg build is added. The MP4 selector prefers a single MP4 stream to avoid a merge where possible.

### Storage
For safety and compatibility with modern Android versions, downloads are stored in the app's private storage:
`<app data>/files/Downloads/Zaimon`
Android file managers may restrict access to this folder. A production release should add Android's Storage Access Framework (SAF) export/folder picker.

## Build on Ubuntu / WSL2
1. Install system dependencies:
   `sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv build-essential autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev`
2. Install Buildozer:
   `python3 -m pip install --user --upgrade buildozer`
3. From this folder, run:
   `buildozer android debug`
4. The APK will be placed in `bin/`.

Buildozer packaging for `yt-dlp` may require additional python-for-android recipes/dependency adjustments as upstream packages evolve. Test on a real device before distribution.