#!/usr/bin/env python3
"""Every place this document states its version must agree, and match the tag.

The version was written by hand in five places — the masthead, the JSON-LD block,
the topbar, the colophon, and `llms.txt` — which is five chances for four of them
to be right. §5 of the document says a fact with two homes will diverge and a
number carried from an earlier report will decay; the version had six homes and
no check.

It is also the claim that makes the citation policy work. `CHANGELOG.md` promises
that the canonical text does not change without a version, and a reader is asked
to cite `blob/v<version>/manifesto.md`. If the stated version and the newest tag
disagree, either the promise was broken or the tag was forgotten, and the citable
address points at text that is not the text on the page.

Usage:  python3 tools/check-version.py [--verbose]
Exit:   0 = every stated version agrees, and equals the newest tag
        1 = they disagree, or the tag is missing
        2 = the check could not look (no git history here)
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every shape the version is written in, scanned across the whole file rather
# than at listed positions: an enumerated list of sites is a list that goes stale
# the first time somebody writes the version somewhere new, which is the failure
# this gate exists to catch.
PATTERNS = [
    (r'"version":\s*"([0-9]+\.[0-9]+)"', "JSON-LD"),
    (r'topbar__ver">v([0-9]+\.[0-9]+)<', "topbar"),
    (r'<dt>Version</dt><dd>([0-9]+\.[0-9]+)</dd>', "a Version row"),
    (r'POD/001 &#183; v([0-9]+\.[0-9]+)', "a POD/001 signature"),
    (r'\bVersion ([0-9]+\.[0-9]+),', "a prose 'Version N.N,'"),
    (r'^## v([0-9]+\.[0-9]+) — ', "the changelog's newest entry"),
]
FILES = ["index.html", "404.html", "llms.txt", "CHANGELOG.md", "README.md"]

failures = []


def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def newest_tag():
    """The highest v<major>.<minor> tag, or None when there is no tag yet."""
    try:
        out = subprocess.run(["git", "tag", "--list", "v[0-9]*"],
                             cwd=ROOT, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    tags = []
    for t in out.stdout.split():
        m = re.fullmatch(r"v(\d+)\.(\d+)", t.strip())
        if m:
            tags.append((int(m.group(1)), int(m.group(2)), t.strip()))
    return max(tags)[2] if tags else None


def main() -> int:
    verbose = "--verbose" in sys.argv

    found = []          # (version, where)
    for rel in FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, label in PATTERNS:
            for m in re.finditer(pattern, text, re.M):
                line = text.count("\n", 0, m.start()) + 1
                found.append((m.group(1), f"{rel}:{line} ({label})"))
                if verbose:
                    print(f"     {m.group(1):<6} {rel}:{line}  {label}")

    check("the version is stated somewhere", bool(found), "no version found in any file")
    if not found:
        print(f"\n{len(failures)} failure(s)")
        return 1

    stated = sorted({v for v, _ in found})
    check(f"every stated version agrees ({len(found)} place(s))", len(stated) == 1,
          "; ".join(f"{w}={v}" for v, w in found))
    if len(stated) != 1:
        print(f"\n{len(failures)} failure(s)")
        return 1

    version = stated[0]
    tag = newest_tag()
    if tag is None:
        # Before the first tag exists this cannot decide, and a check that cannot
        # look is not a pass.
        print(f"\nthe document states v{version}; no v<major>.<minor> tag exists yet")
        print("a check that cannot look is not a pass")
        return 2

    check("the stated version is the newest tag", tag == f"v{version}",
          f"document says v{version}, newest tag is {tag}")

    # The citable address in CHANGELOG.md and llms.txt must name that same tag.
    for rel in ("CHANGELOG.md", "llms.txt", "README.md"):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "blob/v" in text:
            cited = set(re.findall(r"blob/(v[0-9]+\.[0-9]+)/", text))
            check(f"{rel} cites the current tag", cited == {f"v{version}"},
                  f"cites {', '.join(sorted(cited)) or 'nothing'}, document is v{version}")

    print(f"\nv{version}, stated in {len(found)} place(s) across "
          f"{len({w.split(':')[0] for _, w in found})} file(s), and it is the newest tag")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
