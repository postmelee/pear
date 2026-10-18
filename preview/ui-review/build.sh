#!/bin/bash
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
out="$repo/.build/task63-ui"
app="$out/Pear UI Review.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
cp "$repo/docs/assets/pear.png" "$app/Contents/Resources/PearMark.png"
# Small app-only build. No installed application, runtime or authenticated prefix copy.
sources=(AppStyle Presentation SteamWindow ReportingPolicy ReportingStore ReportingTransport HistoryWindow RunObserver Launcher)
args=()
for source in "${sources[@]}"; do args+=("$repo/preview/$source.swift"); done
xcrun swiftc -O -D PEAR_UI_REVIEW -target arm64-apple-macosx15.0 "${args[@]}" "$repo/preview/ui-review/Main.swift" -o "$app/Contents/MacOS/PearUIReview"
cp "$repo/preview/assets/pear_icon.png" "$app/Contents/Resources/Pear.png"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>PearUIReview</string><key>CFBundleIdentifier</key><string>org.pear.ui-review</string>
<key>CFBundleName</key><string>Pear UI Review</string><key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleIconFile</key><string>Pear.png</string><key>LSMinimumSystemVersion</key><string>15.0</string>
</dict></plist>
PLIST
codesign --force --sign - "$app"
printf '%s\n' "$app"
