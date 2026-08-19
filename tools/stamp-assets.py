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

Usage:  python3 tools/stamp-assets.py           # rewrite index.html and fonts.css
        python3 tools/stamp-assets.py --check   # fail if any stamp is stale
Exit:   0 = every asset reference carries the hash of its current contents
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
FONTS = ROOT / "assets" / "fonts" / "fonts.css"

# Two holes were measured on 2026-08-20 and closed here, because the README
# described this gate as covering "every asset URL":
#
#   1. `og.png` is referenced three times as an ABSOLUTE url
#      (https://podmanifesto.org/og.png — og:image and twitter:image require it),
#      and the root-relative pattern never matched it. A changed preview image
#      would have kept its url forever.
#   2. `fonts.css` carries its own four `url()` references. Its hash covers the
#      CSS text, not the fonts it points at, so replacing a woff2 changed no
#      url anywhere. The two `-ext` faces were reachable only that way.
#
# So the origin prefix is optional in the page, and the stylesheet is stamped
# too — which also makes the chain correct: stamping a font changes fonts.css,
# whose new hash then changes its own url in the page.
ORIGIN = "https://podmanifesto.org"
REF = re.compile(
    r'(?P<attr>href|src|content)="(?P<origin>https://podmanifesto\.org)?'
    r'(?P<url>/(?:assets/[^"?]+|favicon\.svg|og\.png))(?:\?v=[0-9a-f]+)?"'
)
# "image": "https://podmanifesto.org/og.png" inside the JSON-LD block — a
# crawler fetches it like any other asset, so it carries a fingerprint too.
JSONLD_REF = re.compile(
    r'(?P<attr>"image":\s*")(?P<origin>https://podmanifesto\.org)'
    r'(?P<url>/(?:assets/[^"?]+|favicon\.svg|og\.png))(?:\?v=[0-9a-f]+)?"'
)
# every same-origin asset url must end up fingerprinted; this is the residual
# scan that makes the claim "every asset URL" checkable rather than asserted.
RESIDUAL = re.compile(
    r'(?:https://podmanifesto\.org)?/(?:assets/[^"\'\s?)]+|favicon\.svg|og\.png)(?=["\'\s)])'
)
# url('./geist-latin.woff2') inside assets/fonts/fonts.css
FONT_REF = re.compile(r"url\('(?P<url>\./[^']+?\.woff2)(?:\?v=[0-9a-f]+)?'\)")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def main() -> int:
    check = "--check" in sys.argv
    stamped, missing = [], []

    def apply(path, text, pattern, resolve, rebuild):
        def repl(m):
            url = m.group("url")
            target = resolve(url)
            if not target.exists():
                missing.append(f"{path.name} -> {url}")
                return m.group(0)
            h = digest(target)
            stamped.append((path.relative_to(ROOT), url, h))
            return rebuild(m, h)
        return pattern.sub(repl, text)

    # The stylesheet first: stamping a font changes fonts.css, whose new hash
    # then has to reach its own reference in the page. Do it the other way round
    # and the page carries the hash of the previous stylesheet — the exact bug
    # this tool exists for, one level down.
    fonts_before = FONTS.read_text(encoding="utf-8")
    fonts_after = apply(FONTS, fonts_before, FONT_REF,
                        lambda url: FONTS.parent / url[2:],
                        lambda m, h: f"url('{m.group('url')}?v={h}')")
    if not check and fonts_after != fonts_before:
        FONTS.write_text(fonts_after, encoding="utf-8")

    page_before = PAGE.read_text(encoding="utf-8")
    page_after = apply(PAGE, page_before, REF,
                       lambda url: ROOT / url.lstrip("/"),
                       lambda m, h: f'{m.group("attr")}="{m.group("origin") or ""}{m.group("url")}?v={h}"')
    page_after = apply(PAGE, page_after, JSONLD_REF,
                       lambda url: ROOT / url.lstrip("/"),
                       lambda m, h: f'{m.group("attr")}{m.group("origin")}{m.group("url")}?v={h}"')

    for where, url, h in stamped:
        print(f"  {h}  {where} -> {url}")
    for m in missing:
        print(f"  MISSING  {m}")
    if missing:
        print(f"\n{len(missing)} referenced asset(s) do not exist")
        return 1

    # The residual scan is what makes "every asset URL" checkable instead of
    # asserted: any same-origin asset reference the patterns above did not reach
    # is reported here rather than shipping unfingerprinted.
    unstamped = sorted({m.group(0) for m in RESIDUAL.finditer(page_after)}
                       | {m.group(0) for m in RESIDUAL.finditer(fonts_after)})
    for u in unstamped:
        print(f"  UNSTAMPED  {u}")
    if unstamped:
        print(f"\n{len(unstamped)} same-origin asset url(s) carry no fingerprint")
        return 1

    if check:
        current = fonts_after == fonts_before and page_after == page_before
        print(f"\n{len(stamped)} assets stamped — {'current' if current else 'STALE'}")
        return 0 if current else 1

    if page_after != page_before:
        PAGE.write_text(page_after, encoding="utf-8")
    print(f"\n{len(stamped)} assets stamped into index.html and fonts.css")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
