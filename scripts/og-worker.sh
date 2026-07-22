#!/bin/sh
# Handles a single ogcard.html -> og.png conversion. Split out from
# generate-og-images.sh so it can run under `xargs -P` for parallel
# screenshotting; see that script for the orchestration side.
set -eu

f="$1"
PORT="$2"
PUBLIC_DIR="$3"
FALLBACK_PNG="$4"
FAIL_SENTINEL="$5"

dir=$(dirname "$f")
rel=${f#"$PUBLIC_DIR"}
url="http://localhost:$PORT${rel}"

chromium_log="/tmp/og-chromium-$$.log"
magick_log="/tmp/og-magick-$$.log"
# Concurrent chromium invocations must not share a profile dir (the default
# ~/.config/chromium), or all but one fail to acquire its SingletonLock.
user_data_dir="/tmp/og-chromium-profile-$$"

if timeout 20 chromium --headless=new --disable-gpu --no-sandbox \
    --user-data-dir="$user_data_dir" \
    --disable-background-networking --disable-component-update \
    --disable-domain-reliability --disable-sync \
    --disable-client-side-phishing-detection --disable-default-apps \
    --disable-breakpad --no-first-run --metrics-recording-only \
    --window-size=1200,630 --virtual-time-budget=1500 \
    --screenshot="$dir/og.png" "$url" >"$chromium_log" 2>&1 \
   && [ -s "$dir/og.png" ]; then
  :
else
  echo "WARN: OGP screenshot failed for $url" >&2
  cat "$chromium_log" >&2
  cp "$FALLBACK_PNG" "$dir/og.png"
  touch "$FAIL_SENTINEL"
fi
rm -f "$chromium_log"
rm -rf "$user_data_dir"

# Twitter/X re-encodes opaque PNGs to lossy JPEG, which introduces visible
# artifacts on this design's thin lines and hairline rule. A PNG with any
# alpha channel is kept as-is, so nudge one corner pixel to 99% opacity
# (imperceptible) purely to keep the PNG format on that platform. og.png is
# already valid at this point either way, so a failure here is a warning,
# not a build failure.
if ! magick "$dir/og.png" -alpha set -channel A -fx "(i==0&&j==0)?0.99:1" "PNG32:$dir/og.png" 2>"$magick_log"; then
  echo "WARN: alpha-pixel post-processing failed for $dir/og.png (kept as-is)" >&2
  cat "$magick_log" >&2
fi
rm -f "$magick_log"

rm -f "$f"
