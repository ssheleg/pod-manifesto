#!/usr/bin/env python3
"""Resolve every external reference this repository publishes.

The manifesto's own rule: a reference that does not resolve is a claim with its receipt
removed. This applies the rule to the document itself.

Usage:  python3 tools/check-links.py
Exit:   0 = every link resolved
        1 = at least one link did not
"""

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["index.html", "manifesto.md", "llms.txt", "README.md", "sitemap.xml"]

# Not yet resolvable from outside: the site's own paths are checked against the working
# tree instead, because a freshly built page has no deployed URL to fetch.
SELF = "https://podmanifesto.org"

UA = {"User-Agent": "pod-manifesto-link-check/1.0 (+https://podmanifesto.org)"}
TIMEOUT = 25


def collect() -> dict:
    found = {}
    for name in SOURCES:
        text = (ROOT / name).read_text(encoding="utf-8")
        for url in re.findall(r'https?://[^\s"\'<>)\]]+', text):
            found.setdefault(url.rstrip('.,;'), set()).add(name)
    return found


def check(url: str) -> tuple:
    if url.startswith(SELF):
        path = url[len(SELF):].split("#")[0].lstrip("/") or "index.html"
        return ((ROOT / path).exists(), "local file" if (ROOT / path).exists() else "MISSING FILE")
    req = urllib.request.Request(url, headers=UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return (200 <= r.status < 300, str(r.status))
    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}")
    except Exception as e:                                   # noqa: BLE001 - report, do not raise
        return (False, type(e).__name__)


def main() -> int:
    links = collect()
    bad = []
    for url in sorted(links):
        ok, note = check(url)
        mark = "ok  " if ok else "FAIL"
        print(f"{mark} {note:<12} {url}")
        if not ok:
            bad.append((url, note, sorted(links[url])))

    print(f"\n{len(links)} links checked, {len(bad)} unresolved")
    for url, note, where in bad:
        print(f"  {note}: {url}  (in {', '.join(where)})")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
