#!/bin/sh
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out="${PEAR_PREVIEW_BUILD_ROOT:-$repo/.build/task47/preview}"
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$repo/.build/task47/preview/cargo}"
export MACOSX_DEPLOYMENT_TARGET=15.0
sparkle="${PEAR_SPARKLE_ROOT:-$repo/.build/task62/admitted}"
test -f "$sparkle/admission.json" || { echo 'Admit Sparkle with preview/sparkle_input.py before building.' >&2; exit 1; }
cargo test --manifest-path "$repo/preview/Cargo.toml" --locked --offline
cargo build --manifest-path "$repo/preview/Cargo.toml" --locked --offline --release
app="$out/Pear.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources" "$app/Contents/Frameworks"
# Copy only the admitted public framework; preserve its upstream internal links.
/usr/bin/ditto "$sparkle/Sparkle.framework" "$app/Contents/Frameworks/Sparkle.framework"
mkdir -p "$app/Contents/Resources/licenses"
cp "$sparkle/LICENSE" "$app/Contents/Resources/licenses/Sparkle.txt"
cp "$repo/docs/assets/pear.png" "$app/Contents/Resources/PearMark.png"
sh "$repo/preview/build-icon.sh" "$app/Contents/Resources/Pear.icns"
cp "$CARGO_TARGET_DIR/release/pear-preview" "$app/Contents/Resources/pear-preview"
if [ -f "$repo/LICENSE" ]; then cp "$repo/LICENSE" "$app/Contents/Resources/LICENSE"; fi
if [ -d "$repo/preview/licenses" ]; then cp -R "$repo/preview/licenses" "$app/Contents/Resources/"; fi
if [ -f "$repo/preview/THIRD_PARTY_NOTICES.md" ]; then cp "$repo/preview/THIRD_PARTY_NOTICES.md" "$app/Contents/Resources/"; fi
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/UpdateLaunchPolicy.swift" "$repo/preview/test_update_launch_policy.swift" -o "$out/update-policy-tests"
"$out/update-policy-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/UpdateEnvironment.swift" "$repo/preview/test_update_environment.swift" -o "$out/update-environment-tests"
"$out/update-environment-tests"
xcrun swiftc -target arm64-apple-macosx15.0 -F "$sparkle" -framework Sparkle -Xlinker -rpath -Xlinker "$sparkle" "$repo/preview/UpdateLaunchPolicy.swift" "$repo/preview/UpdateEnvironment.swift" "$repo/preview/UpdateReleaseNotes.swift" "$repo/preview/SparkleUpdate.swift" "$repo/preview/test_sparkle_adapter.swift" -o "$out/sparkle-adapter-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/UpdateReleaseNotes.swift" "$repo/preview/test_update_notes.swift" -o "$out/update-notes-tests"
"$out/update-notes-tests"
"$out/sparkle-adapter-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/test_reporting_policy.swift" -o "$out/reporting-policy-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/test_reporting_store.swift" -o "$out/reporting-store-tests"
"$out/reporting-store-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/ReportingTransport.swift" "$repo/preview/test_reporting_transport.swift" -o "$out/reporting-transport-tests"
"$out/reporting-transport-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/RunObserver.swift" "$repo/preview/test_run_observer.swift" -o "$out/run-observer-tests"
"$out/run-observer-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/ReportingPolicy.swift" "$repo/preview/RunObserver.swift" "$repo/preview/test_run_observer_host.swift" -o "$out/run-observer-host-tests"
"$out/run-observer-host-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/Presentation.swift" "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/RunObserver.swift" "$repo/preview/test_first_install.swift" -o "$out/first-install-tests"
"$out/first-install-tests" "$app/Contents/Resources/pear-preview"
"$out/reporting-policy-tests"
xcrun swiftc -target arm64-apple-macosx15.0 "$repo/preview/Presentation.swift" "$repo/preview/test_presentation.swift" -o "$out/presentation-tests"
"$out/presentation-tests"
xcrun swiftc -O -target arm64-apple-macosx15.0 -F "$sparkle" -framework Sparkle -Xlinker -rpath -Xlinker @executable_path/../Frameworks "$repo/preview/UpdateLaunchPolicy.swift" "$repo/preview/UpdateEnvironment.swift" "$repo/preview/UpdateReleaseNotes.swift" "$repo/preview/SparkleUpdate.swift" "$repo/preview/AppStyle.swift" "$repo/preview/Presentation.swift" "$repo/preview/SteamWindow.swift" "$repo/preview/ReportingPolicy.swift" "$repo/preview/ReportingStore.swift" "$repo/preview/ReportingTransport.swift" "$repo/preview/HistoryWindow.swift" "$repo/preview/RunObserver.swift" "$repo/preview/Launcher.swift" -o "$app/Contents/MacOS/PearPreview"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>org.pear.rosetta-preview</string>
<key>CFBundleName</key><string>Pear</string>
<key>CFBundleDisplayName</key><string>Pear</string>
<key>CFBundleIconFile</key><string>Pear.icns</string>
<key>CFBundleExecutable</key><string>PearPreview</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>5</string>
<key>CFBundleShortVersionString</key><string>0.1.1</string>
<key>LSMinimumSystemVersion</key><string>15.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
python3 -B "$repo/preview/configure_update.py" "$app/Contents/Info.plist"
# Release signing is explicit; local builds remain ad hoc development artifacts.
if [ -n "${PEAR_SIGNING_IDENTITY:-}" ]; then
    python3 -B "$repo/preview/sign_sparkle.py" "$app/Contents/Frameworks/Sparkle.framework" "$PEAR_SIGNING_IDENTITY"
    /usr/bin/codesign --force --options runtime --timestamp --sign "$PEAR_SIGNING_IDENTITY" "$app/Contents/Resources/pear-preview"
    /usr/bin/codesign --force --options runtime --timestamp --sign "$PEAR_SIGNING_IDENTITY" "$app"
else
    /usr/bin/codesign --force --sign - "$app"
fi
/usr/bin/codesign --verify --deep --strict "$app"
# Signature verification alone is not notarization or ordinary-user qualification.
printf '%s\n' "CLI: $CARGO_TARGET_DIR/release/pear-preview" "App: $app"
