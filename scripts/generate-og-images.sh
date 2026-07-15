#!/bin/sh
set -eu

PUBLIC_DIR="public"
PORT=8080
FALLBACK_PNG="themes/tangentline/images/ogp-fallback.png"

python3 -m http.server "$PORT" --directory "$PUBLIC_DIR" >/tmp/og-http-server.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

for i in $(seq 1 30); do
  if wget -q -O /dev/null "http://localhost:$PORT/" 2>/dev/null; then
    break
  fi
  sleep 0.2
done

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
  echo "ERROR: our http.server (pid $SERVER_PID) is not running; port $PORT may already be in use by another process" >&2
  exit 1
fi

find "$PUBLIC_DIR" -name 'ogcard.html' > /tmp/og-ogcard-list.txt

FAILED=0

while IFS= read -r f; do
  dir=$(dirname "$f")
  rel=${f#"$PUBLIC_DIR"}
  case "$rel" in
    */page/*)
      rm -f "$f"
      continue
      ;;
  esac
  url="http://localhost:$PORT${rel}"
  if timeout 20 chromium --headless=new --disable-gpu --no-sandbox \
      --window-size=1200,630 --virtual-time-budget=1500 \
      --screenshot="$dir/og.png" "$url" >/tmp/og-chromium.log 2>&1 \
     && [ -s "$dir/og.png" ]; then
    :
  else
    echo "WARN: OGP screenshot failed for $url" >&2
    cat /tmp/og-chromium.log >&2
    cp "$FALLBACK_PNG" "$dir/og.png"
    FAILED=1
  fi
  rm -f "$f"
done < /tmp/og-ogcard-list.txt

if [ "$FAILED" -eq 1 ]; then
  echo "One or more OGP screenshots failed; static fallback image was used." >&2
  exit 1
fi
exit 0
