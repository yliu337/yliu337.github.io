#!/bin/bash
# Render tools/og_image.html to og-image.png (1200x630) with headless Chrome.
cd "$(dirname "$0")/.." || exit 1
TMP=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --user-data-dir="$TMP/profile" --allow-file-access-from-files --force-device-scale-factor=1 \
  --window-size=1200,630 --screenshot="$TMP/og.png" "file://$PWD/tools/og_image.html" 2>/dev/null
sips -g pixelWidth -g pixelHeight "$TMP/og.png" | tail -2
mv "$TMP/og.png" og-image.png && rm -rf "$TMP"
