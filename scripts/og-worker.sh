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

# A screenshot occasionally fails purely from resource contention on the CI
# host (4 shared cores, already swapping), not from anything wrong with the
# page: a run of 257 cards saw 2 fail with no common factor between them.
# Since any single failure trips the sentinel and fails the whole pipeline —
# which blocks the deploy step entirely — retry before giving up. At the
# observed ~0.8% per-card failure rate, one attempt leaves only a ~13% chance
# of a fully clean run, while three attempts make it effectively certain.
MAX_ATTEMPTS=3

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  # Concurrent chromium invocations must not share a profile dir (the default
  # ~/.config/chromium), or all but one fail to acquire its SingletonLock.
  user_data_dir="/tmp/og-chromium-profile-$$-$attempt"
  # A timed-out attempt can leave a truncated file behind, which would pass
  # the -s check on the next round.
  rm -f "$dir/og.png"

  # Chromium has no GPU here, but it still brings up a GPU process for
  # compositing and lets ANGLE pick a backend for it. On this image's
  # Chromium 151 that lands on Vulkan, which the container cannot provide
  # (no VK_KHR_surface), so the GPU process crashes and respawns in a loop —
  # measured at ~4 crashes per screenshot, 69 across a 16-shot parallel run.
  # Disabling GPU compositing and the software rasterizer keeps that process
  # from starting at all: 0 crashes, and the rendered PNGs are byte-identical
  # (verified by md5 on the CI host). --disable-dev-shm-usage avoids the
  # small default /dev/shm that containers give Chromium.
  if timeout 20 chromium --headless=new --disable-gpu --no-sandbox \
      --user-data-dir="$user_data_dir" \
      --disable-gpu-compositing --disable-software-rasterizer \
      --disable-dev-shm-usage \
      --disable-background-networking --disable-component-update \
      --disable-domain-reliability --disable-sync \
      --disable-client-side-phishing-detection --disable-default-apps \
      --disable-breakpad --no-first-run --metrics-recording-only \
      --window-size=1200,630 --virtual-time-budget=1500 \
      --screenshot="$dir/og.png" "$url" >"$chromium_log" 2>&1 \
     && [ -s "$dir/og.png" ]; then
    rm -rf "$user_data_dir"
    break
  fi
  rm -rf "$user_data_dir"

  if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
    echo "WARN: OGP screenshot attempt $attempt/$MAX_ATTEMPTS failed for $url; retrying" >&2
    # Back off so a contention spike has a chance to pass before retrying.
    sleep $((attempt * 2))
  else
    echo "WARN: OGP screenshot failed for $url after $MAX_ATTEMPTS attempts" >&2
    cat "$chromium_log" >&2
    cp "$FALLBACK_PNG" "$dir/og.png"
    touch "$FAIL_SENTINEL"
  fi
  attempt=$((attempt + 1))
done
rm -f "$chromium_log"

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
