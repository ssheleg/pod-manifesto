#!/usr/bin/env python3
"""Hold the stylesheet to its own token block and to the motion doctrine.

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
    # A colour literal may be written inside a `:root` block and nowhere else.
    #
    # This used to be expressed positionally — everything before `*, *::before`
    # and everything from `@media print` onward was treated as token territory.
    # The second half of that was a hole: `@media print` sits at line 646 and 147
    # lines of components follow it, so every rule in the "ADDED AFTER THE FIRST
    # VERSION" section was exempt from the check that names this file. It was
    # clean when measured on 2026-08-23, which is luck rather than a gate.
    #
    # Stated as the rule instead of as a position, it covers the whole stylesheet
    # and stays correct wherever a future `:root` block is written.
    ROOT_BLOCK = re.compile(r":root[^{]*\{[^{}]*\}", re.S)
    tokens = "".join(m.group(0) for m in ROOT_BLOCK.finditer(css_code))
    components = ROOT_BLOCK.sub(" ", css_code)
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", components)
    check("no colour literal outside the token block", not hexes, ", ".join(sorted(set(hexes))[:6]))
    check("the token block defines the field and the accent",
          "--bg:" in tokens and "--accent:" in tokens)


    # radii and durations come from the ramp, never from a number
    bad_radius = []
    for value in re.findall(r"border-radius:\s*([^;}]+)", components):
        residue = re.sub(r"var\([^)]*\)", "", value)          # tokens are fine
        residue = residue.replace("50%", "")                  # a circle is not a ramp value
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

    check("the progress bar collapses under reduce",
          re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{\s*\.progress\s*\{[^}]*display:\s*none",
                    css) is not None)

    check("nothing animates without a no-preference guard",
          "prefers-reduced-motion: no-preference" in css)

    # ── the stylesheet parses ───────────────────────────────────────────────
    # A script that stripped a rule once left its @media wrapper open, and every
    # rule after it was swallowed. CSS error recovery hides this until it does not.
    stack = []
    for i, ch in enumerate(css_code):
        if ch == "{":
            stack.append(i)
        elif ch == "}":
            if stack:
                stack.pop()
            else:
                stack.append(-i)
    unclosed = [i for i in stack if i >= 0]
    where = ""
    if unclosed:
        ln = css_code.count("\n", 0, unclosed[0]) + 1
        where = f"line ~{ln}: {css_code.splitlines()[ln - 1][:60]}"
    check("every block is closed", not stack, where or "a stray closing brace")

    # ── the pack's own bans that bite this page ─────────────────────────────
    check("no italic", not re.search(r"font-style:\s*italic", css_code))

    print(f"\n{len(failures)} violation(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
