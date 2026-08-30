#!/usr/bin/env python3
"""Drop the空白 that Markdown's soft line breaks leave inside Japanese text.

CommonMark turns a single newline inside a paragraph into a newline in the
HTML, and HTML renders that newline as a space. For English that space is
the word separator and belongs there; for Japanese it is a gap that nobody
typed. Measured on this site, a stray break sits at 0.34em -- a third of a
character -- which is enough to make a linked phrase look detached from the
sentence around it.

Goldmark's cjk extension (eastAsianLineBreaks) already removes the break
when the characters on both sides are East Asian, and hugo.toml enables it.
It cannot see through an inline element: after </a> the preceding "character"
is a tag boundary, not a kanji, so the rule never fires. That leaves the
breaks this script removes -- the ones that follow a link, some code, or an
emphasis.

Only <p> and <li> inside the article body are touched, and only when at
least one of the characters around the break is Japanese -- a space between
two Latin words is a real separator and stays. <pre> keeps its whitespace
because it never appears inside those elements.
"""
import glob
import re
import sys

PUBLIC_DIR = "public"

# 本文領域。ここ以外(ヘッダ・フッタ・生HTMLブロック)には触れない。
# entry-content は <div> で、中に <div class="highlight"> を含むため、
# 非貪欲な正規表現では最初の </div> で切れてしまう。入れ子を数えて閉じ位置
# を求める。entry-summary は <p> なので単純に閉じタグまで。
BODY_OPEN_RE = re.compile(r'<(div|p)[^>]*class="[^"]*\b(?:entry-content|entry-summary)\b[^"]*"[^>]*>')
BLOCK_RE = re.compile(r"<(p|li)(\s[^>]*)?>(.*?)</\1>", re.S)
TAG_RE = re.compile(r"<[^>]*>")
BREAK_RE = re.compile(r"[ \t]*\n+[ \t]*")


def is_japanese(ch):
    o = ord(ch)
    return (
        0x3000 <= o <= 0x303F        # 、。「」など
        or 0x3040 <= o <= 0x309F     # ひらがな
        or 0x30A0 <= o <= 0x30FF     # カタカナ
        or 0x4E00 <= o <= 0x9FFF     # 漢字
        or 0xFF01 <= o <= 0xFF60     # 全角英数・記号
    )


def _visible_before(text, pos):
    """Last character rendered before pos, looking through closing tags."""
    i = pos - 1
    while i >= 0:
        if text[i] == ">":
            j = text.rfind("<", 0, i)
            if j < 0:
                return None
            i = j - 1
            continue
        if text[i].isspace():
            i -= 1
            continue
        return text[i]
    return None


def _visible_after(text, pos):
    """First character rendered at or after pos, looking through open tags."""
    i = pos
    n = len(text)
    while i < n:
        if text[i] == "<":
            j = text.find(">", i)
            if j < 0:
                return None
            i = j + 1
            continue
        if text[i].isspace():
            i += 1
            continue
        return text[i]
    return None


def fix_block(inner):
    out = []
    last = 0
    for m in BREAK_RE.finditer(inner):
        before = _visible_before(inner, m.start())
        after = _visible_after(inner, m.end())
        # 空白が要るのは欧文の単語区切りとしてだけ。片側でも和文なら、
        # 同じ内容を1行で書いたときと同じ描画になるよう改行を落とす。
        if before and after and (is_japanese(before) or is_japanese(after)):
            out.append(inner[last:m.start()])
            last = m.end()
    if not out:
        return inner, 0
    out.append(inner[last:])
    return "".join(out), len(out) - 1


def _body_end(content, tag, start):
    """Index just past the element that opened at start, counting nesting."""
    depth = 1
    pos = start
    pat = re.compile(rf"<(/?){tag}\b[^>]*?(/?)>", re.I)
    while depth:
        m = pat.search(content, pos)
        if not m:
            return len(content)
        pos = m.end()
        if m.group(2) == "/":
            continue
        depth += -1 if m.group(1) else 1
    return pos


def fix_html(content):
    total = 0
    out = []
    pos = 0
    for om in BODY_OPEN_RE.finditer(content):
        if om.start() < pos:
            continue
        tag = om.group(1)
        end = _body_end(content, tag, om.end())
        inner = content[om.end():end]
        fixed_parts = []

        def on_block(m):
            nonlocal total
            fixed, n = fix_block(m.group(3))
            total += n
            return f"<{m.group(1)}{m.group(2) or ''}>{fixed}</{m.group(1)}>"

        if tag == "p":
            # entry-summary 自身が <p> なので、中身を直に処理する
            fixed, n = fix_block(inner)
            total += n
        else:
            fixed = BLOCK_RE.sub(on_block, inner)
        out.append(content[pos:om.end()])
        out.append(fixed)
        pos = end
    out.append(content[pos:])
    return "".join(out), total


def main():
    pages = glob.glob(f"{PUBLIC_DIR}/**/*.html", recursive=True)
    removed = 0
    touched = 0
    for path in pages:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        fixed, n = fix_html(content)
        if n:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed)
            removed += n
            touched += 1
    print(
        f"cjk breaks removed: {removed} in {touched}/{len(pages)} pages",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
