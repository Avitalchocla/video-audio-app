#!/bin/bash

echo "🎬 Setting up Video Audio Replacer..."

# Create directories
mkdir -p .github/workflows
mkdir -p assets

# Create .gitkeep
touch assets/.gitkeep

# Create buildozer.spec
cat > buildozer.spec << 'EOF'
[app]
title = Video Audio Replacer
package.name = videoaudioreplacer
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,so,bin
source.include_patterns = assets/*,*.py,*.kv
source.exclude_exts = spec
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
android.release_artifact = aab
android.debug_artifact = apk
android.add_assets = assets/ffmpeg:ffmpeg,assets/NotoSansHebrew.ttf:NotoSansHebrew.ttf

[buildozer]
log_level = 2
warn_on_root = 1
EOF

# Create GitHub Action
cat > .github/workflows/build.yml << 'EOF'
name: Build APK

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04
    
    steps:
      - name: 📥 Checkout repository
        uses: actions/checkout@v4

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: ☕ Setup Java 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: 🤖 Setup Android SDK
        uses: android-actions/setup-android@v3

      - name: ⚙️ Install system dependencies
        run: |
          sudo apt update
          sudo apt install -y \
            git zip unzip python3-pip autoconf automake libtool pkg-config \
            zlib1g-dev libncurses5 libncursesw5 cmake libffi-dev libssl-dev \
            patch python3-setuptools build-essential wget file libltdl-dev
          pip install --upgrade pip
          pip install buildozer cython==0.29.33

      - name: 📥 Download FFmpeg and Font to assets
        run: |
          mkdir -p assets
          echo "Downloading FFmpeg..."
          wget --no-check-certificate \
            'https://docs.google.com/uc?export=download&id=1rKA5Lb0vDMy6CKJClhFT8JIAGUh3icfs' \
            -O assets/ffmpeg
          chmod +x assets/ffmpeg
          echo "Downloading Hebrew font..."
          wget -q \
            'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf' \
            -O assets/NotoSansHebrew.ttf || \
          wget -q \
            'https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf' \
            -O assets/NotoSansHebrew.ttf
          echo "Assets downloaded:"
          ls -la assets/

      - name: 🛠️ Build APK with Buildozer
        run: |
          yes | sdkmanager --licenses || true
          rm -rf .buildozer bin/
          export GRADLE_OPTS="-Dorg.gradle.jvmargs=-Xmx4096m -Dorg.gradle.daemon=false"
          export JAVA_OPTS="-Xmx4096m"
          buildozer -v android debug 2>&1 | tee build.log
          echo "Build completed. Checking for APK..."
          ls -la bin/ || echo "No bin directory found"
          find . -name "*.apk" -type f 2>/dev/null || echo "No APK found"

      - name: 📤 Upload APK Artifact
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: VideoAudioReplacer-APK
          path: |
            bin/*.apk
            bin/**/*.apk
          if-no-files-found: warn
          retention-days: 7

      - name: 📋 Upload build logs on failure
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: build-logs
          path: |
            build.log
            .buildozer/android/platform/build-*/build.log
          if-no-files-found: ignore
          retention-days: 3
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Buildozer
/bin/
/.buildozer/
*.apk
*.aab
*.keystore
*.jks

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.log
assets/ffmpeg
assets/*.ttf
!assets/.gitkeep
EOF

# Create README
cat > README.md << 'EOF'
# Video Audio Replacer

אפליקציית אנדרואיד להחלפת אודיו בסרטונים והוספת כתוביות בעברית.

## תכונות
- ✅ החלפת אודיו בסרטון
- ✅ הוספת כתוביות בעברית
- ✅ עורך תזמון עם תצוגה מקדימה
- ✅ גרירה לשינוי סדר כתוביות

## בנייה
ה-APK נבנה אוטומטית ב-GitHub Actions.
EOF

echo "✅ All files created!"
echo ""
echo "📁 Structure:"
tree -L 3 -a || ls -la
echo ""
echo "🚀 Next steps:"
echo "1. Update the Google Drive ID in .github/workflows/build.yml"
echo "2. git add ."
echo "3. git commit -m 'Initial commit'"
echo "4. git push"
echo "5. Go to GitHub → Actions → Build APK → Run workflow"