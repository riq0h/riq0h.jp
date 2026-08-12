#!/bin/sh
# Screenshots each ogcard.html into og.png, skipping cards whose content is
# unchanged since the last deploy.
#
# The skip relies on the deploy step's rsync NOT passing --delete: a card we
# choose not to regenerate simply isn't in this build's output, and the copy
# already on the server survives. Adding `delete: true` to the deploy settings
# in .woodpecker.yml would silently wipe every skipped card.
set -eu

PUBLIC_DIR="public"
PORT=8080
FALLBACK_PNG="themes/tangentline/images/ogp-fallback.png"
FAIL_SENTINEL="/tmp/og-failed-sentinel"
SCRIPT_DIR=$(dirname "$0")
rm -f "$FAIL_SENTINEL"

# Maps each card's path to the sha256 of the ogcard.html that produced its
# current og.png. Deployed alongside the images and read back from the live
# site on the next build.
SITE_URL="${SITE_URL:-https://riq0h.jp}"
MANIFEST_NAME="og-manifest.txt"
MANIFEST_OUT="$PUBLIC_DIR/$MANIFEST_NAME"
MANIFEST_PREV="/tmp/og-manifest-prev.txt"
CARRIED="/tmp/og-carried.txt"
RESULTS="/tmp/og-results.txt"
: > "$CARRIED"
: > "$RESULTS"

if wget -q -O "$MANIFEST_PREV" "$SITE_URL/$MANIFEST_NAME" 2>/dev/null; then
  echo "manifest: $(wc -l < "$MANIFEST_PREV" | tr -d ' ') entries fetched from $SITE_URL" >&2
else
  : > "$MANIFEST_PREV"
  echo "manifest: not available; every card will be regenerated" >&2
fi

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
      continue
      ;;
  esac

  card_hash=$(sha256sum "$f" | cut -d' ' -f1)
  # Match the path column exactly. A substring search would let the home
  # page's card (/ogcard.html) match every post's line, since each of those
  # ends with that same string — so it never matched its own entry and was
  # re-rendered on every build. rel is passed through the environment rather
  # than awk -v, which would interpret backslash escapes in the value.
  prev_hash=$(rel="$rel" awk -F'\t' '$1 == ENVIRON["rel"] { print $2; exit }' "$MANIFEST_PREV")
  if [ "$prev_hash" = "$card_hash" ]; then
    # Unchanged: leave the deployed og.png alone by producing nothing for it,
    # and carry its manifest entry forward so the skip holds next time too.
    printf '%s\t%s\n' "$rel" "$card_hash" >> "$CARRIED"
    rm -f "$f"
  else
    echo "$f" >> /tmp/og-ogcard-todo.txt
  fi
done < /tmp/og-ogcard-list.txt

skipped=$(wc -l < "$CARRIED" | tr -d ' ')
todo=$(wc -l < /tmp/og-ogcard-todo.txt | tr -d ' ')
echo "cards: $todo to render, $skipped unchanged" >&2

# Each screenshot is an independent chromium invocation with no shared state,
# so they fan out across the available cores instead of running one at a time.
JOBS=$(nproc)
xargs -P "$JOBS" -I{} sh "$SCRIPT_DIR/og-worker.sh" {} "$PORT" "$PUBLIC_DIR" "$FALLBACK_PNG" "$FAIL_SENTINEL" "$RESULTS" \
  < /tmp/og-ogcard-todo.txt

# Cards that failed appear in neither file, so they drop out of the manifest
# and are retried on the next build. Cards whose article was deleted drop out
# too, since only ogcard.html files present in this build are considered.
sort -u "$CARRIED" "$RESULTS" > "$MANIFEST_OUT"
echo "manifest: $(wc -l < "$MANIFEST_OUT" | tr -d ' ') entries written to $MANIFEST_NAME" >&2

if [ -f "$FAIL_SENTINEL" ]; then
  echo "One or more OGP screenshots failed; static fallback image was used." >&2
  exit 1
fi
exit 0
