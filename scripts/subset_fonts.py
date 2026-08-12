#!/usr/bin/env python3
"""Generate per-post and shared Noto Serif/Sans JP subsets for public/.

Post pages (single articles) each get their own tight subset covering only
the characters that page actually renders. Every other page (home, section,
taxonomy, term, pagination, 404) shares one subset built from the union of
their own visible text, served from the site root.

Each generated font is saved under a filename that embeds a short hash of
its own bytes (font-serif.<hash>.woff2), and every HTML file referencing it
(index.html, and its sibling ogcard.html if present) is rewritten to point
at that hashed name. Any change to a page's content, the subsetting logic,
or the upstream master font changes the hash, so CDN/browser caches can be
set to cache these indefinitely without ever serving a stale font.

Per-post subsetting is CPU-bound and independent across posts, so it runs
across a worker pool. Workers are forked after each master font is parsed
once in the main process, so every worker inherits the already-decompiled
TTFont via copy-on-write instead of re-parsing the ~10-15MB source font
from disk for each of the 256 posts.
"""
import copy
import glob
import hashlib
import html
import io
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
# no visible benefit here. "palt" is added explicitly since Noto Serif/Sans
# JP both implement it (confirmed via direct GPOS inspection).
_LAYOUT_FEATURES = Options().layout_features + ["palt"]


def extract_chars(html_path):
    with open(html_path, encoding="utf-8") as f:
        raw = f.read()
    text = html.unescape(STRIP_RE.sub(" ", raw))
    return {ch for ch in text if not ch.isspace()}


def subset_from_master(master_font, chars, out_dir, name):
    font = copy.deepcopy(master_font)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = _LAYOUT_FEATURES
    subsetter = Subsetter(options=opts)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    digest = hashlib.sha256(data).hexdigest()[:8]
    filename = f"font-{name}.{digest}.woff2"
    with open(f"{out_dir}/{filename}", "wb") as f:
        f.write(data)
    return filename


def rewrite_font_refs(html_path, hashed_names):
    with open(html_path, encoding="utf-8") as f:
        content = f.read()
    original = content
    for name, filename in hashed_names.items():
        content = content.replace(f"font-{name}.woff2", filename)
    if content != original:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)


def rewrite_sibling_ogcard(html_path, hashed_names):
    ogcard_path = os.path.join(os.path.dirname(html_path), "ogcard.html")
    if os.path.exists(ogcard_path):
        rewrite_font_refs(ogcard_path, hashed_names)


def subset_post(args):
    html_path, sources = args
    chars = extract_chars(html_path) | BASE_CHARS
    out_dir = os.path.dirname(html_path)
    hashed_names = {
        name: subset_from_master(_MASTER_FONTS[name], chars, out_dir, name)
        for name in sources
    }
    rewrite_font_refs(html_path, hashed_names)
    rewrite_sibling_ogcard(html_path, hashed_names)
    return html_path


def _init_worker(sources):
    # Runs once per forked worker; parses each master font a single time so
    # subset_post() tasks in this worker never touch the source files again.
    #
    # recalcTimestamp=False is what makes the output reproducible: fontTools
    # otherwise stamps head.modified with the current time on save, so every
    # build would emit different bytes for identical input. That would give
    # each font a new hash — and therefore a new filename and a rewritten
    # ogcard.html — on every single build, defeating both the long-lived CDN
    # cache and the OGP manifest's ability to skip unchanged cards.
    for name, path in sources.items():
        _MASTER_FONTS[name] = TTFont(path, recalcTimestamp=False)


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
    shared_hashed_names = {
        name: subset_from_master(_MASTER_FONTS[name], shared_chars, PUBLIC_DIR, name)
        for name in sources
    }
    print(f"shared subset: {len(shared_chars)} chars", file=sys.stderr)

    for p in other_pages:
        rewrite_font_refs(p, shared_hashed_names)
        rewrite_sibling_ogcard(p, shared_hashed_names)

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
