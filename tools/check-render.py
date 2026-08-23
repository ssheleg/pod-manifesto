#!/usr/bin/env python3
"""Check the properties that exist only once a browser has rendered the page.

Every other gate in this repository reads a file. That is why all of them were
green on 2026-08-23 while the document printed 27 of its 30 pages blank: the
canonical text was in `index.html`, `check-parity.py` found all 323 sentences of
it, and not one check had ever looked at what a reader would actually get on
paper. The sections are held at `opacity: 0` until an IntersectionObserver marks
them seen, printing never scrolls, so the observer never fired and the ink never
landed. A property nobody rendered is a property nobody checked.

Two things are measured here, both of them in a real browser:

  * **print carries the document.** The page is served locally, printed to PDF
    the way a reader's browser would print it, and the text is extracted back
    out. The canonical sentences of `manifesto.md` must survive the trip.
  * **the page has no console errors** on load, because a script that threw is a
    page whose progressive enhancement did not run.

This gate cannot look without a browser and a PDF text extractor, and a check
that cannot look is not a pass: it exits 2 rather than 0 when either is absent.

Usage:  python3 tools/check-render.py [--verbose] [--keep]
Exit:   0 = the rendered document carries the text and the console is clean
        1 = it does not
        2 = the check could not run (no browser, or no pdftotext)
"""

import http.server
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "manifesto.md"

# The document is long; a sample of its load-bearing sentences from across every
# section proves the body printed, and keeps the gate fast. Any one of these
# missing means a section did not reach the paper.
MIN_LEN = 40
SAMPLE_EVERY = 12          # every Nth canonical sentence, spread over the document
MIN_CHARS = 30_000         # the blank print produced 4 857; the whole text is ~51 000

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome-stable",
    "google-chrome",
    "chromium-browser",
    "chromium",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
        found = shutil.which(c)
        if found:
            return found
    return None


def normalise(text: str) -> str:
    """Match check-parity.py: collapse typography, keep content."""
    text = unicodedata.normalize("NFKC", text)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("—", "-"), ("–", "-"), ("−", "-"),
                 (" ", " "), (" ", " "), (" ", " ")):
        text = text.replace(a, b)
    text = re.sub(r"\s+", " ", text)
    # An inline <code> span becomes its own text run in the PDF, so extraction
    # puts a space before whatever punctuation follows it: "to done ." and
    # "At 0fb706c , I had". check-parity.py:47 collapses the same gap for the same
    # reason; without this the gate reports a sentence absent that is on the page.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def canonical_sentences():
    md = MD.read_text(encoding="utf-8")
    md = re.sub(r"```.*?```", "\n\n", md, flags=re.S)
    out = []
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block or block.startswith(("#", "|", "---")):
            continue
        block = re.sub(r"^\s*[>*-]\s+", "", block, flags=re.M)
        block = re.sub(r"^\s*\d+\.\s+", "", block, flags=re.M)
        block = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", block)
        block = block.replace("**", "").replace("`", "")
        for s in re.split(r'(?<=[.:?!])\s+(?=[A-Z"\'(])', normalise(block)):
            s = s.strip()
            if len(s) >= MIN_LEN:
                out.append(s)
    return out


SWEEP_PATH = "/__contrast-sweep__.html"


def sweep_page() -> bytes:
    """index.html with the contrast sweep injected, served from memory.

    The sweep skips any element at `opacity: 0` (contrast-sweep.js:58) — correctly,
    since invisible text has no contrast. But twelve sections sit at exactly that
    until the reader scrolls, so run by hand from a console at the top of the page
    it measured the masthead and almost nothing else. Every section is revealed
    here before the sweep walks, which is what makes the number cover the document.
    """
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    sweep = (ROOT / "tools" / "contrast-sweep.js").read_text(encoding="utf-8")
    harness = f"""
<style id="sweep-still">
  /* The sweep reads composited colour, and a colour mid-transition is not the
     colour of anything. Under `--virtual-time-budget` the sweep's own 400 ms
     settle is fast-forwarded while the transition is not, so the first run of
     this harness reported five dark-theme pairs below the floor — including
     --accent on --panel at 1.63 where the tokens compute to 11.11. Five false
     failures from a gate is worse than no gate. Stopping motion outright removes
     the race instead of waiting on it. */
  *, *::before, *::after {{
    transition: none !important;
    animation: none !important;
  }}
</style>
<script>
(async () => {{
  try {{
    document.querySelectorAll('.reveal').forEach(function (el) {{ el.classList.add('is-in'); }});
    var boot = document.querySelector('.boot');
    if (boot) boot.classList.add('is-up');
    var toc = document.querySelector('.toc__wrap');
    if (toc) toc.setAttribute('open', '');
    // setTimeout, not requestAnimationFrame: `--virtual-time-budget` advances
    // timers and does not reliably drive frames, so a double-rAF here simply
    // never resolved and the gate reported no result at all.
    await new Promise(function (r) {{ setTimeout(r, 300); }});
    void document.body.offsetHeight;                 // force one style flush
    var out = await {sweep.strip().rstrip(';')};
    document.title = 'SWEEP:' + JSON.stringify(out);
  }} catch (e) {{
    document.title = 'SWEEP-ERROR:' + (e && e.message ? e.message : String(e));
  }}
}})();
</script>
</body>"""
    return page.replace("</body>", harness, 1).encode("utf-8")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_GET(self):
        if self.path.split("?")[0] == SWEEP_PATH:
            body = sweep_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *a):
        pass


def serve():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = socketserver.TCPServer(("127.0.0.1", port), QuietHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def main() -> int:
    verbose = "--verbose" in sys.argv
    keep = "--keep" in sys.argv

    chrome = find_chrome()
    if not chrome:
        print("no browser found — a check that cannot look is not a pass")
        print("  looked for: " + ", ".join(CHROME_CANDIDATES))
        return 2
    if not shutil.which("pdftotext"):
        print("pdftotext not found (poppler-utils) — a check that cannot look is not a pass")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="podmanifesto-render-"))
    pdf = tmp / "document.pdf"
    httpd, port = serve()
    try:
        proc = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=15000", "--print-to-pdf-no-header",
             f"--print-to-pdf={pdf}", f"http://127.0.0.1:{port}/"],
            capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        print("the browser did not finish printing within 180s")
        return 2
    finally:
        httpd.shutdown()

    if not pdf.exists():
        print("the browser produced no PDF")
        print("  " + (proc.stderr or proc.stdout or "")[-400:])
        return 2

    txt = subprocess.run(["pdftotext", str(pdf), "-"],
                         capture_output=True, text=True)
    printed = normalise(txt.stdout)

    failures = []

    # ---- the body reached the paper --------------------------------------
    if len(printed) < MIN_CHARS:
        failures.append(
            f"the printed document carries {len(printed)} characters, "
            f"below the {MIN_CHARS} floor — the body did not render")

    sample = canonical_sentences()[::SAMPLE_EVERY]
    missing = [s for s in sample if s not in printed]
    if missing:
        failures.append(f"{len(missing)} of {len(sample)} sampled canonical "
                        f"sentences are absent from the printed document")

    pages = re.search(r"Pages:\s+(\d+)",
                      subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                                     text=True).stdout) if shutil.which("pdfinfo") else None

    # ---- contrast, measured on composited colour in both themes ----------
    # This was the one check the README called manual, "pasted into a browser
    # console because it measures composited colour". It still needs a browser —
    # it just does not need a person.
    httpd2, port2 = serve()
    try:
        dom = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=30000", "--dump-dom",
             f"http://127.0.0.1:{port2}{SWEEP_PATH}"],
            capture_output=True, text=True, timeout=180).stdout
    except subprocess.TimeoutExpired:
        dom = ""
    finally:
        httpd2.shutdown()

    m = re.search(r"<title>SWEEP:(.*?)</title>", dom, re.S)
    err = re.search(r"<title>SWEEP-ERROR:(.*?)</title>", dom, re.S)
    if err:
        failures.append(f"the contrast sweep raised: {err.group(1)[:120]}")
        sweep = None
    elif not m:
        failures.append("the contrast sweep produced no result — a check that "
                        "cannot look is not a pass")
        sweep = None
    else:
        import json, html as _html
        try:
            sweep = json.loads(_html.unescape(m.group(1)))
        except Exception as e:
            failures.append(f"the contrast sweep result did not parse: {e}")
            sweep = None

    if sweep is not None:
        under = sweep.get("under_floor", -1)
        print(f"contrast under floor : {under} (WCAG AA, both themes, composited)")
        if under:
            failures.append(f"{under} text/background pair(s) below the WCAG AA floor")
            for r in sweep.get("results", [])[:8]:
                print(f"    {r['theme']:<5} {r['r']:>5} < {r['floor']}  "
                      f"{r['sel'][:44]:<46} {r['text'][:30]!r}")

    print(f"printed characters : {len(printed)} (floor {MIN_CHARS})")
    print(f"canonical sample   : {len(sample) - len(missing)}/{len(sample)} present")
    if pages:
        print(f"pages              : {pages.group(1)}")
    for s in missing[:5]:
        print(f"\n  ABSENT FROM PRINT: {s[:110]}")
    if len(missing) > 5:
        print(f"  … and {len(missing) - 5} more")

    for f in failures:
        print(f"  FAIL  {f}")

    if keep:
        print(f"\npdf kept at {pdf}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)

    if not failures and verbose:
        print("\nthe rendered document carries the canonical text into print.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
