#!/usr/bin/env python3
"""Prove that a citation this document *characterises* still says what is claimed of it.

`check-links.py` answers one question: does the address resolve? That question has a
green answer for a permalink forever, because a permalink is pinned to a commit and a
commit does not change. It is the wrong question to ask alone.

On 2026-08-17 this repository shipped a paragraph asserting that four requirements were
"filed as open backlog rows", with two permalinks as the receipt (`790f053`, 05:05+02).
Three of the four rows closed the same day, the first at 11:49+02, and the paragraph was
not corrected until `4b3694d` on 2026-08-19 at 18:01+02 — two days and six hours later.
Both permalinks resolved throughout. `check-links` was green. The receipt confirmed a belief that had stopped being true, which is a worse
failure than a dead link: a reader who follows a dead link knows to distrust it.

So resolution and **currency** are two properties, and this repository had a mechanism for
only the first. This is the second.

A claim here has two ends and both are checked:

  pinned  — what the cited range said at the commit the document points at. This is what
            the document is entitled to describe, and it must still be true, or the
            citation has been mis-transcribed.
  current — what that same row says on the default branch today. The document must not
            contradict it.

Usage:
    python3 tools/check-currency.py              # check every registered claim
    python3 tools/check-currency.py --self-test  # plant a defect in each rule, offline
    python3 tools/check-currency.py --verbose

Exit:
    0 = every registered claim is both correctly transcribed and current
    1 = at least one claim is stale, mis-transcribed, or unreadable
    2 = the check could not look (no network, no token, an API error)

Exit 2 is deliberately not exit 0. A check that cannot look must never read as one that
looked — the same rule `check_no_member_holds_a_commit_the_remote_does_not` follows in
the sshlg-skills umbrella, which discloses rather than passing.

Network: reads the GitHub API. `GITHUB_TOKEN` is used when present, because github.com
answers anonymous blob requests with a 404 once it throttles, and a check that measures
the rate limit instead of its subject is worthless. The self-test needs no network.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
# This repository, for the interval endpoints. Read from the local git when there
# is one and from the API when there is not — `tools/negatives.py` runs the gates
# against a copy of the tree with no `.git`, and a check that cannot look there
# would report exit 2 for a reason that has nothing to do with its subject.
SELF_REPO = "ssheleg/pod-manifesto"

# ---------------------------------------------------------------------------
# The registry. One entry per claim this document makes ABOUT a cited artifact.
#
# `rows`     the row ids the document characterises
# `pinned`   (repo, commit, path) the document's permalink points at
# `says`     what the document asserts those rows said AT THE PIN
# `now`      what the document asserts is true TODAY on the default branch
# `where`    the documents carrying the claim, so a failure names what to edit
#
# Adding a claim here is the cost of citing a mutable record. That cost is the point:
# a citation nobody registered is a citation nobody re-reads.
# ---------------------------------------------------------------------------
CLAIMS = [
    {
        "id": "four-named-requirements",
        "rows": ["B-076", "B-077", "B-080", "B-081"],
        "pinned": (
            "ssheleg/task-pipeline",
            "404fd09afd919d57834a095d05ddaa4f0d693d9c",
            "docs/evidence/backlog.md",
        ),
        "says": "open",
        "now": "closed",
        "where": ["manifesto.md", "index.html", "llms.txt"],
    },
]

STATE_WORDS = ("open", "closed", "parked", "dropped")

# ---------------------------------------------------------------------------
# Intervals. A duration in the prose is a computed quantity like any other, and
# this document learned that the hard way twice: the paragraph about a stale
# receipt carried "a day and a half" against commit timestamps that give two days
# and six hours. A restated interval is a restated number — the class §5 of the
# manifesto forbids — so each one is registered here with its two endpoints and
# recomputed from the commits themselves.
#
# `start` and `end` are (repo, sha); the repo "self" means this repository, read
# from the local git rather than the API.
# ---------------------------------------------------------------------------
INTERVALS = [
    {
        "id": "stale-receipt-window",
        "what": "how long the receipt confirmed a belief that had stopped being true",
        # the first of the four rows closing is when the claim went false
        "start": ("ssheleg/task-pipeline", "fbd8a67e6988a0893f273eb37bd9a075a036c223"),
        # the commit that corrected the paragraph is when it stopped being false
        "end": ("self", "4b3694d"),
        "where": ["manifesto.md", "index.html"],
    },
]

WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve")


def render_interval(seconds):
    """The phrase the document is allowed to print for a duration.

    Floors to whole hours deliberately: a document that says "two days and six hours"
    should not have to be re-edited every time a minute is recounted. Rendering and
    checking share this one function, so the prose cannot drift from the arithmetic.
    """
    days, rem = divmod(int(seconds), 86400)
    hours = rem // 3600

    def word(n):
        return WORDS[n] if n < len(WORDS) else str(n)

    parts = []
    if days:
        parts.append(f"{word(days)} day" + ("s" if days != 1 else ""))
    if hours or not days:
        parts.append(f"{word(hours)} hour" + ("s" if hours != 1 else ""))
    return " and ".join(parts)


def commit_date(repo, sha, token):
    """The committer date of a commit, as an aware datetime, or (None, reason)."""
    if repo == "self":
        try:
            out = subprocess.run(["git", "show", "-s", "--format=%cI", sha],
                                 cwd=ROOT, capture_output=True, text=True, check=True)
            return datetime.fromisoformat(out.stdout.strip()), None
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
            repo = SELF_REPO                        # no git here; ask the API instead
    url = f"{API}/repos/{repo}/commits/{sha}"
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "podmanifesto-check-currency"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            body = json.load(r)
        return datetime.fromisoformat(body["commit"]["committer"]["date"].replace("Z", "+00:00")), None
    except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
        return None, f"unreachable ({e})"


def check_intervals(token, verbose=False):
    """Every registered interval is recomputed and must appear, so worded, in its surfaces."""
    problems, unlooked = [], []
    for iv in INTERVALS:
        start, why = commit_date(*iv["start"], token)
        if start is None:
            unlooked.append(f"{iv['id']}: start {iv['start'][1][:7]} — {why}")
            continue
        end, why = commit_date(*iv["end"], token)
        if end is None:
            unlooked.append(f"{iv['id']}: end {iv['end'][1][:7]} — {why}")
            continue
        phrase = render_interval((end - start).total_seconds())
        for surface in iv["where"]:
            text = (ROOT / surface).read_text(encoding="utf-8")
            if phrase not in text:
                problems.append(f"{surface}: {iv['id']} computes to \"{phrase}\" "
                                f"({iv['start'][1][:7]} -> {iv['end'][1][:7]}), "
                                f"and that phrase is not in the file")
            elif verbose:
                print(f"  {surface}: {iv['id']} = {phrase} — as printed")
    return problems, unlooked


def fetch(repo, ref, path, token):
    """Raw file bytes at a ref, or (None, reason) when the check could not look."""
    url = f"{API}/repos/{repo}/contents/{path}?ref={ref}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.raw",
        "User-Agent": "podmanifesto-check-currency",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return None, f"unreachable ({e})"


def row_state(text, row_id):
    """The state word of a board row, or None when the row or its state is unreadable.

    Two things here were got wrong first and are worth stating, because both are the
    kind of mistake that reads as a pass:

    1. **The state is read from the State COLUMN, located by the table's own header** —
       not from anywhere on the line. Searching the whole row finds words in prose: a
       row's *What* cell legitimately contains "open" when it describes what was open.
    2. **Within that cell the FIRST state word wins.** A closed row keeps its history in
       the same cell — `**closed 2026-08-17** — the row was open until ...` — so taking
       the last match reads the wrong end of the row's own story. The first version of
       this function took the last match, passed on every real row by luck, and was
       caught by its own planted case rather than by review.

    Falls back to the last cell when no header is found, which is what a small fixture
    table looks like.
    """
    state_col = None
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [re.sub(r"[*`]", "", c).strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue

        if state_col is None and any(c.lower() == "state" for c in cells):
            state_col = next(i for i, c in enumerate(cells) if c.lower() == "state")
            continue

        if cells[0] != row_id:
            continue

        idx = state_col if state_col is not None and state_col < len(cells) else len(cells) - 1
        found = re.findall(r"\b(%s)\b" % "|".join(STATE_WORDS), cells[idx], re.I)
        return found[0].lower() if found else None
    return None


def check(verbose=False):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    problems, unlooked = [], []

    for claim in CLAIMS:
        repo, commit, path = claim["pinned"]
        where = ", ".join(claim["where"])

        pinned_text, why = fetch(repo, commit, path, token)
        if pinned_text is None:
            unlooked.append(f"{claim['id']}: pinned {repo}@{commit[:7]} — {why}")
            continue
        head_text, why = fetch(repo, "HEAD", path, token)
        if head_text is None:
            unlooked.append(f"{claim['id']}: default branch of {repo} — {why}")
            continue

        for row in claim["rows"]:
            was = row_state(pinned_text, row)
            now = row_state(head_text, row)

            if was is None:
                problems.append(
                    f"{claim['id']}/{row}: not readable at the pinned commit "
                    f"{commit[:7]} — the citation names a row that is not there, so the "
                    f"claim in {where} has no receipt")
            elif was != claim["says"]:
                problems.append(
                    f"{claim['id']}/{row}: {where} says the pinned range reads "
                    f"'{claim['says']}', but at {commit[:7]} it reads '{was}' — the "
                    f"citation is mis-transcribed")
            elif verbose:
                print(f"ok   {row} at {commit[:7]}: {was}")

            if now is None:
                problems.append(
                    f"{claim['id']}/{row}: not readable on the default branch of {repo} "
                    f"— {where} asserts it is now '{claim['now']}' and nothing can "
                    f"confirm that")
            elif now != claim["now"]:
                problems.append(
                    f"{claim['id']}/{row}: {where} asserts '{claim['now']}' today, but "
                    f"the default branch of {repo} reads '{now}'. The permalink still "
                    f"resolves, which is exactly why this is not caught by a link check")
            elif verbose:
                print(f"ok   {row} today: {now}")

    for u in unlooked:
        print(f"unlooked: {u}")
    for p in problems:
        print(f"FAIL {p}")

    if problems:
        print(f"\n{len(problems)} stale or mis-transcribed claim(s).")
        return 1
    if unlooked:
        print(f"\nCould not look at {len(unlooked)} claim(s). Not a pass.")
        return 2
    iv_problems, iv_unlooked = check_intervals(token, verbose)
    for u in iv_unlooked:
        print(f"  unlooked: {u}")
    for pr in iv_problems:
        print(f"  STALE: {pr}")
    if iv_problems:
        print(f"\n{len(iv_problems)} interval(s) printed a number the commits do not give.")
        return 1
    if iv_unlooked:
        print(f"\n{len(iv_unlooked)} interval(s) could not be recomputed — exit 2, not 0.")
        return 2

    n = sum(len(c["rows"]) for c in CLAIMS)
    print(f"{n} cited row(s) across {len(CLAIMS)} claim(s): correctly transcribed and current.")
    print(f"{len(INTERVALS)} interval(s): recomputed from their endpoint commits and printed as computed.")
    return 0


# ---------------------------------------------------------------------------
# Self-test. Offline, and every rule is fed a defect it must reject — a guard that
# has not been watched failing is not evidence.
# ---------------------------------------------------------------------------
BOARD_PINNED = """
| id | What | State |
|---|---|---|
| B-076 | judgment gates | open |
| B-080 | per-node checks | open |
"""

BOARD_TODAY = """
| id | What | State |
|---|---|---|
| B-076 | judgment gates | **closed 2026-08-17** — the row was open until the schema grew a `judge` |
| B-080 | per-node checks | open |
"""

PLANTS = [
    ("a row that is absent at the pinned commit",
     lambda: row_state(BOARD_PINNED, "B-099") is None),
    ("a row whose state cell carries no state word",
     lambda: row_state("| id |\n|---|\n| B-076 | judgment gates | |", "B-076") is None),
    ("a closed row read from the wrong end of its own story",
     lambda: row_state(BOARD_TODAY, "B-076") == "closed"),
    ("a row still open today where the document claims closed",
     lambda: row_state(BOARD_TODAY, "B-080") == "open"),
    ("the pinned state read correctly",
     lambda: row_state(BOARD_PINNED, "B-076") == "open"),
    ("an interval rounded up instead of floored to the hour",
     lambda: render_interval(2 * 86400 + 6 * 3600 + 3599) == "two days and six hours"),
    ("a sub-day interval rendered as days",
     lambda: render_interval(5 * 3600) == "five hours"),
    ("the interval this document actually prints",
     lambda: render_interval(195714) == "two days and six hours"),
    ("a singular hour printed as a plural",
     lambda: render_interval(86400 + 3600) == "one day and one hour"),
]


def self_test():
    bad = 0
    for name, holds in PLANTS:
        ok = False
        try:
            ok = bool(holds())
        except Exception as e:                       # noqa: BLE001 - a raising rule is a failing rule
            print(f"  self-test [{name}]: RAISED {e!r}")
        print(f"  self-test [{name}]: {'ok' if ok else 'MISSED'}")
        bad += 0 if ok else 1
    if bad:
        print(f"\nSELF-TEST FAIL: {bad} of {len(PLANTS)} rules did not behave as designed.")
        return 1
    print(f"\nSELF-TEST PASS: {len(PLANTS)} rules, each fed a case it must decide.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="offline; plant a defect per rule")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    sys.exit(self_test() if a.self_test else check(a.verbose))
