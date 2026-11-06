# Zaimon the Mote Shahzade

A starter Android downloader project with a dark AMOLED interface and purple accents.

## Upload to your GitHub repository
1. Download and extract this ZIP on your phone or computer.
2. Open your repository on GitHub.
3. Choose **Add file → Upload files**.
4. Upload the contents of this folder (including `.github`).
5. Commit the files to the `main` branch.

## Start a cloud APK build
1. Open the repository's **Actions** tab.
2. Select **Build Zaimon Android APK**.
3. Tap **Run workflow**.
4. When the run completes, open it and download the `Zaimon-Android-debug` artifact.

This is starter source code, not a prebuilt APK. The first Android packaging run may reveal dependency or build-environment issues that need fixing.

## Current limitations
- yt-dlp packaging on Android may need additional python-for-android recipes.
- MP3 extraction and merging separate audio/video streams require a compatible FFmpeg binary; one is not bundled here.
- Downloads currently go to app-private storage. A future version should add Android's Storage Access Framework for choosing a public folder.
- Only download content you own, have permission to download, or that the platform explicitly permits you to download. Follow applicable laws and site terms.
