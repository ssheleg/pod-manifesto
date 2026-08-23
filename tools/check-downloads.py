#!/usr/bin/env python3
"""Recompute the adoption figure this page prints, from the registry that owns it.

The colophon states how many times the reference implementation has been
installed. §5 of the document it sits under says a number should be computed
rather than carried from an earlier report, and belief 6 says a number copied
from an earlier report will decay. A hand-typed install count is that failure
exactly, and a fast-moving one: it would be wrong the next morning and would go
on looking authoritative.

Two rules make the figure stable and checkable rather than merely impressive:

  * **The window is closed.** It ends on a day that is over. npm reports the
    current day as a partial count — 0 for hours, then rising — so a window that
    reaches today is a number that changes under the page while nobody edits it.
    This check refuses such a window outright, before it even asks the registry.
  * **The figure is a sum, not a memory.** It is fetched for that exact window
    and added up here. If the page disagrees with the registry, the page is wrong.

The claim is deliberately narrow, and the page says so: an install count is
evidence that the process runs somewhere other than here. It is not evidence
that it runs correctly, and this document is the last place that should confuse
the two.

Usage:  python3 tools/check-downloads.py [--verbose]
        python3 tools/check-downloads.py --self-test   # the rules, offline
Exit:   0 = the printed figure is what the registry reports for its window
        1 = it is not, or the window is not closed
        2 = the registry could not be reached
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
API = "https://api.npmjs.org/downloads/range/{start}:{end}/{pkg}"
TIMEOUT = 30

# <b data-installs data-pkg="…" data-from="…" data-to="…">21,951</b>
CLAIM = re.compile(
    r'<b data-installs\s+data-pkg="(?P<pkg>[^"]+)"\s+'
    r'data-from="(?P<start>\d{4}-\d{2}-\d{2})"\s+'
    r'data-to="(?P<end>\d{4}-\d{2}-\d{2})">(?P<figure>[\d,   ]+)</b>')

failures = []


def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


# --------------------------------------------------------------------------
# The rules, as pure functions, so they can be decided without the network.
# --------------------------------------------------------------------------
def parse_figure(text: str) -> int:
    """The printed number, however it is spaced or grouped."""
    return int(re.sub(r"[^\d]", "", text))


def window_is_closed(end: str, today: date) -> bool:
    """A window may not reach today: npm counts the current day as it happens."""
    return date.fromisoformat(end) < today


def window_days(start: str, end: str) -> int:
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


def total(points) -> int:
    return sum(p["downloads"] for p in points)


def self_test() -> int:
    today = date(2026, 8, 23)
    cases = [
        ("a grouped figure parses to its number",
         lambda: parse_figure("21,951") == 21951),
        ("a thin-space figure parses the same",
         lambda: parse_figure("21 951") == 21951),
        ("yesterday closes a window",
         lambda: window_is_closed("2026-08-22", today) is True),
        ("today does not close a window",
         lambda: window_is_closed("2026-08-23", today) is False),
        ("tomorrow certainly does not",
         lambda: window_is_closed("2026-08-24", today) is False),
        ("a window is counted inclusively at both ends",
         lambda: window_days("2026-07-28", "2026-08-22") == 26),
        ("a single day is one day",
         lambda: window_days("2026-08-22", "2026-08-22") == 1),
        ("the total is the sum of its days",
         lambda: total([{"downloads": 3}, {"downloads": 4}, {"downloads": 0}]) == 7),
        ("an empty window totals nothing",
         lambda: total([]) == 0),
    ]
    bad = 0
    for name, fn in cases:
        try:
            ok = fn()
        except Exception as e:
            ok, name = False, f"{name} — raised {e!r}"
        print(f"  self-test [{name}]: {'ok' if ok else 'FAILED'}")
        bad += 0 if ok else 1
    if bad:
        print(f"\nSELF-TEST FAIL: {bad} of {len(cases)} rules did not decide their case.")
        return 1
    print(f"\nSELF-TEST PASS: {len(cases)} rules, each fed a case it must decide.")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    verbose = "--verbose" in sys.argv

    doc = PAGE.read_text(encoding="utf-8")
    m = CLAIM.search(doc)
    if not m:
        print("index.html states no install figure — nothing to verify, and the "
              "colophon claims one")
        return 1

    pkg, start, end = m.group("pkg"), m.group("start"), m.group("end")
    printed = parse_figure(m.group("figure"))

    check("the window is closed", window_is_closed(end, date.today()),
          f"{end} is today or later; npm counts the current day as it happens, "
          "so this figure would change under the page")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1

    try:
        req = urllib.request.Request(
            API.format(start=start, end=end, pkg=pkg),
            headers={"User-Agent": "pod-manifesto-downloads-check/1.0 "
                                   "(+https://podmanifesto.org)"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"the registry could not be reached — a check that cannot look is "
              f"not a pass\n  {e}")
        return 2

    actual = total(data.get("downloads", []))
    days = window_days(start, end)

    if verbose:
        live = [p for p in data.get("downloads", []) if p["downloads"]]
        print(f"     {pkg}  {start} .. {end}  ({days} days, "
              f"{len(live)} with installs, peak {max((p['downloads'] for p in live), default=0)}/day)")

    check(f"the printed figure is what npm reports", printed == actual,
          f"the page says {printed:,}, the registry says {actual:,} "
          f"for {pkg} over {start}..{end}")

    print(f"\n{printed:,} installs of {pkg} across {days} closed day(s), recomputed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
