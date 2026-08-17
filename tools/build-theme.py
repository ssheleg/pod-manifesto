#!/usr/bin/env python3
"""Derive and verify the light twin of the SHELEG `instrument-console` pack.

The pack ships one register: a near-black console. This page needs a light theme
as well, so the twin below is **authored**, not extracted — and it is authored
under a rule instead of by taste:

  · the field and the ink swap roles between the two themes, so both are colours
    the pack already measured (`--ink` #eef2f7 becomes the light field, `--base`
    #05070a becomes the light ink);
  · the surface ladder is rebuilt by mixing the pack's own base into its own ink
    at the *same* luminance steps the dark ladder uses, so no third colour enters;
  · the accent hue never changes — the pack's rule is that energy varies by
    brightness, never by hue — so the light theme keeps #3392ff and routes
    accent-coloured *text* to the pack's own `--accent-dim` where the bright
    value fails on a light field;
  · every ratio is computed here and written into the file as a comment, so the
    twin ships with the same evidence the measured half does.

Usage:  python3 tools/build-theme.py           # writes assets/tokens/console-light.css
        python3 tools/build-theme.py --check   # recompute and verify, write nothing
Exit:   0 = every stated ratio holds and every floor is cleared
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DARK = ROOT / "assets" / "tokens" / "instrument-console.css"
LIGHT = ROOT / "assets" / "tokens" / "console-light.css"


# ── colour maths ─────────────────────────────────────────────────────────────

def parse(hex_s):
    h = hex_s.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fmt(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def to_hsl(rgb):
    r, g, b = (c / 255 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d + (6 if g < b else 0)) / 6
    elif mx == g:
        h = ((b - r) / d + 2) / 6
    else:
        h = ((r - g) / d + 4) / 6
    return h, s, l


def from_hsl(h, s, l):
    def hue(p, q, t):
        t %= 1
        if t < 1 / 6: return p + (q - p) * 6 * t
        if t < 1 / 2: return q
        if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
        return p
    if s == 0:
        v = l * 255
        return (v, v, v)
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return tuple(hue(p, q, h + k) * 255 for k in (1 / 3, 0, -1 / 3))


def darken_to(rgb, field, floor):
    """Hold the hue and saturation of a pack colour; lower its lightness until it
    clears the floor on this field. Derivation, not a new colour choice."""
    h, s, l = to_hsl(rgb)
    best = rgb
    for i in range(1000, -1, -1):
        cand = from_hsl(h, s, l * i / 1000)
        if ratio(cand, field) >= floor:
            best = cand
            break
    return best


def mix(a, b, t):
    """t=0 is a, t=1 is b — a straight channel mix of two pack colours."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ── the dark ladder, read from the vendored pack file ────────────────────────

def read_dark():
    css = DARK.read_text(encoding="utf-8")
    out = {}
    for name, value in re.findall(r"(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", css):
        out[name] = parse(value)
    return out


def step_positions(dark):
    """Where each dark surface sits between the field and the ink, by luminance."""
    base, ink = dark["--base"], dark["--ink"]
    lo, hi = luminance(base), luminance(ink)
    pos = {}
    for name in ("--surface-1", "--surface-2", "--surface-3", "--hairline", "--hairline-strong"):
        pos[name] = (luminance(dark[name]) - lo) / (hi - lo)
    return pos


def derive_light(dark):
    """The twin: roles swap, steps are preserved, hue is untouched."""
    field, ink = dark["--ink"], dark["--base"]          # the swap
    pos = step_positions(dark)
    light = {"--base": field, "--ink": ink}
    for name, t in pos.items():
        light[name] = mix(field, ink, t)                # same step, opposite direction

    # secondary text: match the dark theme's own contrast targets on the new field
    for name, target in (("--ink-muted", ratio(dark["--ink-muted"], dark["--base"])),
                         ("--ink-faint", ratio(dark["--ink-faint"], dark["--base"]))):
        best, best_err = None, 1e9
        for i in range(1001):
            cand = mix(field, ink, i / 1000)
            err = abs(ratio(cand, field) - target)
            if err < best_err:
                best, best_err = cand, err
        light[name] = best

    # the signal keeps its hue; only what is used as *text* changes
    light["--accent"] = dark["--accent"]
    light["--accent-dim"] = dark["--accent-dim"]
    light["--accent-bright"] = dark["--accent-bright"]
    light["--accent-ink"] = dark["--accent-ink"]
    # The status hues were measured for a dark field: on the light one they fall
    # to 1.69:1 and 2.02:1. Hue and saturation are held; lightness comes down
    # until each clears the text floor.
    light["--ok"] = darken_to(dark["--ok"], field, 4.5)
    light["--warn"] = darken_to(dark["--warn"], field, 4.5)
    return light


# ── floors ───────────────────────────────────────────────────────────────────

FLOORS = [
    ("--ink", "body text", 4.5),
    ("--ink-muted", "secondary text", 4.5),
    ("--ink-faint", "captions (large/quiet only)", 3.0),
    ("--accent-text", "the signal used as text", 4.5),
    ("--ok", "status: ok", 4.5),
    ("--warn", "status: warn", 4.5),
]


def audit(tokens, field_name="--base"):
    field = tokens[field_name]
    rows, failures = [], []
    for name, role, floor in FLOORS:
        if name == "--accent-text":
            # whichever of the accent family is legible as text on this field
            cands = [("--accent", tokens["--accent"]), ("--accent-dim", tokens["--accent-dim"]),
                     ("--accent-bright", tokens["--accent-bright"])]
            best = max(((n, c, ratio(c, field)) for n, c in cands), key=lambda x: x[2])
            n, c, r = best
            rows.append((f"{name} -> {n}", fmt(c), r, floor, role))
            if r < floor:
                failures.append((name, r, floor))
            continue
        r = ratio(tokens[name], field)
        rows.append((name, fmt(tokens[name]), r, floor, role))
        if r < floor:
            failures.append((name, r, floor))
    # the label on an accent fill
    r = ratio(tokens["--accent-ink"], tokens["--accent"])
    rows.append(("--accent-ink on --accent", fmt(tokens["--accent-ink"]), r, 4.5, "label on the signal"))
    if r < 4.5:
        failures.append(("--accent-ink on --accent", r, 4.5))
    return rows, failures


def accent_text_token(tokens):
    field = tokens["--base"]
    cands = [("--accent", tokens["--accent"]), ("--accent-dim", tokens["--accent-dim"]),
             ("--accent-bright", tokens["--accent-bright"])]
    return max(((n, c, ratio(c, field)) for n, c in cands), key=lambda x: x[2])


# ── emit ─────────────────────────────────────────────────────────────────────

def render(light, dark):
    n, c, r = accent_text_token(light)
    rows, _ = audit(light)
    lines = [
        "/* SHELEG Design — Instrument Console, LIGHT TWIN.",
        "",
        "   AUTHORED, NOT EXTRACTED. The pack ships a single dark register; this file",
        "   is generated by tools/build-theme.py under the rule stated at the top of",
        "   that script: the field and the ink swap roles, the surface ladder is",
        "   rebuilt from the same two pack colours at the dark ladder's own luminance",
        "   steps, and the accent hue is untouched. Regenerate rather than hand-edit.",
        "",
        "   Measured on this file, against --base:",
    ]
    for name, value, rr, floor, role in rows:
        lines.append(f"     {name:<26} {value}  {rr:6.2f}:1  (floor {floor})  {role}")
    lines += [
        "*/",
        "",
        ':root[data-theme="light"] {',
        "  color-scheme: light;",
        "",
    ]
    order = ["--base", "--surface-1", "--surface-2", "--surface-3",
             "--hairline", "--hairline-strong", "--ink", "--ink-muted", "--ink-faint"]
    for k in order:
        lines.append(f"  {k}: {fmt(light[k])};")
    lines += [
        "",
        "  /* The signal keeps its hue in both themes — the pack's rule is that",
        f"     energy varies by brightness, never by hue. As TEXT on this field the",
        f"     bright value measures {ratio(light['--accent'], light['--base']):.2f}:1 and fails, so accent-coloured type",
        f"     takes {n} ({fmt(c)}, {r:.2f}:1). The fill and its label are unchanged. */",
        f"  --accent: {fmt(light['--accent'])};",
        f"  --accent-dim: {fmt(light['--accent-dim'])};",
        f"  --accent-bright: {fmt(light['--accent-bright'])};",
        f"  --accent-ink: {fmt(light['--accent-ink'])};",
        f"  --accent-text: var({n});",
        "  --accent-glow: rgba(51, 146, 255, 0.14);",
        "",
        f"  --ok: {fmt(light['--ok'])};",
        f"  --warn: {fmt(light['--warn'])};",
        "",
        "  --signal-glow: 0 0 0 1px rgba(51, 146, 255, 0.35),",
        "    0 8px 30px rgba(51, 146, 255, 0.12);",
        "",
        "  background-color: var(--base);",
        "  color: var(--ink);",
        "  --bg: var(--base);",
        "}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    check = "--check" in sys.argv
    dark = read_dark()
    light = derive_light(dark)

    print("dark register (the pack, as measured)")
    rows_d, fail_d = audit({**dark, "--accent-text": None} if False else dark)
    for name, value, r, floor, role in rows_d:
        print(f"  {name:<26} {value}  {r:6.2f}:1  floor {floor}  {'ok' if r >= floor else 'FAIL'}")

    print("\nlight twin (authored here)")
    rows_l, fail_l = audit(light)
    for name, value, r, floor, role in rows_l:
        print(f"  {name:<26} {value}  {r:6.2f}:1  floor {floor}  {'ok' if r >= floor else 'FAIL'}")

    css = render(light, dark)
    if check:
        current = LIGHT.read_text(encoding="utf-8") if LIGHT.exists() else ""
        if current != css:
            print("\nconsole-light.css is out of date — run tools/build-theme.py")
            return 1
    else:
        LIGHT.parent.mkdir(parents=True, exist_ok=True)
        LIGHT.write_text(css, encoding="utf-8")
        print(f"\nwrote {LIGHT.relative_to(ROOT)}")

    failures = fail_d + fail_l
    print(f"\n{len(failures)} floor(s) missed")
    for name, r, floor in failures:
        print(f"  {name}: {r:.2f}:1 < {floor}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
