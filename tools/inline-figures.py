#!/usr/bin/env python3
"""Inline the generated figures into index.html.

The SVGs are inlined rather than referenced with <img> because they take their
colour from the page's CSS custom properties — an external image cannot read
them, and the figures would lose the theme.

Each slot in the page is a pair of markers:  <!--FIG:fig-1--> … <!--/FIG-->

Usage:  python3 tools/inline-figures.py [--check]
Exit:   0 = every slot filled (or, with --check, already current)
        1 = a slot has no figure, or the page is out of date
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
FIGS = ROOT / "assets" / "figures"

SLOT = re.compile(r"(<!--FIG:([a-z0-9-]+)-->)(.*?)(<!--/FIG-->)", re.S)


def main() -> int:
    check = "--check" in sys.argv
    html = PAGE.read_text(encoding="utf-8")
    missing, filled, stale = [], 0, []

    def repl(m):
        nonlocal filled
        open_tag, name, current, close_tag = m.groups()
        svg = FIGS / f"{name}.svg"
        if not svg.exists():
            missing.append(name)
            return m.group(0)
        body = svg.read_text(encoding="utf-8").strip()
        if current.strip() != body:
            stale.append(name)
        filled += 1
        return f"{open_tag}{body}{close_tag}"

    out = SLOT.sub(repl, html)

    if missing:
        for n in missing:
            print(f"MISSING figure: assets/figures/{n}.svg")
        return 1

    if check:
        print(f"{filled} slots, {len(stale)} out of date"
              + (": " + ", ".join(stale) if stale else ""))
        return 1 if stale else 0

    if out != html:
        PAGE.write_text(out, encoding="utf-8")
    print(f"{filled} figures inlined into index.html"
          + (f" ({len(stale)} updated)" if stale else " (already current)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
