#!/bin/sh
# Convert the requester-supplied app artwork with macOS tools; do not redraw it.
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ "$#" -ne 1 ]; then
    printf '%s\n' 'Usage: sh preview/build-icon.sh OUTPUT.icns' >&2
    exit 2
fi
scratch=$(mktemp -d "${TMPDIR:-/tmp}/pear-icon.XXXXXX")
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
iconset="$scratch/Pear.iconset"
mkdir -p "$iconset"
for size in 16 32 128 256 512; do
    /usr/bin/sips -z "$size" "$size" "$repo/preview/assets/pear_icon.png" --out "$iconset/icon_${size}x${size}.png" >/dev/null
    doubled=$((size * 2))
    /usr/bin/sips -z "$doubled" "$doubled" "$repo/preview/assets/pear_icon.png" --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
done
/usr/bin/iconutil -c icns "$iconset" -o "$1"
