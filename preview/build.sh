#!/bin/sh
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out="${PEAR_PREVIEW_BUILD_ROOT:-$repo/.build/task47/preview}"
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$repo/.build/task47/preview/cargo}"
export MACOSX_DEPLOYMENT_TARGET=15.0
cargo test --manifest-path "$repo/preview/Cargo.toml" --locked --offline
cargo build --manifest-path "$repo/preview/Cargo.toml" --locked --offline --release
app="$out/Pear.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
sh "$repo/preview/build-icon.sh" "$app/Contents/Resources/Pear.icns"
cp "$CARGO_TARGET_DIR/release/pear-preview" "$app/Contents/Resources/pear-preview"
if [ -f "$repo/LICENSE" ]; then cp "$repo/LICENSE" "$app/Contents/Resources/LICENSE"; fi
if [ -d "$repo/preview/licenses" ]; then cp -R "$repo/preview/licenses" "$app/Contents/Resources/"; fi
if [ -f "$repo/preview/THIRD_PARTY_NOTICES.md" ]; then cp "$repo/preview/THIRD_PARTY_NOTICES.md" "$app/Contents/Resources/"; fi
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/test_reporting_policy.swift" -o "$out/reporting-policy-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/test_reporting_store.swift" -o "$out/reporting-store-tests"
"$out/reporting-store-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/ReportingTransport.swift" "$repo/preview/test_reporting_transport.swift" -o "$out/reporting-transport-tests"
"$out/reporting-transport-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/RunObserver.swift" "$repo/preview/test_run_observer.swift" -o "$out/run-observer-tests"
"$out/run-observer-tests"
"$out/reporting-policy-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/Presentation.swift" "$repo/preview/test_presentation.swift" -o "$out/presentation-tests"
"$out/presentation-tests"
xcrun swiftc -O -target arm64-apple-macosx15.0 "$repo/preview/Presentation.swift" "$repo/preview/SteamWindow.swift" "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/ReportingTransport.swift" "$repo/preview/HistoryWindow.swift" "$repo/preview/RunObserver.swift" "$repo/preview/Launcher.swift" -o "$app/Contents/MacOS/PearPreview"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>org.pear.rosetta-preview</string>
<key>CFBundleName</key><string>Pear</string>
<key>CFBundleDisplayName</key><string>Pear</string>
<key>CFBundleIconFile</key><string>Pear.icns</string>
<key>CFBundleExecutable</key><string>PearPreview</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>5</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>LSMinimumSystemVersion</key><string>15.0</string>
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
