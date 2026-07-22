#!/bin/sh
set -eu

PUBLIC_DIR="public"
PORT=8080
FALLBACK_PNG="themes/tangentline/images/ogp-fallback.png"
FAIL_SENTINEL="/tmp/og-failed-sentinel"
SCRIPT_DIR=$(dirname "$0")
rm -f "$FAIL_SENTINEL"

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

: > /tmp/og-ogcard-todo.txt
while IFS= read -r f; do
  rel=${f#"$PUBLIC_DIR"}
  case "$rel" in
    */page/*)
      rm -f "$f"
      ;;
    *)
      echo "$f" >> /tmp/og-ogcard-todo.txt
      ;;
  esac
done < /tmp/og-ogcard-list.txt

# Each screenshot is an independent chromium invocation with no shared state,
# so they fan out across the available cores instead of running one at a time.
JOBS=$(nproc)
xargs -P "$JOBS" -I{} sh "$SCRIPT_DIR/og-worker.sh" {} "$PORT" "$PUBLIC_DIR" "$FALLBACK_PNG" "$FAIL_SENTINEL" \
  < /tmp/og-ogcard-todo.txt

if [ -f "$FAIL_SENTINEL" ]; then
  echo "One or more OGP screenshots failed; static fallback image was used." >&2
  exit 1
fi
exit 0
