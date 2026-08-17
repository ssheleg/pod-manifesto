#!/usr/bin/env python3
"""Assert that index.html closes what it opens.

Written because it did not. An edit that removed a wrapper took its closing tag
with it, leaving one unclosed `<div>` for several commits. Chrome's error
recovery hid it completely — the page rendered — which is exactly why this needs
to be a check and not a reading: the defect was invisible in the one browser it
was looked at in, and error recovery is not specified to agree between engines.

Also checks the two things that silently break a page the same way: a stray
closing tag, and a `<style>`/`<script>` that never closes.

Usage:  python3 tools/check-html.py
Exit:   0 = every element is balanced
        1 = at least one is not
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# elements the HTML parser is allowed to close implicitly
OPTIONAL_END = {"li", "dt", "dd", "p", "option", "thead", "tbody", "tfoot", "tr", "td", "th"}

TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>")


def main() -> int:
    src = PAGE.read_text(encoding="utf-8")
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)          # comments
    src = re.sub(r"<svg\b.*?</svg>", "", src, flags=re.S | re.I)   # figures are generated
    src = re.sub(r"<!doctype[^>]*>", "", src, flags=re.I)
    body = src[src.index("<html"):]

    stack, errors = [], []
    for m in TAG.finditer(body):
        closing, tag, _attrs, self_closed = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        line = body.count("\n", 0, m.start()) + 1
        if tag in VOID or self_closed:
            continue
        if closing:
            if stack and stack[-1][0] == tag:
                stack.pop()
            elif any(t == tag for t, _ in stack):
                # close through elements whose end tag is optional
                while stack and stack[-1][0] != tag:
                    t, ln = stack.pop()
                    if t not in OPTIONAL_END:
                        errors.append(f"line {line}: </{tag}> closes over an open <{t}> from line {ln}")
                if stack:
                    stack.pop()
            else:
                errors.append(f"line {line}: stray </{tag}>")
        else:
            stack.append((tag, line))

    for tag, line in stack:
        if tag not in OPTIONAL_END:
            errors.append(f"line {line}: <{tag}> is never closed")

    print(f"index.html: {len(errors)} structural error(s)")
    for e in errors:
        print(f"  {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
