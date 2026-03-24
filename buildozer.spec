[app]

# (str) Title of your application
title = Video Audio Replacer

# (str) Package name
package.name = videoaudioreplacer

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,so,bin

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,*.py,*.kv

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,android,pyjnius,requests,urllib3,chardet,certifi,idna

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# Android specific
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (str) Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (list) Android additional libraries to copy (libs armeabi-v7a, arm64-v8a, x86, x86_64)
android.add_libs_arm64_v8a =

# (list) Android AAB configuration
android.archs = arm64-v8a, armeabi-v7a

# (str) format used to package the app for release mode (aab or apk or aar).
android.release_artifact = aab

# (str) format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

# (list) Android additional assets to copy
android.add_assets = assets/ffmpeg:ffmpeg,assets/NotoSansHebrew.ttf:NotoSansHebrew.ttf

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1