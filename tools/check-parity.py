#!/usr/bin/env python3
"""Prove that index.html carries the canonical text of manifesto.md.

manifesto.md is the one authoritative home for the words. index.html renders them.
This check fails when the two drift, so "the site matches the text" is a command with
an exit code rather than a sentence in a commit message.

Usage:  python3 tools/check-parity.py [--verbose]
Exit:   0 = every canonical sentence is present in the page
        1 = at least one sentence is missing
"""

import html
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "manifesto.md"
PAGE = ROOT / "index.html"

MIN_LEN = 40  # shorter fragments carry too little signal to locate a drift

BLOCK_TAGS = (
    "p|div|section|article|header|footer|main|nav|aside|figure|figcaption|"
    "h[1-6]|ul|ol|li|dl|dt|dd|table|thead|tbody|tr|td|th|caption|"
    "blockquote|pre|br|hr|details|summary|form"
)


def normalise(text: str) -> str:
    """Collapse the differences that are typography rather than content."""
    text = unicodedata.normalize("NFKC", text)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("—", "-"), ("–", "-"), ("−", "-"),
                 (" ", " "), (" ", " "), (" ", " ")):
        text = text.replace(a, b)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)   # inline markup leaves a gap here
    return text.strip()


def md_blocks(md: str) -> list:
    md = re.sub(r"```.*?```", "\n\n", md, flags=re.S)       # fenced code and mermaid
    out = []
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block or block.startswith(("#", "|", "---")):
            continue                                        # headings, tables, rules
        block = re.sub(r"^\s*[>*-]\s+", "", block, flags=re.M)
        block = re.sub(r"^\s*\d+\.\s+", "", block, flags=re.M)
        block = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", block)   # links -> link text
        block = block.replace("**", "").replace("`", "")
        out.append(normalise(block))
    return out


def page_text(doc: str) -> str:
    doc = re.sub(r"<script.*?</script>", " ", doc, flags=re.S | re.I)
    doc = re.sub(r"<style.*?</style>", " ", doc, flags=re.S | re.I)
    doc = re.sub(r"<svg\b.*?</svg>", " ", doc, flags=re.S | re.I)   # figure labels
    doc = re.sub(r"<!--.*?-->", " ", doc, flags=re.S)
    doc = re.sub(rf"</?(?:{BLOCK_TAGS})\b[^>]*>", " \n ", doc, flags=re.I)
    doc = re.sub(r"<[^>]+>", "", doc)                       # inline tags leave no gap
    return normalise(html.unescape(doc))


def sentences(block: str) -> list:
    parts = re.split(r'(?<=[.:?!])\s+(?=[A-Z"\'(])', block)
    return [p.strip() for p in parts if len(p.strip()) >= MIN_LEN]


def main() -> int:
    verbose = "--verbose" in sys.argv
    rendered = page_text(PAGE.read_text(encoding="utf-8"))

    checked, missing = 0, []
    for block in md_blocks(MD.read_text(encoding="utf-8")):
        for s in sentences(block):
            checked += 1
            if s not in rendered:
                missing.append(s)

    print(f"canonical sentences checked : {checked}")
    print(f"missing from index.html     : {len(missing)}")
    for s in missing:
        print(f"\n  MISSING: {s}")

    # The page states how many cases it carries. That number is computed here
    # rather than trusted, because the document forbids restating a figure.
    doc = PAGE.read_text(encoding="utf-8")
    claimed = re.search(r"<b data-cases>(\d+)</b>", doc)
    actual = len(re.findall(r'<li id="n\d+"', doc))
    counted_ok = bool(claimed) and int(claimed.group(1)) == actual
    print(f"cases claimed / listed      : "
          f"{claimed.group(1) if claimed else '—'} / {actual}"
          f" {'ok' if counted_ok else 'MISMATCH'}")

    if verbose and not missing and counted_ok:
        print("\nindex.html carries every canonical sentence of manifesto.md.")
    return 0 if (not missing and counted_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
