#!/bin/sh
# Builds the site and generates the same self-hosted font subsets CI
# produces (scripts/subset_fonts.py doesn't run under `hugo server`, only
# against a built public/), then serves the result so it can be compared
# against production like-for-like. Requires docker.
set -eu

PORT="${1:-8000}"

DOCKER="docker"
if ! docker info >/dev/null 2>&1; then
  DOCKER="sudo docker"
fi

hugo --destination public

$DOCKER run --rm \
  -v "$(pwd)/public:/drone/src/public" \
  -v "$(pwd)/scripts:/drone/src/scripts:ro" \
  -w /drone/src \
  hugomods/hugo:base sh -c "
    apk add --no-cache python3 py3-pip curl >/dev/null 2>&1
    pip install --break-system-packages --quiet fonttools brotli >/dev/null 2>&1
    python3 ./scripts/fix_cjk_breaks.py
    python3 ./scripts/subset_fonts.py
  "

echo "Serving public/ at http://localhost:${PORT}/ (Ctrl+C to stop)"
python3 -m http.server "$PORT" --directory public
