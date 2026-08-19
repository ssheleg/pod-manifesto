#!/usr/bin/env python3
"""Every gate in this repository, fed a planted defect and required to refuse it.

This document says it at `manifesto.md:190`: a check must be shown able to
discriminate failure from success, and a green nobody watched fail is not
evidence. Until this file existed, eight of the nine tools here had no negative
control — `check-currency.py` had one, and the rest were trusted because they
were green. That is the exact position the manifesto argues against, held by the
manifesto's own repository.

How a case runs
---------------
The tree is copied to a temporary directory (without `.git`), one defect is
planted in the copy, and the gate is run there with the copy as its root. Two
things are asserted, in this order:

  1. **the plant landed** — the file on disk actually changed. A plant that
     silently matched nothing turns the case into a green that proves nothing,
     which is the failure mode this whole file exists to prevent. Measured in
     four sibling repositories before it was believed.
  2. **the gate refused** — a non-zero exit. The gate's output is captured and
     the first line that mentions the defect is printed, so the refusal is
     legible rather than merely counted.

Nothing is written to the real tree, and the copy is removed on the pass path
and KEPT on the fail path — a planted defect is debugged by reading the tree it
landed in, and a cleanup that runs only when the case passed deletes the
evidence exactly when it is wanted.

The two network cases are skipped without a token, and the skip is printed and
counted. A run that could not look must not read as a run that looked.

Usage:  python3 tools/negatives.py            # every case
        python3 tools/negatives.py --offline   # only the cases needing no network
        python3 tools/negatives.py -k parity   # cases whose name matches
Exit:   0 = every case's plant landed and its gate refused
        1 = a plant did not land, or a gate accepted a defect
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Planting helpers. Each returns the (path, before, after) it changed so the
# caller can prove the plant landed rather than trusting that it did.
# --------------------------------------------------------------------------
def replace_once(tree, rel, old, new):
    p = tree / rel
    before = p.read_text(encoding="utf-8")
    if old not in before:
        return p, before, before          # did not land; the runner will fail the case
    after = before.replace(old, new, 1)
    p.write_text(after, encoding="utf-8")
    return p, before, after


def sub_once(tree, rel, pattern, new):
    p = tree / rel
    before = p.read_text(encoding="utf-8")
    after, n = re.subn(pattern, new, before, count=1)
    if n:
        p.write_text(after, encoding="utf-8")
    return p, before, after


CASES = [
    # ---- check-parity ----------------------------------------------------
    dict(
        name="parity: a canonical sentence altered on the page",
        gate=["tools/check-parity.py", "--verbose"],
        expect=r"missing from index.html\s*:\s*[1-9]",
        plant=lambda t: replace_once(
            t, "index.html",
            "Definition of Done states what must be true",
            "Definition of Done states what ought to be true"),
    ),
    dict(
        name="parity: the case count restated instead of computed",
        gate=["tools/check-parity.py", "--verbose"],
        expect=r"cases claimed / listed",
        plant=lambda t: sub_once(t, "index.html", r'<b data-cases>9</b>', '<b data-cases>8</b>'),
    ),
    # ---- check-html ------------------------------------------------------
    dict(
        name="html: an element opened and never closed",
        gate=["tools/check-html.py"],
        expect=r"error",
        plant=lambda t: replace_once(
            t, "index.html",
            "<p>Every case in this document resolves to a receipt",
            "<p><span>Every case in this document resolves to a receipt"),
    ),
    # ---- stamp-assets ----------------------------------------------------
    dict(
        name="stamp: the stylesheet reference loses its fingerprint",
        gate=["tools/stamp-assets.py", "--check"],
        expect=r"UNSTAMPED|STALE",
        plant=lambda t: sub_once(t, "index.html", r'/assets/style\.css\?v=[0-9a-f]+', "/assets/style.css"),
    ),
    dict(
        name="stamp: a font inside fonts.css loses its fingerprint",
        gate=["tools/stamp-assets.py", "--check"],
        expect=r"UNSTAMPED|STALE",
        plant=lambda t: sub_once(t, "assets/fonts/fonts.css",
                                 r"geist-latin\.woff2\?v=[0-9a-f]+", "geist-latin.woff2"),
    ),
    dict(
        name="stamp: the page references an asset that does not exist",
        gate=["tools/stamp-assets.py", "--check"],
        expect=r"MISSING",
        plant=lambda t: replace_once(
            t, "index.html", "<title>",
            '<link rel="preload" href="/assets/absent.css?v=0000000000" as="style"><title>'),
    ),
    dict(
        name="stamp: a font file changes and the page keeps the old hash",
        gate=["tools/stamp-assets.py", "--check"],
        expect=r"STALE",
        plant=lambda t: (lambda p: (p, "before", p.write_bytes(p.read_bytes() + b"\x00") or "after"))(
            t / "assets" / "fonts" / "geist-latin.woff2"),
    ),
    # ---- check-pack ------------------------------------------------------
    dict(
        name="pack: a colour literal outside the token block",
        gate=["tools/check-pack.py"],
        expect=r"violation|#c0ffee",
        plant=lambda t: replace_once(
            t, "assets/style.css", "\n.masthead", "\n.plant-probe { color: #c0ffee; }\n.masthead"),
    ),
    # ---- inline-figures --------------------------------------------------
    dict(
        name="figures: an inlined SVG drifts from its source file",
        gate=["tools/inline-figures.py", "--check"],
        expect=r"out of date|STALE|1 slot",
        plant=lambda t: sub_once(t, "index.html", r'<svg ', '<svg data-plant="1" '),
    ),
    dict(
        name="figures: a plate is drawn outside its own canvas",
        gate=["tools/build-figures.py", "--check"],
        expect=r"Traceback|assert|error|leaves",
        plant=lambda t: sub_once(t, "tools/build-figures.py", r'\b960\b', "120"),
    ),
    # ---- network ---------------------------------------------------------
    dict(
        name="links: a cited line range beyond the end of the file",
        gate=["tools/check-links.py"],
        expect=r"unresolved|beyond|not within|1 unresolved",
        network=True,
        plant=lambda t: sub_once(t, "manifesto.md", r"backlog\.md#L21-L22", "backlog.md#L9021-L9022"),
    ),
    dict(
        name="currency: the document claims a state the row no longer has",
        gate=["tools/check-currency.py", "--verbose"],
        expect=r"STALE|stale",
        network=True,
        plant=lambda t: replace_once(t, "tools/check-currency.py",
                                     '"now": "closed",', '"now": "open",'),
    ),
    dict(
        name="currency: an interval printed as a number nobody computed",
        gate=["tools/check-currency.py", "--verbose"],
        expect=r"STALE|is not in the file",
        network=True,
        plant=lambda t: replace_once(t, "manifesto.md",
                                     "for two days and six hours", "for a day and a half"),
    ),
]


def run_case(case, keep_all=False):
    tmp = Path(tempfile.mkdtemp(prefix="podmanifesto-negative-"))
    tree = tmp / "repo"
    shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"))

    path, before, after = case["plant"](tree)
    if before == after:
        print(f"  PLANT DID NOT LAND  {case['name']}")
        print(f"    the file is unchanged: {path.relative_to(tree)}")
        print(f"    tree kept at {tree}")
        return False

    proc = subprocess.run([sys.executable] + case["gate"], cwd=tree,
                          capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    refused = proc.returncode != 0
    named = re.search(case["expect"], out) is not None

    if refused and named:
        line = next((l.strip() for l in out.splitlines() if re.search(case["expect"], l)), "")
        print(f"  refused  {case['name']}")
        if line:
            print(f"    exit {proc.returncode} — {line[:150]}")
        if not keep_all:
            shutil.rmtree(tmp, ignore_errors=True)
        return True

    print(f"  ACCEPTED  {case['name']}")
    print(f"    gate {' '.join(case['gate'])} exited {proc.returncode}"
          f"{'' if refused else ' (a defect passed)'}"
          f"{'' if named else ', and its output never named the defect'}")
    print(f"    tree kept at {tree}")
    for l in out.splitlines()[-6:]:
        print(f"    | {l}")
    return False


def main():
    ap = argparse.ArgumentParser(description="plant a defect per gate; every gate must refuse")
    ap.add_argument("--offline", action="store_true", help="skip the cases that need the API")
    ap.add_argument("--keep", action="store_true", help="keep every workspace, pass or fail")
    ap.add_argument("-k", metavar="SUBSTRING", help="only cases whose name matches")
    a = ap.parse_args()

    has_token = bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    ran = passed = 0
    skipped = []

    for case in CASES:
        if a.k and a.k not in case["name"]:
            continue
        if case.get("network") and (a.offline or not has_token):
            skipped.append(case["name"])
            continue
        ran += 1
        passed += 1 if run_case(case, a.keep) else 0

    for name in skipped:
        print(f"  skipped  {name} — needs GITHUB_TOKEN; a check that cannot look is not a pass")

    gates = sorted({c["gate"][0].split("/")[-1] for c in CASES})
    print(f"\n{passed} of {ran} planted defect(s) refused, across {len(gates)} gates: "
          f"{', '.join(gates)}")
    if skipped:
        print(f"{len(skipped)} case(s) skipped for want of a token — not counted as passes.")
    return 0 if passed == ran else 1


if __name__ == "__main__":
    raise SystemExit(main())
