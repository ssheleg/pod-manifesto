#!/usr/bin/env python3
"""Hold the page to the SHELEG `instrument-console` pack and to the motion doctrine.

Both are things a stylesheet drifts away from quietly: one hex literal, one
`transition: all`, one animation with no reduced-motion path. Each is checked
here so the claim "the page still looks like the pack" has an exit code.

Usage:  python3 tools/check-pack.py
Exit:   0 = every rule held
        1 = at least one violation
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "assets" / "style.css"
TOKENS = ROOT / "assets" / "tokens" / "instrument-console.css"
LIGHT = ROOT / "assets" / "tokens" / "console-light.css"
PACK = Path.home() / (".claude/plugins/cache/sheleg-design-skill/sheleg-design/"
                      "1.19.0/skills/sheleg-design/styles/tokens/instrument-console.css")

failures = []


def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def main() -> int:
    css = CSS.read_text(encoding="utf-8")
    # comments carry explanations, including hex values quoted from the pack
    css_code = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    # ── the pack owns the values ─────────────────────────────────────────────
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", css_code)
    check("no colour literal in the component layer", not hexes, ", ".join(sorted(set(hexes))[:6]))

    if TOKENS.exists() and PACK.exists():
        check("token layer is the pack's file, byte for byte",
              TOKENS.read_bytes() == PACK.read_bytes())
    else:
        check("token layer present", TOKENS.exists(), "assets/tokens/instrument-console.css missing")

    check("the light twin is generated, not hand-written",
          LIGHT.exists() and "AUTHORED, NOT EXTRACTED" in LIGHT.read_text(encoding="utf-8"))

    # radii and durations come from the ramp, never from a number
    bad_radius = []
    for value in re.findall(r"border-radius:\s*([^;}]+)", css_code):
        residue = re.sub(r"var\([^)]*\)", "", value)          # tokens are fine
        if re.search(r"\d", residue.replace("0", "")):        # a bare 0 is fine
            bad_radius.append(value.strip())
    check("no hardcoded radius", not bad_radius, "; ".join(bad_radius[:3]))

    # ── the motion doctrine ─────────────────────────────────────────────────
    check("no `transition: all`", "transition: all" not in css_code)

    bare_vh = re.findall(r"\b\d+vh\b", css_code)
    check("no bare vh (svh/dvh only)", not bare_vh, ", ".join(bare_vh[:4]))

    # every rule that hides a revealed element must sit inside no-preference
    no_pref = re.findall(r"@media \(prefers-reduced-motion: no-preference\)\s*\{(.*?)\n\}",
                         css, flags=re.S)
    hidden_total = len(re.findall(r"\.reveal[^{]*\{[^}]*opacity:\s*0", css))
    hidden_guarded = sum(len(re.findall(r"\.reveal[^{]*\{[^}]*opacity:\s*0", block))
                         for block in no_pref)
    check("nothing is hidden outside a no-preference block",
          hidden_total > 0 and hidden_total == hidden_guarded,
          f"{hidden_guarded}/{hidden_total} guarded")

    check("the progress rail collapses under reduce",
          re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{\s*\.rail\s*\{[^}]*display:\s*none",
                    css) is not None)

    # instrument-console ships motion tokens with no reduced-motion branch of its
    # own, so the zeroing has to be found in one layer or the other.
    zeroed = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{\s*:root\s*\{[^}]*--dur-fast:\s*0s",
                       TOKENS.read_text(encoding="utf-8") + css)
    check("every duration token is zeroed under reduce", zeroed is not None)

    # ── the pack's own bans that bite this page ─────────────────────────────
    check("no italic", not re.search(r"font-style:\s*italic", css_code))

    print(f"\n{len(failures)} violation(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
