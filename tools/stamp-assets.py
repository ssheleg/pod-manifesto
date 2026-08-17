#!/usr/bin/env python3
"""Fingerprint every asset URL in index.html with a hash of its contents.

Written because a deploy shipped and the browser kept serving the previous
stylesheet — twice, to two different people, and once to me while I was checking
whether the deploy had worked. GitHub Pages sends `Cache-Control: max-age=600`
on everything, so a fresh HTML page can reference a stale CSS file by the same
URL and the browser is right to reuse it.

A content hash in the query string removes the ambiguity rather than working
around it: change the file and the URL changes, so no cache anywhere — browser,
Cloudflare, or a proxy in between — can answer with the old bytes. Unchanged
files keep their URL and stay cached, which is the point.

Usage:  python3 tools/stamp-assets.py           # rewrite index.html
        python3 tools/stamp-assets.py --check   # fail if any stamp is stale
Exit:   0 = every asset reference carries the hash of its current contents
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"

# every same-origin asset the page references
REF = re.compile(r'(?P<attr>href|src|content)="(?P<url>/(?:assets/[^"?]+|favicon\.svg|og\.png))(?:\?v=[0-9a-f]+)?"')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def main() -> int:
    check = "--check" in sys.argv
    html = PAGE.read_text(encoding="utf-8")
    missing, stamped = [], []

    def repl(m):
        url = m.group("url")
        target = ROOT / url.lstrip("/")
        if not target.exists():
            missing.append(url)
            return m.group(0)
        h = digest(target)
        stamped.append((url, h))
        return f'{m.group("attr")}="{url}?v={h}"'

    out = REF.sub(repl, html)

    for url, h in stamped:
        print(f"  {h}  {url}")
    for url in missing:
        print(f"  MISSING  {url}")

    if missing:
        print(f"\n{len(missing)} referenced asset(s) do not exist")
        return 1

    if check:
        current = out == html
        print(f"\n{len(stamped)} assets stamped — {'current' if current else 'STALE'}")
        return 0 if current else 1

    if out != html:
        PAGE.write_text(out, encoding="utf-8")
    print(f"\n{len(stamped)} assets stamped into index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
