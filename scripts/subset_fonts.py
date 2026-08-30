#!/usr/bin/env python3
"""Generate per-post and shared font subsets for public/.

Two typefaces share each page, split by weight rather than by role. BIZ UDP
Mincho/Gothic ships only 400 and 700, so everything drawn at those weights
uses it: the article text, the excerpts, h3-h6, dates, tags, the pager and
the footer. What is left for Noto Serif/Sans JP is what needs weight 300 --
the masthead, article titles, h2 and taxonomy titles. Splitting the page's
characters along that same line means neither family carries glyphs the
other renders.

The split must track main.css exactly. If a rule moves between the two
families and this file is not updated, the characters it draws end up only
in the other family's subset; the browser then falls back per glyph and a
single word renders in two typefaces. Local development hides this, because
the @font-face rules list local() first and a machine with BIZ UDP installed
resolves every character regardless of what shipped.

BIZ UDP covers JIS X 0208 and X 0213 in full, so no Japanese ever falls
through it. What it lacks -- emoji, Devanagari, Thai, simplified-only
hanzi -- is folded back into the Noto subsets so those characters still
have a webfont to land on instead of dropping to a system face.

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
TTFont via copy-on-write instead of re-parsing the source fonts from disk
for each of the 256 posts.
"""
import copy
import glob
import hashlib
import html
import io
import multiprocessing
import os
import re
import shutil
import sys
import time
import urllib.request
import zipfile
from html.parser import HTMLParser

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

PUBLIC_DIR = "public"

_GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"

# UDEV Gothic ships only as a release archive, so its four faces are pulled
# from one download. Pinning the version keeps the build reproducible; bump
# both constants together.
_UDEV_VER = "v2.2.0"
_UDEV_ZIP = (
    f"https://github.com/yuru7/udev-gothic/releases/download/{_UDEV_VER}"
    f"/UDEVGothic_NF_{_UDEV_VER}.zip"
)
_UDEV_DIR = f"UDEVGothic_NF_{_UDEV_VER}"

# name -> (source URL, character bucket it must cover, archive member or None).
#
# "chrome" fonts also absorb any body character the BIZ UDP masters cannot
# render; see subset_targets(). Code needs all four mono faces because the
# Chroma theme sets bold and italic independently and together (.nc/.nb).
FONT_SOURCES = {
    "serif":           (f"{_GF}/notoserifjp/NotoSerifJP%5Bwght%5D.ttf", "chrome", None),
    "sans":            (f"{_GF}/notosansjp/NotoSansJP%5Bwght%5D.ttf",   "chrome", None),
    "bizmincho":       (f"{_GF}/bizudpmincho/BIZUDPMincho-Regular.ttf", "body",   None),
    "bizmincho-bold":  (f"{_GF}/bizudpmincho/BIZUDPMincho-Bold.ttf",    "strong", None),
    "bizgothic":       (f"{_GF}/bizudpgothic/BIZUDPGothic-Regular.ttf", "body",   None),
    "bizgothic-bold":  (f"{_GF}/bizudpgothic/BIZUDPGothic-Bold.ttf",    "strong", None),
    "mono":            (_UDEV_ZIP, "mono", f"{_UDEV_DIR}/UDEVGothic35NFLG-Regular.ttf"),
    "mono-bold":       (_UDEV_ZIP, "mono", f"{_UDEV_DIR}/UDEVGothic35NFLG-Bold.ttf"),
    "mono-italic":     (_UDEV_ZIP, "mono", f"{_UDEV_DIR}/UDEVGothic35NFLG-Italic.ttf"),
    "mono-bolditalic": (_UDEV_ZIP, "mono", f"{_UDEV_DIR}/UDEVGothic35NFLG-BoldItalic.ttf"),
}

# The masters whose coverage decides what has to be folded back into the
# Noto subsets. Regular and Bold of one family ship the same cmap, so one
# of each family is enough.
BODY_MASTERS = ("bizmincho", "bizgothic")

# ASCII printable range as a baseline safety net, independent of extraction.
BASE_CHARS = {chr(c) for c in range(0x20, 0x7F)}

POST_PATH_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/\d{6}/index\.html$")

# Populated once per worker process (via fork, so this is inherited from the
# parent's already-parsed state rather than re-read/re-parsed per task).
_MASTER_FONTS = {}
_BODY_CMAP = set()

# fontTools' default layout_features already covers kern/liga/ccmp/vert etc.;
# "*" (retain every GSUB/GPOS feature) costs ~25% extra subsetting time for
# no visible benefit here. "palt" is added explicitly since Noto Serif/Sans
# JP both implement it (confirmed via direct GPOS inspection). BIZ UDP has
# no palt at all -- its proportional advances are baked into hmtx -- so the
# request is simply a no-op there.
_LAYOUT_FEATURES = Options().layout_features + ["palt"]


class _PageChars(HTMLParser):
    """Split a rendered page's text into the buckets each family serves.

    Tracks element nesting rather than pattern-matching the markup, so a
    <div> inside .entry-content cannot end the body region early. Getting
    this wrong is silent -- the characters simply render in a fallback
    face -- which is why main() re-checks the result against the page.
    """

    # weight 300 で描かれるものだけが Noto に残る。main.css と対で保つこと。
    CHROME_CLASSES = frozenset(("site-title", "entry-title", "term-title"))
    CHROME_TAGS = frozenset(("h2",))
    MONO = frozenset(("code", "pre"))
    SKIP = frozenset(("script", "style"))
    VOID = frozenset((
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chrome = set()
        self.body = set()
        self.strong = set()
        self.mono = set()
        self._stack = []
        self._chrome_at = None  # stack depth where a weight-300 region opened
        self._h2 = 0
        self._strong = 0
        self._mono = 0
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
            return
        if tag in self.VOID:
            return
        self._stack.append(tag)
        if self._chrome_at is None:
            classes = dict(attrs).get("class") or ""
            if self.CHROME_CLASSES & set(classes.split()):
                self._chrome_at = len(self._stack)
        if tag in self.CHROME_TAGS:
            self._h2 += 1
        elif tag == "strong":
            self._strong += 1
        elif tag in self.MONO:
            self._mono += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
            return
        if tag in self.VOID:
            return
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass
        if self._chrome_at is not None and len(self._stack) < self._chrome_at:
            self._chrome_at = None
        if tag in self.CHROME_TAGS:
            self._h2 = max(0, self._h2 - 1)
        elif tag == "strong":
            self._strong = max(0, self._strong - 1)
        elif tag in self.MONO:
            self._mono = max(0, self._mono - 1)

    def handle_data(self, data):
        if self._skip:
            return
        chars = {c for c in data if not c.isspace()}
        if not chars:
            return
        # weight 300 のものだけ Noto。それ以外はすべて BIZ UDP が描く。
        if self._chrome_at is not None or self._h2:
            self.chrome |= chars
            return
        # Code sets --font-mono, so it never reaches the body face. Keeping
        # it out of the body bucket is what makes the mono subset free: the
        # same characters would otherwise ride along in BIZ UDP unused.
        if self._mono:
            self.mono |= chars
            return
        self.body |= chars
        if self._strong:
            self.strong |= chars


def extract_chars(html_path):
    """Return (chrome, body, strong, mono) character sets for one page."""
    with open(html_path, encoding="utf-8") as f:
        parser = _PageChars()
        parser.feed(f.read())
    return parser.chrome, parser.body, parser.strong, parser.mono


def subset_targets(chrome, body, strong, mono, body_cmap):
    """Map each font name to the exact character set it must carry.

    A face whose bucket is empty is left out entirely rather than built
    from the ASCII floor: most articles carry no code, and a bare-ASCII
    subset of the mono faces still costs ~75KB each because the ligature
    tables and hinting survive whatever the glyph count. remove_font_faces()
    then strips their @font-face rules so nothing points at a missing file.
    """
    # Anything the body face cannot draw is handed back to Noto, which
    # covers a far wider repertoire, rather than left to a system font.
    gap = {c for c in body if ord(c) not in body_cmap}
    buckets = {
        # chrome carries every page (masthead, date, footer), so it never
        # drops out; the others appear only when the page uses them.
        "chrome": chrome | gap | BASE_CHARS,
        "body": (body | BASE_CHARS) if body else set(),
        "strong": (strong | BASE_CHARS) if strong else set(),
        # All four mono faces carry the same set: Chroma decides per token
        # which face applies, and working out that split per page would be
        # far more fragile than the few KB it would save.
        "mono": (mono | BASE_CHARS) if mono else set(),
    }
    return {
        name: buckets[role]
        for name, (_, role, _m) in FONT_SOURCES.items()
        if buckets[role]
    }


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
    # Every @font-face sits on its own line, so a face that was not built
    # for this page is removed by dropping the line that still names it.
    unbuilt = [n for n in FONT_SOURCES if n not in hashed_names]
    if unbuilt:
        content = "\n".join(
            line for line in content.split("\n")
            if not any(f"font-{n}.woff2" in line for n in unbuilt)
        )
    if content != original:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)


def rewrite_sibling_ogcard(html_path, hashed_names):
    ogcard_path = os.path.join(os.path.dirname(html_path), "ogcard.html")
    if os.path.exists(ogcard_path):
        rewrite_font_refs(ogcard_path, hashed_names)


def subset_post(args):
    html_path, sources = args
    targets = subset_targets(*extract_chars(html_path), _BODY_CMAP)
    out_dir = os.path.dirname(html_path)
    hashed_names = {
        name: subset_from_master(_MASTER_FONTS[name], chars, out_dir, name)
        for name, chars in targets.items()
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
    _BODY_CMAP.update(
        cp
        for name in BODY_MASTERS
        if name in _MASTER_FONTS
        for cp in _MASTER_FONTS[name].getBestCmap()
    )


def verify(html_path, targets):
    """Report characters the page renders that no shipped subset covers.

    The split above is the one part of this script that can fail without
    raising: a missed region just sends text to a fallback face. Comparing
    the union of every subset against the page's own text catches that.
    """
    buckets = extract_chars(html_path)
    covered = set().union(*targets.values()) if targets else set()
    missing = set().union(*buckets) - covered
    # Characters no master font could draw either are not our failure.
    return {c for c in missing if any(
        ord(c) in _MASTER_FONTS[n].getBestCmap() for n in _MASTER_FONTS
    )}


def download(url, dest, attempts=3):
    """Fetch one file, failing loudly rather than hanging.

    urllib honours no timeout of its own, so a connection that stalls
    mid-transfer would block the build until the runner kills the job.
    The timeout bounds each read instead, and the retry covers the
    transient failures this shared runner already shows in the OG image
    step. Writing to a temporary name and renaming on success keeps a
    half-downloaded file from being mistaken for a cached one later.
    """
    tmp = f"{dest}.part"
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as out:
                shutil.copyfileobj(r, out)
            os.replace(tmp, dest)
            return
        except Exception as exc:
            if os.path.exists(tmp):
                os.remove(tmp)
            if attempt == attempts:
                raise
            print(f"  retrying ({attempt}/{attempts - 1}): {exc}", file=sys.stderr)
            time.sleep(attempt * 2)


def fetch_sources():
    """Download every master font, unpacking archive members as needed.

    Several faces share one archive, so it is fetched once and each member
    extracted from the cached copy rather than re-downloaded per face.
    """
    sources = {}
    archives = {}
    for name, (url, _role, member) in FONT_SOURCES.items():
        local_path = f"/tmp/font-{name}-source.ttf"
        sources[name] = local_path
        if os.path.exists(local_path):
            continue
        if member is None:
            print(f"downloading {name} source font...", file=sys.stderr)
            download(url, local_path)
            continue
        if url not in archives:
            archives[url] = f"/tmp/font-archive-{hashlib.sha256(url.encode()).hexdigest()[:8]}.zip"
            if not os.path.exists(archives[url]):
                print(f"downloading archive for {name}...", file=sys.stderr)
                download(url, archives[url])
        with zipfile.ZipFile(archives[url]) as zf, open(local_path, "wb") as out:
            out.write(zf.read(member))
    return sources


def main():
    sources = fetch_sources()

    all_pages = glob.glob(f"{PUBLIC_DIR}/**/index.html", recursive=True)
    post_pages = [p for p in all_pages if POST_PATH_RE.search(p)]
    other_pages = [p for p in all_pages if p not in set(post_pages)]
    print(f"post pages: {len(post_pages)}, other pages: {len(other_pages)}", file=sys.stderr)

    _init_worker(sources)

    shared = [set(), set(), set(), set()]
    for p in other_pages:
        for bucket, chars in zip(shared, extract_chars(p)):
            bucket |= chars
    shared_targets = subset_targets(*shared, _BODY_CMAP)
    shared_hashed_names = {
        name: subset_from_master(_MASTER_FONTS[name], chars, PUBLIC_DIR, name)
        for name, chars in shared_targets.items()
    }
    print(
        "shared subset: "
        + ", ".join(f"{n} {len(c)}" for n, c in shared_targets.items()),
        file=sys.stderr,
    )

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

    uncovered = {}
    for p in other_pages + post_pages:
        gap = verify(p, subset_targets(*extract_chars(p), _BODY_CMAP))
        if gap:
            uncovered[p] = gap
    if uncovered:
        for p, gap in list(uncovered.items())[:10]:
            print(f"UNCOVERED {p}: {''.join(sorted(gap))}", file=sys.stderr)
        print(f"error: {len(uncovered)} page(s) reference uncovered characters", file=sys.stderr)
        sys.exit(1)

    print(
        f"done: {len(post_pages)} post subsets + shared subset generated "
        f"({len(FONT_SOURCES)} fonts each), coverage verified",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
