#!/usr/bin/env python3
"""Check the published site, not the repository that produced it.

Every other gate here reads the working tree. That leaves a class of defect no
gate can see: the one introduced *between* the commit and the reader. Two of
them were found by hand on 2026-08-23, and both had been live for days with all
eleven checks green.

  * `robots.txt` in this repository is 184 bytes and says the second reader — the
    machine — is welcome. The edge was serving 2 020 bytes, because Cloudflare's
    managed robots.txt was switched on and prepended a block disallowing
    ClaudeBot, GPTBot, CCBot, Google-Extended and five others, with
    `Content-Signal: ai-train=no`. The file in git said one thing; the file on the
    internet said the opposite; nothing compared them.
  * a deploy can silently serve an older commit, and the fingerprints in the page
    are only proof against *caches*, not against a deploy that never landed.

So this gate fetches what a reader gets and compares it to what the repository
says a reader should get. It needs the network and it is the only check here
that does; it belongs after a deploy, not before one.

Usage:  python3 tools/check-live.py [--origin URL] [--verbose]
        python3 tools/check-live.py --expect-commit <sha>   # deploy must be this
Exit:   0 = the published site matches the repository
        1 = it does not
        2 = the site could not be reached at all
"""

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORIGIN = "https://podmanifesto.org"
UA = {"User-Agent": "pod-manifesto-live-check/1.0 (+https://podmanifesto.org)"}
TIMEOUT = 30

failures = []
notes = []


# --------------------------------------------------------------------------
# The robots comparison, as pure functions so they can be fed planted cases
# offline. The gate needs the network; its rules must not.
# --------------------------------------------------------------------------
def robots_differs(live: bytes, repo: bytes) -> bool:
    return live.strip() != repo.strip()


def agents_disallowed(live: bytes):
    """Every user-agent the edge blocks outright."""
    return [x.decode() for x in
            re.findall(rb"(?im)^User-agent:\s*(\S+)\s*\n\s*Disallow:\s*/\s*$", live)]


def training_denied(live: bytes) -> bool:
    m = re.search(rb"(?im)^Content-Signal:\s*(.+)$", live)
    return bool(m and b"ai-train=no" in m.group(1))


BEACON_TAG = re.compile(
    r'<script\b[^>]*\bsrc="https://static\.cloudflareinsights\.com/[^"]*"[^>]*>\s*</script>')


def beacon_count(page: str) -> int:
    """How many analytics beacons the reader actually received.

    Exactly one is the answer. Zero means nothing is counted. Two means every
    visit is counted twice, and a number that is wrong by a factor is worse than
    no number, because it will be believed.

    Two can happen here without anyone editing the page: the zone's Web Analytics
    is bound to the zone with automatic injection, which Cloudflare's API refuses
    to switch off (`autoInstallRequired`), and the edge intermittently adds its own
    tag on top of the one in the file. Observed on 2026-08-23: the served page was
    359 bytes larger than the committed one for one deploy and identical for the
    next.
    """
    return len(BEACON_TAG.findall(page))


def beacon_present(page: str) -> bool:
    return beacon_count(page) >= 1


def without_beacon(page: str) -> str:
    """The page with every analytics tag removed, for comparing document bytes.

    The byte comparison asks whether the deploy landed. An analytics tag the edge
    may or may not have added is a different question, asked and answered directly
    above — folding the two together makes a real staleness look like injection and
    an injection look like staleness.
    """
    return re.sub(r"\s*" + BEACON_TAG.pattern, "", page)


def off_origin(page: str, origin_host: str = "podmanifesto.org"):
    """Hosts the browser will GO AND FETCH, not hosts merely linked to.

    A hyperlink to github.com is not a request. Counting one would make the claim
    "exactly one off-origin request" fail on a document full of citations, which is
    how a check earns the habit of being ignored.
    """
    urls = set()
    for pat in (r'<script\b[^>]*\bsrc="([^"]+)"',
                r'<link\b[^>]*\brel="(?:stylesheet|preload|icon)"[^>]*\bhref="([^"]+)"',
                r'<link\b[^>]*\bhref="([^"]+)"[^>]*\brel="(?:stylesheet|preload|icon)"',
                r'<img\b[^>]*\bsrc="([^"]+)"'):
        urls |= {m.group(1) for m in re.finditer(pat, page)}
    return sorted({urllib.parse.urlsplit(u).netloc for u in urls
                   if u.startswith("http")} - {origin_host})


def self_test() -> int:
    """Each rule above, fed a case it must decide. No network, no deploy.

    The cases are the real ones: the Cloudflare managed block exactly as it was
    served on 2026-08-23, and the repository's own file.
    """
    repo = (ROOT / "robots.txt").read_bytes()
    local_page = (ROOT / "index.html").read_text(encoding="utf-8")
    plain = ('<link rel="stylesheet" href="/assets/style.css?v=1">'
             '<a href="https://github.com/ssheleg/pod-manifesto">Source</a>'
             '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>')
    with_beacon = (plain + '<script defer src="https://static.cloudflareinsights.com/'
                   'beacon.min.js" data-cf-beacon=\'{"token": "x"}\'></script>')
    cloudflare = (b"# BEGIN Cloudflare Managed content\n\n"
                  b"User-agent: *\n"
                  b"Content-Signal: search=yes,ai-train=no,use=reference\n"
                  b"Allow: /\n\n"
                  b"User-agent: ClaudeBot\nDisallow: /\n\n"
                  b"User-agent: GPTBot\nDisallow: /\n\n"
                  b"# END Cloudflare Managed Content\n\n") + repo

    cases = [
        ("the served file equals the repository's",
         lambda: robots_differs(repo, repo) is False),
        ("a prepended edge block is a difference",
         lambda: robots_differs(cloudflare, repo) is True),
        ("trailing whitespace alone is not a difference",
         lambda: robots_differs(repo + b"\n\n", repo) is False),
        ("the blocked agents are named, not merely counted",
         lambda: agents_disallowed(cloudflare) == ["ClaudeBot", "GPTBot"]),
        ("a file that blocks nobody names nobody",
         lambda: agents_disallowed(repo) == []),
        ("ai-train=no is read as a restriction",
         lambda: training_denied(cloudflare) is True),
        ("a file with no content signal restricts nothing",
         lambda: training_denied(repo) is False),
        ("a permissive content signal is not a restriction",
         lambda: training_denied(b"Content-Signal: search=yes,ai-train=yes\n") is False),

        # The beacon rules, fed the page shapes they must tell apart. Analytics was
        # enabled with automatic injection on while the served HTML was byte-identical
        # to the file in git — configuration reporting green over no measurement.
        ("one beacon is counted as one",
         lambda: beacon_count(with_beacon) == 1),
        ("a page without the beacon counts none",
         lambda: beacon_count(plain) == 0),
        ("an edge-injected second beacon is counted, not absorbed",
         lambda: beacon_count(with_beacon + with_beacon) == 2),
        ("removing the beacons leaves the document itself",
         lambda: without_beacon(with_beacon) == without_beacon(plain) == plain),
        ("a hyperlink to another host is not a request",
         lambda: off_origin(plain) == []),
        ("a script from another host is a request",
         lambda: off_origin(with_beacon) == ["static.cloudflareinsights.com"]),
        ("a stylesheet from a CDN would be caught",
         lambda: off_origin('<link rel="stylesheet" href="https://cdn.example.com/a.css">')
                 == ["cdn.example.com"]),
        ("this repository's own page satisfies both rules",
         lambda: beacon_present(local_page)
                 and off_origin(local_page) == ["static.cloudflareinsights.com"]),
    ]

    bad = 0
    for name, fn in cases:
        try:
            ok = fn()
        except Exception as e:                                   # a rule that throws decides nothing
            ok, name = False, f"{name} — raised {e!r}"
        print(f"  self-test [{name}]: {'ok' if ok else 'FAILED'}")
        bad += 0 if ok else 1

    if bad:
        print(f"\nSELF-TEST FAIL: {bad} of {len(cases)} rules did not decide their case.")
        return 1
    print(f"\nSELF-TEST PASS: {len(cases)} rules, each fed a case it must decide.")
    return 0


def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def fetch(url, retries=3):
    """Return (status, bytes). A 5xx is retried; the edge 503s under deploy."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == retries - 1:
                return e.code, e.read() if e.fp else b"", dict(e.headers or {})
            last = e
        except Exception as e:                       # DNS, TLS, timeout
            last = e
    raise RuntimeError(f"{url}: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description="compare the published site to this repository")
    ap.add_argument("--origin", default=DEFAULT_ORIGIN)
    ap.add_argument("--expect-commit", help="fail unless the deployed page matches this commit's index.html")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="run the robots rules offline against planted cases")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    origin = a.origin.rstrip("/")

    # ---- the document is served at all -----------------------------------
    try:
        status, body, headers = fetch(f"{origin}/")
    except RuntimeError as e:
        print(f"the site could not be reached — a check that cannot look is not a pass\n  {e}")
        return 2
    check("the document is served", status == 200, f"HTTP {status}")
    if status != 200:
        return 1

    # ---- the deployed page is the committed page -------------------------
    # A fingerprint proves no cache answered with old bytes. It does not prove
    # the deploy landed: both sides can be consistently stale.
    local_page = (ROOT / "index.html").read_text(encoding="utf-8")
    served = body.decode("utf-8", "replace")
    same = without_beacon(served) == without_beacon(local_page)
    check("the deployed document is the committed document", same,
          f"live {len(served)} chars vs repository {len(local_page)}, beacons aside; "
          "the deploy has not landed, or the checkout is not the deployed commit")

    # ---- robots.txt says what the repository says ------------------------
    # The check that would have caught the edge rewriting this file.
    local_robots = (ROOT / "robots.txt").read_bytes()
    _, live_robots, _ = fetch(f"{origin}/robots.txt")
    robots_same = not robots_differs(live_robots, local_robots)
    detail = ""
    if not robots_same:
        extra = sorted(set(re.findall(rb"(?im)^User-agent:\s*(\S+)", live_robots))
                       - set(re.findall(rb"(?im)^User-agent:\s*(\S+)", local_robots)))
        detail = (f"live {len(live_robots)} bytes vs repository {len(local_robots)}"
                  + (f"; agents the repository never named: "
                     + ", ".join(x.decode() for x in extra[:8]) if extra else ""))
    check("robots.txt is the one in this repository", robots_same, detail)

    # A directive nobody committed is worth naming even when the byte compare
    # already failed: it is the difference between a formatting drift and the
    # document being closed to the reader it was written for.
    denied = agents_disallowed(live_robots)
    check("no crawler is disallowed at the edge", not denied, ", ".join(denied[:10]))
    check("no content signal restricts the second reader",
          not training_denied(live_robots),
          (re.search(rb"(?im)^Content-Signal:\s*(.+)$", live_robots) or [b"", b""])[1].decode()
          if training_denied(live_robots) else "")

    # ---- every asset the page references resolves ------------------------
    page = body.decode("utf-8", "replace")
    urls = sorted({m if m.startswith("http") else origin + m
                   for m in re.findall(
                       r'(?:https://podmanifesto\.org)?(/(?:assets/[^"\'\s?)]+|favicon\.svg|og\.png)(?:\?v=[0-9a-f]+)?)',
                       page)})
    bad = []
    for u in urls:
        st, payload, _ = fetch(u)
        if st != 200 or not payload:
            bad.append(f"{u} -> {st}")
        elif a.verbose:
            print(f"     200  {len(payload):>7}b  {u}")
    check(f"every referenced asset resolves ({len(urls)} checked)", not bad, "; ".join(bad[:5]))

    # ---- the measurement is actually being taken -------------------------
    # Cloudflare Web Analytics was enabled, its automatic injection on and its
    # ruleset bound to this zone, while the served HTML was byte-identical to the
    # file in git: the beacon never reached a reader and the dashboard said nothing
    # was wrong. Configuration is not measurement. The snippet is in the page now,
    # and this is the check that it stays there.
    n = beacon_count(page)
    check("exactly one analytics beacon reaches the reader", n == 1,
          "none — nothing is being counted" if n == 0 else
          f"{n} — every visit is counted {n} times; the edge injected one on top of the file's")

    foreign = off_origin(page)
    check("the beacon is the only off-origin request",
          foreign == ["static.cloudflareinsights.com"],
          "off-origin: " + (", ".join(foreign) if foreign else "none, so the beacon is missing"))

    # ---- the published companions --------------------------------------
    for path in ("/manifesto.md", "/llms.txt", "/sitemap.xml", "/404.html"):
        st, payload, _ = fetch(origin + path)
        check(f"{path} is served", st == 200 and bool(payload), f"HTTP {st}")

    # ---- a missing address gets this project's 404, not the host's -------
    st, payload, _ = fetch(f"{origin}/a-path-that-does-not-exist-{abs(hash(origin)) % 10**6}")
    is_ours = st == 404 and b"the address does not resolve" in payload
    check("a missing address returns this document's own 404", is_ours,
          f"HTTP {st}, {len(payload)} bytes — the host's default page, not ours")

    # ---- the commit, when the caller knows which one to expect -----------
    if a.expect_commit:
        check("the deploy carries the expected commit", same,
              f"expected {a.expect_commit[:10]}")

    print(f"\n{len(failures)} failure(s) against {origin}")
    for n in notes:
        print(f"  note: {n}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
