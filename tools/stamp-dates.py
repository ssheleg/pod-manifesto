#!/usr/bin/env python3
"""Derive every published date in this repository from the commits, not from memory.

Three dates were being carried by hand, and two of them were wrong on
2026-08-20:

  * `sitemap.xml` gave `lastmod 2026-08-17` for `/`, `/manifesto.md` and
    `/llms.txt`. All three had last changed on 2026-08-19, in the commit that
    corrected the document's own stale paragraph. A crawler was being told the
    text had not moved since the day the error shipped.
  * the JSON-LD block and `llms.txt` carried `datePublished` and no
    `dateModified` at all — in a document whose §5 says proof is perishable and
    whose masthead is the first thing a reader dates.

`datePublished` and the version are editorial and stay hand-written; a
modification date is a measurement, so it is measured. The date for each URL is
the committer date of the newest commit touching the files that URL serves,
which is also why `/` tracks `index.html` *and* its assets: a restyled page is a
changed page.

Usage:  python3 tools/stamp-dates.py           # rewrite the dates
        python3 tools/stamp-dates.py --check   # fail if any is not what git says
Exit:   0 = every published date equals the commit date it describes
        1 = at least one is stale
        2 = the check could not look (no git history here)
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# a sitemap URL and the paths whose newest change it describes
SERVES = {
    "https://podmanifesto.org/": ["index.html", "assets"],
    "https://podmanifesto.org/manifesto.md": ["manifesto.md"],
    "https://podmanifesto.org/llms.txt": ["llms.txt"],
}
# the modification date of the document as a whole
DOCUMENT = ["manifesto.md", "index.html", "llms.txt"]


def last_change(paths):
    """ISO date of the newest commit touching any of these paths, or None.

    An uncommitted change to one of them counts as today's, because the commit
    that is about to be written is the one the date will describe. Without this
    the tool is unusable: stamping the last commit's date and then committing
    makes the stamp stale in the same breath, and CI on the clean checkout goes
    red on the change that stamped it.
    """
    try:
        dirty = subprocess.run(["git", "status", "--porcelain", "--"] + paths,
                               cwd=ROOT, capture_output=True, text=True, check=True)
        if dirty.stdout.strip():
            return date.today().isoformat()
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short", "--"] + paths,
            cwd=ROOT, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip() or None


def main() -> int:
    check = "--check" in sys.argv
    stale, edits = [], {}

    doc_date = last_change(DOCUMENT)
    if not doc_date:
        print("no git history here — a check that cannot look is not a pass")
        return 2

    # ---- sitemap ---------------------------------------------------------
    sitemap = ROOT / "sitemap.xml"
    text = sitemap.read_text(encoding="utf-8")
    for url, paths in SERVES.items():
        want = last_change(paths)
        if not want:
            continue
        pattern = re.compile(
            r"(<loc>" + re.escape(url) + r"</loc>\s*<lastmod>)(\d{4}-\d{2}-\d{2})(</lastmod>)")
        m = pattern.search(text)
        if not m:
            stale.append(f"sitemap.xml: no lastmod found for {url}")
            continue
        if m.group(2) != want:
            stale.append(f"sitemap.xml: {url} says {m.group(2)}, git says {want}")
        text = pattern.sub(lambda mm, w=want: mm.group(1) + w + mm.group(3), text, count=1)
    if text != sitemap.read_text(encoding="utf-8"):
        edits[sitemap] = text

    # ---- JSON-LD dateModified -------------------------------------------
    page = ROOT / "index.html"
    html = page.read_text(encoding="utf-8")
    if '"dateModified"' in html:
        new = re.sub(r'("dateModified":\s*")(\d{4}-\d{2}-\d{2})(")',
                     lambda m: m.group(1) + doc_date + m.group(3), html, count=1)
        found = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})"', html)
        if found and found.group(1) != doc_date:
            stale.append(f'index.html: JSON-LD dateModified says {found.group(1)}, git says {doc_date}')
    else:
        new = html.replace('"datePublished": "', f'"dateModified": "{doc_date}",\n  "datePublished": "', 1)
        stale.append("index.html: JSON-LD carries no dateModified")
    if new != html:
        edits[page] = new
        html = new

    # ---- the masthead's own line ----------------------------------------
    if "docmeta__updated" in html:
        found = re.search(r'<time class="docmeta__updated" datetime="(\d{4}-\d{2}-\d{2})">'
                          r'(\d{4}-\d{2}-\d{2})</time>', html)
        if found and (found.group(1) != doc_date or found.group(2) != doc_date):
            stale.append(f"index.html: masthead Updated says {found.group(2)}, git says {doc_date}")
        html = re.sub(r'(<time class="docmeta__updated" datetime=")\d{4}-\d{2}-\d{2}("[^>]*>)\d{4}-\d{2}-\d{2}(</time>)',
                      lambda m: m.group(1) + doc_date + m.group(2) + doc_date + m.group(3), html, count=1)
        edits[page] = html

    # ---- llms.txt --------------------------------------------------------
    llms = ROOT / "llms.txt"
    ltext = llms.read_text(encoding="utf-8")
    found = re.search(r"published (\d{4}-\d{2}-\d{2}), last modified (\d{4}-\d{2}-\d{2})\.", ltext)
    if found:
        if found.group(2) != doc_date:
            stale.append(f"llms.txt: last modified says {found.group(2)}, git says {doc_date}")
        lnew = re.sub(r"(published \d{4}-\d{2}-\d{2}, last modified )\d{4}-\d{2}-\d{2}(\.)",
                      lambda m: m.group(1) + doc_date + m.group(2), ltext, count=1)
    else:
        stale.append("llms.txt: states no modification date")
        lnew = re.sub(r"(published \d{4}-\d{2}-\d{2})\.",
                      lambda m: f"{m.group(1)}, last modified {doc_date}.", ltext, count=1)
    if lnew != ltext:
        edits[llms] = lnew

    for s in stale:
        print(f"  STALE  {s}")
    print(f"\ndocument last changed {doc_date} (git); "
          f"{len(SERVES)} sitemap url(s) and 3 modification date(s) checked")

    if check:
        return 1 if stale else 0

    for path, out in edits.items():
        path.write_text(out, encoding="utf-8")
    if edits:
        print(f"rewrote {len(edits)} file(s): " + ", ".join(p.name for p in edits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
