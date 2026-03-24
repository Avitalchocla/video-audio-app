[app]

title = Video Audio Replacer
package.name = videoaudioreplacer
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,so,bin
version = 0.1
requirements = python3,kivy,android,pyjnius,requests,urllib3,chardet,certifi,idna
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.arch = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.debug_artifact = apk
android.add_assets = assets/ffmpeg:ffmpeg,assets/NotoSansHebrew.ttf:NotoSansHebrew.ttf

[buildozer]
log_level = 2
warn_on_root = 1
