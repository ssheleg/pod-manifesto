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


def plant_stale_published_date(tree):
    """Give the copy a history, bring every date true, then falsify one.

    `stamp-dates.py` derives its answer from `git log`, and the case tree is
    copied without `.git` — so a naive plant makes the gate exit 2 ("a check that
    cannot look is not a pass") and the case would record a refusal it did not
    earn. The gate must refuse the *date*, not the missing repository.

    Three steps, in this order: commit a baseline so the log exists; run the
    stamper so every published date equals what this new history says; then
    falsify one `lastmod`. The only staleness left in the tree is the plant.
    """
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "negatives", "GIT_AUTHOR_EMAIL": "negatives@example.invalid",
           "GIT_COMMITTER_NAME": "negatives", "GIT_COMMITTER_EMAIL": "negatives@example.invalid"}
    git = lambda *a: subprocess.run(["git", *a], cwd=tree, env=env,
                                    capture_output=True, text=True, check=True)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "baseline")
    subprocess.run([sys.executable, "tools/stamp-dates.py"], cwd=tree,
                   capture_output=True, text=True)
    git("add", "-A")
    git("commit", "-q", "--allow-empty", "-m", "dates stamped to this history")

    return sub_once(tree, "sitemap.xml",
                    r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
                    "<lastmod>2019-01-01</lastmod>")


def plant_swapped_sections(tree):
    """Swap two section headings on the page, leaving the canonical text alone.

    The forward pass cannot see this: every sentence is still present, just in a
    different place. On 2026-08-23 the document's whole assertion moved to the
    front, and had that move landed in one file and not the other, every gate here
    would have stayed green.
    """
    p = tree / "index.html"
    before = p.read_text(encoding="utf-8")
    a = '<h2 class="sec__h">The three graphs '
    b = '<h2 class="sec__h">Bounded autonomy '
    if a not in before or b not in before:
        return p, before, before
    after = before.replace(a, "@@SWAP@@", 1).replace(b, a, 1).replace("@@SWAP@@", b, 1)
    p.write_text(after, encoding="utf-8")
    return p, before, after


def plant_version_ahead_of_tag(tree):
    """Tag the current release, then bump every stated version to 9.9 consistently.

    The interesting failure is not two files disagreeing; that is the case above.
    It is the whole document agreeing on a version no tag carries, because then
    `blob/v9.9/manifesto.md` — the address a reader is told to cite — resolves to
    nothing. The copy is tagged first so the gate is refusing the version rather
    than the missing repository.
    """
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "negatives", "GIT_AUTHOR_EMAIL": "negatives@example.invalid",
           "GIT_COMMITTER_NAME": "negatives", "GIT_COMMITTER_EMAIL": "negatives@example.invalid"}
    git = lambda *a: subprocess.run(["git", *a], cwd=tree, env=env,
                                    capture_output=True, text=True, check=True)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "baseline")
    changelog = (tree / "CHANGELOG.md").read_text(encoding="utf-8")
    current_match = re.search(r"^## v([0-9]+\.[0-9]+)(?:\s*[—:]\s*)", changelog, re.M)
    current = current_match.group(1) if current_match else "1.0"
    git("tag", f"v{current}")

    changed, first = 0, None
    for rel in ("index.html", "llms.txt", "CHANGELOG.md", "README.md"):
        p = tree / rel
        if not p.exists():
            continue
        before = p.read_text(encoding="utf-8")
        after = (before.replace(f'"version": "{current}"', '"version": "9.9"')
                       .replace(f'topbar__ver">v{current}<', 'topbar__ver">v9.9<')
                       .replace(f"<dt>Version</dt><dd>{current}</dd>", "<dt>Version</dt><dd>9.9</dd>")
                       .replace(f"POD/001 &#183; v{current}", "POD/001 &#183; v9.9")
                       .replace(f"Version {current},", "Version 9.9,")
                       .replace(f"## v{current} — ", "## v9.9 — ")
                       .replace(f"## v{current}: ", "## v9.9: ")
                       .replace(f"blob/v{current}/", "blob/v9.9/"))
        if after != before:
            p.write_text(after, encoding="utf-8")
            changed += 1
            if first is None:
                first = (p, before, after)
    return first if first else (tree / "index.html", "", "")


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
    # ---- stamp-dates -----------------------------------------------------
    # The ninth gate, and the last one to get a control. Between 2026-08-19 and
    # 2026-08-23 this file covered eight of the nine tools while `README.md:75`
    # described it as covering "every gate above" — with `stamp-dates.py` listed
    # three lines above that sentence. The gate was green the whole time and
    # nobody had watched it go red.
    dict(
        name="dates: a published lastmod the git history contradicts",
        gate=["tools/stamp-dates.py", "--check"],
        expect=r"STALE",
        plant=plant_stale_published_date,
    ),
    dict(
        name="parity: the page grows a paragraph the canonical text never had",
        gate=["tools/check-parity.py", "--verbose"],
        expect=r"with no canonical source\s*:\s*[1-9]",
        plant=lambda t: replace_once(
            t, "index.html",
            '<section id="learns" class="sec reveal">',
            '<section id="learns" class="sec reveal">\n  <p>This paragraph exists only on '
            'the page and in no canonical source, which is the state the reverse pass was '
            'built to refuse.</p>'),
    ),
    dict(
        name="parity: the page states the sections in a different order",
        gate=["tools/check-parity.py", "--verbose"],
        expect=r"section order.*MISMATCH|ORDER: position",
        plant=plant_swapped_sections,
    ),
    # ---- check-version ---------------------------------------------------
    # The version is written in nine places. Nine chances for eight to be right.
    dict(
        name="version: one of the nine statements of the version disagrees",
        gate=["tools/check-version.py"],
        expect=r"every stated version agrees|do not agree",
        plant=lambda t: sub_once(
            t, "index.html",
            r'(<dt>Version</dt><dd>)[0-9]+\.[0-9]+(</dd>)',
            r'\g<1>9.8\g<2>'),
    ),
    dict(
        name="version: every statement agrees, and none of them is the tag",
        gate=["tools/check-version.py"],
        expect=r"the stated version is the newest tag",
        plant=lambda t: plant_version_ahead_of_tag(t),
    ),
    # ---- check-downloads --------------------------------------------------
    # The colophon prints an install count. A hand-typed one decays the next
    # morning and goes on looking authoritative, which is what §5 forbids.
    dict(
        name="downloads: the printed install count is not what npm reports",
        gate=["tools/check-downloads.py"],
        expect=r"the printed figure is what npm reports|the registry says",
        network=True,
        plant=lambda t: sub_once(t, "index.html",
                                 r'(<b data-installs[^>]*>)[\d,   ]+(</b>)',
                                 r"\g<1>999,999\g<2>"),
    ),
    dict(
        name="downloads: the window reaches a day that is not over",
        gate=["tools/check-downloads.py"],
        expect=r"the window is closed",
        plant=lambda t: sub_once(t, "index.html",
                                 r'(<b data-installs[^>]*data-to=")\d{4}-\d{2}-\d{2}(")',
                                 r"\g<1>2099-01-01\g<2>"),
    ),
    dict(
        name="downloads: the window ends on a day npm has not finished counting",
        gate=["tools/check-downloads.py"],
        expect=r"has been counted|has not finished counting",
        network=True,
        plant=lambda t: sub_once(t, "index.html",
                                 r'(<b data-installs[^>]*data-to=")\d{4}-\d{2}-\d{2}(")',
                                 r"\g<1>2026-08-24\g<2>"),
    ),
    dict(
        name="downloads: the colophon drops the figure it claims to carry",
        gate=["tools/check-downloads.py"],
        expect=r"states no install figure",
        plant=lambda t: sub_once(t, "index.html", r"<b data-installs", "<b data-removed"),
    ),
    # ---- render ----------------------------------------------------------
    # The defect this gate was built for, put back. Without the print reset the
    # twelve sections stay at `opacity: 0`, printing never scrolls, and the
    # document goes to paper as 30 pages of running header. Every file-reading
    # gate in this repository stayed green through that for four days.
    dict(
        name="render: the print reset removed, and the document prints blank",
        gate=["tools/check-render.py"],
        expect=r"below the \d+ character floor|below the \d+ floor|did not render|absent from the printed",
        browser=True,
        plant=lambda t: sub_once(
            t, "assets/style.css",
            r"\n  \.reveal, \.boot > \* \{ opacity: 1 !important; transform: none !important; \}",
            ""),
    ),
    dict(
        name="render: a quiet ink dropped under the contrast floor",
        gate=["tools/check-render.py"],
        expect=r"below the WCAG AA floor",
        browser=True,
        plant=lambda t: replace_once(t, "assets/style.css",
                                     "--faint:      #7a897f;", "--faint:      #2c332e;"),
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
        name="links: an npm package that was never published",
        gate=["tools/check-links.py"],
        expect=r"unresolved|from the registry",
        network=True,
        plant=lambda t: replace_once(t, "index.html",
                                     "https://www.npmjs.com/package/sshlg-skills",
                                     "https://www.npmjs.com/package/sshlg-skills-not-a-real-pkg-9x7"),
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
    shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(
        ".git", "*.pyc", "__pycache__", ".preview"))

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
    # A browser case that runs without a browser would report the gate's "cannot
    # look" exit as a refusal it never earned — the exact false green this file
    # exists to prevent. Detect it the way the gate itself does.
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "check_render", ROOT / "tools" / "check-render.py")
        cr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cr)
        has_browser = bool(cr.find_chrome()) and bool(shutil.which("pdftotext"))
    except Exception:
        has_browser = False

    ran = passed = 0
    skipped = []

    for case in CASES:
        if a.k and a.k not in case["name"]:
            continue
        if case.get("network") and (a.offline or not has_token):
            skipped.append(f"{case['name']} — needs GITHUB_TOKEN")
            continue
        if case.get("browser") and not has_browser:
            skipped.append(f"{case['name']} — needs a browser and pdftotext")
            continue
        ran += 1
        passed += 1 if run_case(case, a.keep) else 0

    for name in skipped:
        print(f"  skipped  {name}; a check that cannot look is not a pass")

    gates = sorted({c["gate"][0].split("/")[-1] for c in CASES})
    print(f"\n{passed} of {ran} planted defect(s) refused, across {len(gates)} gates: "
          f"{', '.join(gates)}")
    if skipped:
        print(f"{len(skipped)} case(s) skipped for want of a token — not counted as passes.")
    return 0 if passed == ran else 1


if __name__ == "__main__":
    raise SystemExit(main())
