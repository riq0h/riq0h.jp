#!/usr/bin/env python3
"""Generate per-post and shared Noto Serif/Sans JP subsets for public/.

Post pages (single articles) each get their own tight subset covering only
the characters that page actually renders. Every other page (home, section,
taxonomy, term, pagination, 404) shares one subset built from the union of
their own visible text, served from the site root.
"""
import glob
import html
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


def extract_chars(html_path):
    with open(html_path, encoding="utf-8") as f:
        raw = f.read()
    text = html.unescape(STRIP_RE.sub(" ", raw))
    return {ch for ch in text if not ch.isspace()}


def subset_font(src_font_path, chars, out_path):
    font = TTFont(src_font_path)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    subsetter = Subsetter(options=opts)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    font.save(out_path)


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
    for name, src in sources.items():
        subset_font(src, shared_chars, f"{PUBLIC_DIR}/font-{name}.woff2")
    print(f"shared subset: {len(shared_chars)} chars", file=sys.stderr)

    for p in post_pages:
        chars = extract_chars(p) | BASE_CHARS
        out_dir = os.path.dirname(p)
        for name, src in sources.items():
            subset_font(src, chars, f"{out_dir}/font-{name}.woff2")

    print(f"done: {len(post_pages)} post subsets + shared subset generated", file=sys.stderr)


if __name__ == "__main__":
    main()
