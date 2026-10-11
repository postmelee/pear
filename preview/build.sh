#!/bin/sh
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out="${PEAR_PREVIEW_BUILD_ROOT:-$repo/.build/task47/preview}"
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$repo/.build/task47/preview/cargo}"
export MACOSX_DEPLOYMENT_TARGET=26.0
cargo test --manifest-path "$repo/preview/Cargo.toml" --locked --offline
cargo build --manifest-path "$repo/preview/Cargo.toml" --locked --offline --release
app="$out/Pear Preview.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
sh "$repo/preview/build-icon.sh" "$app/Contents/Resources/Pear.icns"
cp "$CARGO_TARGET_DIR/release/pear-preview" "$app/Contents/Resources/pear-preview"
if [ -f "$repo/LICENSE" ]; then cp "$repo/LICENSE" "$app/Contents/Resources/LICENSE"; fi
if [ -d "$repo/preview/licenses" ]; then cp -R "$repo/preview/licenses" "$app/Contents/Resources/"; fi
if [ -f "$repo/preview/THIRD_PARTY_NOTICES.md" ]; then cp "$repo/preview/THIRD_PARTY_NOTICES.md" "$app/Contents/Resources/"; fi
xcrun swiftc -O -target arm64-apple-macosx26.0 "$repo/preview/Launcher.swift" -o "$app/Contents/MacOS/PearPreview"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>org.pear.rosetta-preview</string>
<key>CFBundleName</key><string>Pear Preview</string>
<key>CFBundleIconFile</key><string>Pear.icns</string>
<key>CFBundleExecutable</key><string>PearPreview</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>LSMinimumSystemVersion</key><string>26.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
# Release signing is explicit; local builds remain ad hoc development artifacts.
if [ -n "${PEAR_SIGNING_IDENTITY:-}" ]; then
    /usr/bin/codesign --force --options runtime --timestamp --sign "$PEAR_SIGNING_IDENTITY" "$app/Contents/Resources/pear-preview"
    /usr/bin/codesign --force --options runtime --timestamp --sign "$PEAR_SIGNING_IDENTITY" "$app"
else
    /usr/bin/codesign --force --sign - "$app"
fi
/usr/bin/codesign --verify --deep --strict "$app"
# Signature verification alone is not notarization or ordinary-user qualification.
printf '%s\n' "CLI: $CARGO_TARGET_DIR/release/pear-preview" "App: $app"
