#!/usr/bin/env python3
"""Resolve every external reference this repository publishes.

The manifesto's rule: a reference that does not resolve is a claim with its
receipt removed. This applies the rule to the document itself.

WHY THIS DOES NOT JUST FETCH THE PAGE. It used to, and it was a check that did
not observe its subject. github.com answers anonymous HTML requests for a blob
with a **404 and a full page body** once it decides to throttle you — so the
checker went red on eleven references that were, and are, public and present.
The same URLs resolve through the API every time. A check whose green depends on
whether GitHub felt like serving HTML that minute measures the weather, not the
claim, which is the failure this document is about.

So a github.com reference is verified through the API instead, and verified
harder than before: for `blob/<ref>/<path>#L10-L20` this fetches the file at that
exact ref and asserts the file has those lines. A line range the file cannot
contain is a broken citation even when the URL loads.

Usage:  python3 tools/check-links.py
Exit:   0 = every reference resolved
        1 = at least one did not
"""

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["index.html", "manifesto.md", "llms.txt", "README.md", "sitemap.xml"]
SELF = "https://podmanifesto.org"

UA = {"User-Agent": "pod-manifesto-link-check/2.0 (+https://podmanifesto.org)"}
API = "https://api.github.com"
TIMEOUT = 25

BLOB = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+?)(?:#L(\d+)(?:-L(\d+))?)?$")
COMMIT = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/commit/([0-9a-f]{7,40})$")
REPO = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)/?$")
USER = re.compile(r"^https://github\.com/([^/]+)/?$")


def gh(path):
    """One API call, with the runner's token when there is one, and a retry."""
    req = urllib.request.Request(API + path, headers=dict(UA, Accept="application/vnd.github+json"))
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if (e.code in (403, 429) or e.code >= 500) and attempt < 2:   # throttled or a gateway blip
                time.sleep(5 * (attempt + 1))
                continue
            return e.code, None
        except Exception:                                  # noqa: BLE001
            if attempt < 2:
                time.sleep(2)
                continue
            return 0, None
    return 0, None


def check_github(url):
    m = BLOB.match(url)
    if m:
        owner, repo, ref, path, l1, l2 = m.groups()
        status, body = gh(f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")
        if status != 200 or not body:
            return False, f"HTTP {status} from the API"
        if l1:
            try:
                text = base64.b64decode(body.get("content", "")).decode("utf-8", "replace")
            except Exception:                              # noqa: BLE001
                return True, "ok (binary; line range unverified)"
            lines = text.count("\n") + 1
            want = int(l2 or l1)
            if want > lines:
                return False, f"cites L{want} but the file has {lines} lines"
            return True, f"ok (L{l1}-{l2 or l1} within {lines})"
        return True, "ok"

    m = COMMIT.match(url)
    if m:
        owner, repo, sha = m.groups()
        status, _ = gh(f"/repos/{owner}/{repo}/commits/{sha}")
        return status == 200, f"HTTP {status}" if status != 200 else "ok"

    m = REPO.match(url)
    if m:
        owner, repo = m.groups()
        status, _ = gh(f"/repos/{owner}/{repo}")
        return status == 200, f"HTTP {status}" if status != 200 else "ok"

    m = USER.match(url)
    if m:
        status, _ = gh(f"/users/{m.group(1)}")
        return status == 200, f"HTTP {status}" if status != 200 else "ok"

    return None, ""      # some other github.com URL — fall through to plain HTTP


def check_npm(url):
    """Resolve an npm package page through the registry, not the website.

    The same shape as the github.com problem this file already solves one function
    up: `npmjs.com/package/<name>` answers a scripted GET with 403 whether or not
    the package exists, so a plain fetch measures the bot filter rather than the
    reference. `registry.npmjs.org/<name>` is the address the package actually
    lives at — it is what `npx` resolves against — and it answers 404 for a name
    that is not published.
    """
    m = re.match(r"https://www\.npmjs\.com/package/([^/?#]+)", url)
    if not m:
        return None, ""
    name = m.group(1)
    req = urllib.request.Request(f"https://registry.npmjs.org/{name}",
                                 headers=UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} from the registry"
    except Exception as e:                                 # noqa: BLE001
        return False, type(e).__name__
    if data.get("name") != name:
        return False, f"the registry serves {data.get('name')!r} at that name"
    return True, f"ok ({len(data.get('versions', {}))} versions published)"


def check_plain(url):
    req = urllib.request.Request(url, headers=UA, method="GET")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return 200 <= r.status < 300, str(r.status)
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            return False, f"HTTP {e.code}"
        except Exception as e:                             # noqa: BLE001
            if attempt < 2:
                time.sleep(2)
                continue
            return False, type(e).__name__
    return False, "unreachable"


def check(url):
    if url.startswith(SELF):
        # `?v=<hash>` is a cache fingerprint, not part of the path — stamp-assets
        # puts one on every same-origin asset, including the absolute og:image url,
        # and resolving the query as a filename reported a shipped file missing.
        path = url[len(SELF):].split("#")[0].split("?")[0].lstrip("/") or "index.html"
        here = (ROOT / path).exists()
        return here, "local file" if here else "MISSING FILE"
    if url.startswith("https://github.com/"):
        ok, note = check_github(url)
        if ok is not None:
            return ok, note
    if url.startswith("https://www.npmjs.com/package/"):
        ok, note = check_npm(url)
        if ok is not None:
            return ok, note
    return check_plain(url)


def collect():
    found = {}
    for name in SOURCES:
        text = (ROOT / name).read_text(encoding="utf-8")
        for url in re.findall(r'https?://[^\s"\'<>)\]]+', text):
            found.setdefault(url.rstrip(".,;"), set()).add(name)
    return found


def main() -> int:
    links = collect()
    bad = []
    for url in sorted(links):
        ok, note = check(url)
        print(f"{'ok  ' if ok else 'FAIL'} {note:<34} {url}")
        if not ok:
            bad.append((url, note, sorted(links[url])))
    print(f"\n{len(links)} references checked, {len(bad)} unresolved")
    for url, note, where in bad:
        print(f"  {note}: {url}  (in {', '.join(where)})")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
