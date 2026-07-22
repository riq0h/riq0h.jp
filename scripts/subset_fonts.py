#!/usr/bin/env python3
"""Generate per-post and shared Noto Serif/Sans JP subsets for public/.

Post pages (single articles) each get their own tight subset covering only
the characters that page actually renders. Every other page (home, section,
taxonomy, term, pagination, 404) shares one subset built from the union of
their own visible text, served from the site root.

Per-post subsetting is CPU-bound and independent across posts, so it runs
across a worker pool. Workers are forked after each master font is parsed
once in the main process, so every worker inherits the already-decompiled
TTFont via copy-on-write instead of re-parsing the ~10-15MB source font
from disk for each of the 256 posts.
"""
import copy
import glob
import html
import multiprocessing
import os
import re
import sys
import urllib.request

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

PUBLIC_DIR = "public"

FONT_SOURCES = {
    "serif": "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifjp/NotoSerifJP%5Bwght%5D.ttf",
    "sans": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf",
}

# ASCII printable range as a baseline safety net, independent of extraction.
BASE_CHARS = {chr(c) for c in range(0x20, 0x7F)}

POST_PATH_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/\d{6}/index\.html$")
STRIP_RE = re.compile(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<[^>]+>", re.DOTALL)

# Populated once per worker process (via fork, so this is inherited from the
# parent's already-parsed state rather than re-read/re-parsed per task).
_MASTER_FONTS = {}

# fontTools' default layout_features already covers kern/liga/ccmp/vert etc.;
# "*" (retain every GSUB/GPOS feature) costs ~25% extra subsetting time for
# no visible benefit here. "palt" is added explicitly for forward
# compatibility even though neither the self-hosted nor the bunny.net-served
# Noto Serif/Sans JP currently exposes it (main.css's font-feature-settings:
# "palt" is a pre-existing no-op either way, confirmed against both sources).
_LAYOUT_FEATURES = Options().layout_features + ["palt"]


def extract_chars(html_path):
    with open(html_path, encoding="utf-8") as f:
        raw = f.read()
    text = html.unescape(STRIP_RE.sub(" ", raw))
    return {ch for ch in text if not ch.isspace()}


def subset_from_master(master_font, chars, out_path):
    font = copy.deepcopy(master_font)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = _LAYOUT_FEATURES
    subsetter = Subsetter(options=opts)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    font.save(out_path)


def subset_post(args):
    html_path, sources = args
    chars = extract_chars(html_path) | BASE_CHARS
    out_dir = os.path.dirname(html_path)
    for name in sources:
        subset_from_master(_MASTER_FONTS[name], chars, f"{out_dir}/font-{name}.woff2")
    return html_path


def _init_worker(sources):
    # Runs once per forked worker; parses each master font a single time so
    # subset_post() tasks in this worker never touch the source files again.
    for name, path in sources.items():
        _MASTER_FONTS[name] = TTFont(path)


def main():
    sources = {}
    for name, url in FONT_SOURCES.items():
        local_path = f"/tmp/noto-{name}-source.ttf"
        print(f"downloading {name} source font...", file=sys.stderr)
        urllib.request.urlretrieve(url, local_path)
        sources[name] = local_path

    all_pages = glob.glob(f"{PUBLIC_DIR}/**/index.html", recursive=True)
    post_pages = [p for p in all_pages if POST_PATH_RE.search(p)]
    other_pages = [p for p in all_pages if p not in set(post_pages)]
    print(f"post pages: {len(post_pages)}, other pages: {len(other_pages)}", file=sys.stderr)

    shared_chars = set(BASE_CHARS)
    for p in other_pages:
        shared_chars |= extract_chars(p)
    _init_worker(sources)
    for name in sources:
        subset_from_master(_MASTER_FONTS[name], shared_chars, f"{PUBLIC_DIR}/font-{name}.woff2")
    print(f"shared subset: {len(shared_chars)} chars", file=sys.stderr)

    worker_count = min(len(post_pages) or 1, os.cpu_count() or 1)
    with multiprocessing.Pool(
        processes=worker_count, initializer=_init_worker, initargs=(sources,)
    ) as pool:
        for i, _ in enumerate(pool.imap_unordered(subset_post, ((p, sources) for p in post_pages)), 1):
            if i % 32 == 0 or i == len(post_pages):
                print(f"  {i}/{len(post_pages)} post subsets done", file=sys.stderr)

    print(f"done: {len(post_pages)} post subsets + shared subset generated", file=sys.stderr)


if __name__ == "__main__":
    main()
