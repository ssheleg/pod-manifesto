#!/usr/bin/env python3
"""Prove that index.html carries the canonical text of manifesto.md.

manifesto.md is the one authoritative home for the words. index.html renders them.
This check fails when a canonical sentence is MISSING from the page, so "the site carries
the text" is a command with an exit code rather than a sentence in a commit message.

It measures three things, and for two days it measured only the first. Every block of
`manifesto.md` must appear in `index.html`. Nothing asserted the reverse, so the page could
carry prose that exists in no canonical source; and nothing compared the ORDER, so moving
the document's whole assertion to the front in one file and not the other would have left
every gate here green. Both are checked now.

The reverse pass drops what the forward pass already drops on the other side — fenced code,
tables, headings — plus the sections and chrome that exist only on the page, enumerated in
`PAGE_ONLY`. Symmetry is the rule rather than a stricter regex: compared naively the two
sides differ in 69 places and not one of them is a defect, and a check that loud is one
people learn to skip.

Usage:  python3 tools/check-parity.py [--verbose]
Exit:   0 = the page carries every canonical sentence, carries nothing that is not
            canonical, and carries it in the canonical order
        1 = a sentence is missing, a sentence has no canonical source, the section
            order differs, or the stated case count is not the number listed
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


# ---------------------------------------------------------------------------
# The reverse pass, and what it is allowed to ignore.
#
# The page carries things the canonical text does not and should not: the
# masthead, the contents index, the colophon, the evidence list, the machine
# section. Comparing everything would report sixty-nine differences, of which
# none is a defect, and a check that cries that loudly is one people learn to
# skip.
#
# So the reverse pass drops exactly what the FORWARD pass already drops on the
# other side — fenced code, tables, headings — plus the two sections and the few
# chrome elements that exist only on the page. Symmetry is the rule: anything
# `md_blocks` refuses to look at, this refuses to look at too.
# ---------------------------------------------------------------------------
PAGE_ONLY = [
    (r'<section id="notes".*?</section>', "the evidence list"),
    (r'<section id="machines".*?</section>', "the machine-readable section"),
    (r'<pre\b.*?</pre>', "code blocks — fenced in the canonical text"),
    (r'<table\b.*?</table>', "tables — skipped by md_blocks"),
    (r'<h[1-6]\b[^>]*>.*?</h[1-6]>', "headings — skipped by md_blocks"),
    (r'<figcaption\b.*?</figcaption>', "figure and terminal captions"),
    (r'<p class="eyebrow"[^>]*>.*?</p>', "the section index"),
    (r'<blockquote class="q q--final">.*?</blockquote>', "the closing pull-quote"),
    (r'<p class="sign">.*?</p>', "the signature"),
    (r'<p class="card__note">.*?</p>', "the comparison cards' labels"),
]


def document_body(doc: str) -> str:
    """The part of the page that claims to render the canonical text."""
    m = re.search(r'<main class="doc">(.*?)</main>', doc, re.S)
    body = m.group(1) if m else doc
    for pattern, _ in PAGE_ONLY:
        body = re.sub(pattern, " \n ", body, flags=re.S | re.I)
    return body


def section_order(md: str, doc: str):
    """The canonical `##` headings, and the page's, in the order each states them.

    The forward pass proves every sentence is somewhere on the page. It cannot
    prove they are in the same order, and on 2026-08-23 the whole assertion of
    this document was moved to the front — had that move been made in one file and
    not the other, every gate here would have stayed green.
    """
    md_heads = [normalise(h) for h in re.findall(r"^## (.+)$", md, re.M)]
    page_heads = []
    for raw in re.findall(r'<h2 class="sec__h">(.*?)</h2>', doc, re.S):
        text = normalise(html.unescape(re.sub(r"<[^>]+>", "", raw))).rstrip(" □")
        page_heads.append(text.strip())
    # The page numbers its sections in the eyebrow, not the heading; the canonical
    # text numbers them in the heading. Compare what both actually say.
    md_heads = [re.sub(r"^\d+\.\s*", "", h) for h in md_heads]
    # Sections that exist only on the page are not part of the canonical sequence.
    page_only_headings = {"Preamble", "Evidence", "For machines"}
    page_heads = [h for h in page_heads if h not in page_only_headings]
    return md_heads, page_heads


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

    # ---- the reverse direction ------------------------------------------
    # Symmetric to the forward pass in both what it compares and how: a sentence
    # against the whole canonical text, not against a set of sentences, because a
    # reference label at a paragraph's end moves the boundary on one side only.
    md_text = normalise(" ".join(md_blocks(MD.read_text(encoding="utf-8"))))
    body = document_body(PAGE.read_text(encoding="utf-8"))
    page_sentences = sentences(page_text(body))
    uncanonical = [s for s in page_sentences if s not in md_text]

    print(f"page sentences checked      : {len(page_sentences)}")
    print(f"with no canonical source    : {len(uncanonical)}")
    for s in uncanonical:
        print(f"\n  NOT IN manifesto.md: {s}")

    # ---- and the order ---------------------------------------------------
    md_heads, page_heads = section_order(MD.read_text(encoding="utf-8"),
                                         PAGE.read_text(encoding="utf-8"))
    order_ok = md_heads == page_heads
    print(f"section order               : {len(md_heads)} canonical / "
          f"{len(page_heads)} on the page"
          f" {'ok' if order_ok else 'MISMATCH'}")
    if not order_ok:
        for i, (a, b) in enumerate(zip(md_heads + [""] * len(page_heads),
                                       page_heads + [""] * len(md_heads))):
            if a != b:
                print(f"\n  ORDER: position {i + 1} — manifesto.md says "
                      f"{a or '(nothing)'!r}, the page says {b or '(nothing)'!r}")
                break

    # The page states how many cases it carries. That number is computed here
    # rather than trusted, because the document forbids restating a figure.
    doc = PAGE.read_text(encoding="utf-8")
    claimed = re.search(r"<b data-cases>(\d+)</b>", doc)
    actual = len(re.findall(r'<li id="n\d+"', doc))
    counted_ok = bool(claimed) and int(claimed.group(1)) == actual
    print(f"cases claimed / listed      : "
          f"{claimed.group(1) if claimed else '—'} / {actual}"
          f" {'ok' if counted_ok else 'MISMATCH'}")

    ok = not missing and counted_ok and not uncanonical and order_ok
    if verbose and ok:
        print("\nindex.html carries every canonical sentence of manifesto.md, "
              "carries nothing else, and carries it in the same order.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
