#!/usr/bin/env python3
"""Draw the manifesto's five figures as printed plates, in the `field-notes` register.

The rule this file exists to keep: in this pack **mono is annotation, not data**.
A diagram whose every word is monospaced reads as ASCII art with rounded corners.
So a node here is a name set in the text face sitting on a hairline, and the mono
is kept for what a plate uses it for — lane labels, indices, relation names and
state tags.

Geometry is generated rather than hand-drawn so it can be asserted: nothing leaves
the canvas and nothing on a row overlaps. Colour comes from the pack's tokens
through CSS classes; no literal is written here, so one drawing serves both themes.

Usage:  python3 tools/build-figures.py          # writes assets/figures/*.svg
        python3 tools/build-figures.py --check  # geometry only, writes nothing
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "figures"

FS_NAME = 14        # node names — the text face
FS_NOTE = 10.5      # relation names and questions — mono
FS_LANE = 10        # lane labels, indices and tags — mono
DOT = 3.4
NOTE_GAP = 30       # a note above a station clears the name's ascender


# ── measurement ──────────────────────────────────────────────────────────────
# Geist is proportional, so widths are estimated per character class here and
# then verified in the browser, where the real metrics live.

_NARROW = set("iltfjIr.,;:'!|()[]{}-/ ")
_WIDE = set("mwMW@")


def sans_w(s, size=FS_NAME):
    u = 0.0
    for ch in s:
        if ch in _NARROW:
            u += 0.30
        elif ch in _WIDE:
            u += 0.88
        elif ch.isupper() or ch.isdigit():
            u += 0.62
        else:
            u += 0.535
    return u * size


def mono_w(s, size=FS_NOTE, track=0.06):
    return len(s) * (size * 0.6 + size * track)


# ── the plate ────────────────────────────────────────────────────────────────

class Plate:
    def __init__(self, width, height, title):
        self.w, self.h, self.title = width, height, title
        self.p = []
        self.spans = []       # (x0, x1, row) — for the overlap assertion

    # -- marks -------------------------------------------------------------
    def rule(self, x1, x2, y, cls="rule"):
        self.p.append(f'<path class="{cls}" d="M{x1:.1f} {y:.1f} H{x2:.1f}"/>')

    def vrule(self, x, y1, y2, cls="rule"):
        self.p.append(f'<path class="{cls}" d="M{x:.1f} {y1:.1f} V{y2:.1f}"/>')

    def dot(self, x, y, cls="dot", r=DOT):
        self.p.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')

    def wash(self, x, y, w, h):
        self.p.append(f'<rect class="wash" x="{x:.1f}" y="{y:.1f}" '
                      f'width="{w:.1f}" height="{h:.1f}" rx="10"/>')

    def flow(self, d, cls="flow", head=True):
        m = ' marker-end="url(#h)"' if head else ""
        self.p.append(f'<path class="{cls}" d="{d}"{m}/>')

    # -- type --------------------------------------------------------------
    def _span(self, x, w, anchor, row):
        x0 = x if anchor == "start" else (x - w / 2 if anchor == "middle" else x - w)
        if row is not None:
            self.spans.append((x0, x0 + w, row))
        return x0, x0 + w

    def name(self, x, y, s, cls="name", anchor="start", row=None):
        self.p.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" '
                      f'text-anchor="{anchor}">{escape(s)}</text>')
        return self._span(x, sans_w(s), anchor, row)

    def note(self, x, y, s, cls="note", anchor="start", row=None):
        self.p.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" '
                      f'text-anchor="{anchor}">{escape(s)}</text>')
        return self._span(x, mono_w(s), anchor, row)

    def lane(self, x, y, s, anchor="start"):
        self.p.append(f'<text class="lane" x="{x:.1f}" y="{y:.1f}" '
                      f'text-anchor="{anchor}">{escape(s)}</text>')

    def idx(self, x, y, s):
        self.p.append(f'<text class="idx" x="{x:.1f}" y="{y:.1f}">{escape(s)}</text>')

    def tag(self, x, y, s, state, row=None):
        """A provenance tag — the pack's signature label, reused as a state mark."""
        self.p.append(f'<text class="tag tag--{state}" x="{x:.1f}" y="{y:.1f}">'
                      f'[{escape(s)}]</text>')
        return self._span(x, mono_w(f"[{s}]", FS_LANE, 0.08), "start", row)

    # -- composition -------------------------------------------------------
    def station(self, x, y, label, key=False, row=0, dotcls=None):
        """A name set above a hairline with its dot on the line. The plate's atom."""
        span = self.name(x, y - 11, label, "name name--key" if key else "name", row=row)
        self.dot(x + 1.6, y, dotcls or ("dot--key" if key else "dot"))
        return span

    def stop(self, spine_x, y, label, key=False, row=0, dotcls=None, gap=18):
        """A dot on a vertical spine with its name beside it, on the same baseline."""
        self.dot(spine_x, y, dotcls or ("dot--key" if key else "dot"))
        return self.name(spine_x + gap, y + 5, label,
                         "name name--key" if key else "name", row=row)

    def render(self):
        return (
            f'<svg class="figsvg" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-label="{escape(self.title)}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<defs><marker id="h" markerWidth="6" markerHeight="6" refX="5.2" refY="3" '
            f'orient="auto"><path class="head" d="M0 0 L6 3 L0 6 z"/></marker></defs>'
            + "".join(self.p) + "</svg>\n"
        )

    def verify(self):
        rows = {}
        for x0, x1, row in self.spans:
            assert -1 <= x0 and x1 <= self.w + 1, \
                f"{self.title}: text leaves the canvas ({x0:.0f}..{x1:.0f} of {self.w})"
            rows.setdefault(row, []).append((x0, x1))
        for row, spans in rows.items():
            spans.sort()
            for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
                assert a1 <= b0 + 0.5, \
                    f"{self.title}: row {row} overlaps ({a1:.0f} > {b0:.0f})"
        return len(self.spans)


# ── FIG 1 — three lanes, and the relations that cross them ───────────────────

def fig1():
    """Three strata. A band groups a graph, a rule carries its sequence, and a
    station is a name on that rule — the relations between graphs cross the
    channels between bands."""
    W = 960
    B1, B2, B3 = 52, 182, 312          # band tops
    BH, BH3 = 76, 124                  # band heights
    c = Plate(W, 512, "Three graphs, and the relations that cross between them")

    def band(y, h, label):
        c.wash(0, y, W, h)
        c.lane(16, y + 21, label)

    def lane_rule(x0, stations, y):
        """One rule from the first station to just past the last, ending in an arrow."""
        last = stations[-1]
        end = last[1] + sans_w(last[0]) + 26
        c.rule(x0, end - 8, y)
        c.flow(f"M{end - 20:.1f} {y:.1f} H{end:.1f}")

    band(B1, BH, "INTENT")
    intent = [("Problem", 16), ("Hypothesis", 144), ("Requirement", 302),
              ("Decision", 478), ("Contract and failure behaviour", 610)]
    y1 = B1 + 56
    lane_rule(16, intent, y1)
    for label, x in intent:
        c.station(x, y1, label, row=1)

    band(B2, BH, "EXECUTION")
    ex = [("Task", 302), ("Change", 436), ("Integrated result", 582),
          ("Reachable surface", 776)]
    y2 = B2 + 56
    lane_rule(302, ex, y2)
    for label, x in ex:
        c.station(x, y2, label, row=2)

    band(B3, BH3, "EVIDENCE")
    ev = [("Implementation check", 436), ("Observed result", 636),
          ("Delivery acceptance", 792)]
    y3 = B3 + 52
    lane_rule(436, ev, y3)
    for label, x in ev:
        c.station(x, y3, label, row=3)
    ev2 = [("Outcome observation", 596), ("Product learning", 812)]
    y3b = B3 + 100
    lane_rule(596, ev2, y3b)
    for label, x in ev2:
        c.station(x, y3b, label, row=4)

    # ── the relations that cross a channel ────────────────────────────────
    ch1, ch2 = B1 + BH, B2 + BH        # channel tops

    # two of them align, so they drop straight
    c.flow(f"M303.6 {ch1:.1f} V{B2 + 30:.1f}")
    c.note(311, ch1 + 26, "assigned to")
    c.flow(f"M437.6 {B3 - 6:.1f} V{ch2 + 8:.1f}")
    c.note(445, ch2 + 30, "observes")

    # two cannot; each is one elbow routed along its channel
    c.flow(f"M611.6 {ch1:.1f} V{ch1 + 34:.1f} H311 V{B2 + 30:.1f}", cls="flow flow--dash")
    c.note(620, ch1 + 30, "constrains", cls="note")
    c.flow(f"M597.6 {B3 + 70:.1f} V{ch2 + 22:.1f} H777.6 V{y2 + 8:.1f}",
           cls="flow flow--dash")
    c.note(786, ch2 + 18, "observes", cls="note")

    y = 492
    c.rule(0, W, y - 28, "rule rule--faint")
    c.note(0, y, "Delivery acceptance closes a requirement", cls="note note--foot", row=9)
    c.note(430, y, "Product learning updates a hypothesis", cls="note note--foot", row=9)
    c.note(W, y, "both return into INTENT", cls="note note--foot", anchor="end", row=9)
    return c


# ── FIG 2 — the checker between fan-out and convergence ──────────────────────

def fig2():
    W, H = 880, 330
    c = Plate(W, H, "A checker stands between fan-out and convergence")
    lanes = [86, 158, 230]
    mid = lanes[1]

    c.lane(0, 34, "FAN-OUT")
    c.station(0, mid, "Locked input", row=1)

    split = 132
    c.flow(f"M{sans_w('Locked input') + 10:.1f} {mid:.1f} H{split - 4:.1f}", head=False)
    c.vrule(split, lanes[0], lanes[2])
    for i, y in enumerate(lanes):
        c.flow(f"M{split:.1f} {y:.1f} H{split + 22:.1f}")
        c.station(split + 30, y, f"Independent branch {'ABC'[i]}", row=10 + i)

    join = 372
    for y in lanes:
        c.flow(f"M{split + 30 + sans_w('Independent branch A') + 10:.1f} {y:.1f} "
               f"H{join:.1f}", head=False)
    c.vrule(join, lanes[0], lanes[2])

    gate = 446
    c.flow(f"M{join:.1f} {mid:.1f} H{gate - 7:.1f}")
    c.p.append(f'<path class="gate" d="M{gate} {lanes[0] - 16} V{lanes[2] + 16}"/>')
    c.lane(gate, lanes[0] - 26, "CHECKER", anchor="middle")

    out = gate + 62
    c.flow(f"M{gate:.1f} {mid:.1f} H{out - 30:.1f}", head=False)
    c.vrule(out - 30, 108, 208)
    c.flow(f"M{out - 30:.1f} 108 H{out - 6:.1f}")
    c.flow(f"M{out - 30:.1f} 208 H{out - 6:.1f}")

    c.station(out, 108, "Convergence", row=20, dotcls="dot--ok")
    c.note(out, 108 - NOTE_GAP, "validated outputs", row=21)
    c.tag(out + sans_w("Convergence") + 14, 101, "ACCEPTED", "ok", row=20)

    c.station(out, 208, "Stop, route the finding", row=30, dotcls="dot--bad")
    c.note(out, 208 - NOTE_GAP, "missing or contradictory", row=31)
    c.tag(out + sans_w("Stop, route the finding") + 14, 201, "HELD", "bad", row=30)

    c.rule(0, W, 278, "rule rule--faint")
    c.note(0, 302, "convergence consumes validated results or stops; it never repairs them",
           cls="note note--foot", row=40)
    return c


# ── FIG 3 — invalidation is a routing decision ───────────────────────────────

def fig3():
    """A spine, one fork, then a second: the plate reads top-down like a routing slip."""
    W, H = 880, 400
    c = Plate(W, H, "Invalidation is a routing decision, not a deletion")
    spine = 8
    c.lane(0, 32, "THE SPINE")
    c.vrule(spine, 56, 320)

    for y, label in [(70, "Accepted proof"),
                     (142, "Code, dependency, environment, or policy change"),
                     (214, "Map the change to covered claims")]:
        c.stop(spine, y, label, row=int(y))

    col_b, col_c = 392, 636

    # first fork: does the change touch the claim?
    for y, label, tail in [(262, "claim unaffected", "Proof remains valid"),
                           (320, "claim affected", "Check owed")]:
        c.flow(f"M{spine:.1f} {y:.1f} H{col_b - 14:.1f}")
        c.note(spine + 18, y - 10, label)

    c.stop(col_b, 262, "Proof remains valid", row=262, dotcls="dot--ok")
    c.tag(col_b + 18 + sans_w("Proof remains valid") + 14, 267, "STILL COVERED", "ok", row=262)
    c.stop(col_b, 320, "Check owed", key=True, row=320)

    # second fork: did the owed check run, and pass?
    stem = col_c - 26
    c.flow(f"M{col_b + 18 + sans_w('Check owed') + 12:.1f} 320 H{stem:.1f}", head=False)
    c.vrule(stem, 292, 356)
    c.flow(f"M{stem:.1f} 292 H{col_c - 8:.1f}")
    c.flow(f"M{stem:.1f} 356 H{col_c - 8:.1f}")

    c.stop(col_c, 292, "New proof version", row=292, dotcls="dot--ok")
    c.note(col_c + 18, 276, "passes", row=290)
    c.stop(col_c, 356, "Unproven state", row=356, dotcls="dot--bad")
    c.note(col_c + 18, 340, "fails or cannot run", row=354)

    c.rule(0, W, 374, "rule rule--faint")
    c.note(0, 396, "the old proof stays in the record; the change returns to the earliest "
                   "uncovered node", cls="note note--foot", row=50)
    return c


# ── FIG 4 — the seam walk, as a numbered plate ───────────────────────────────

RUNGS = [
    ("Requirement with an observable", "did it rest on a decision somebody actually made?"),
    ("Recorded decision", "did the decision reach the specification?"),
    ("Design or specification", "did it define a contract and its failure behaviour?"),
    ("Contract and failure behaviour", "did a task build that contract?"),
    ("Task with a satisfiable definition of done", "did the change satisfy the task as written?"),
    ("Change in the tree", "did an executed check observe the changed behaviour?"),
    ("Executed check", "can you or a downstream system reach it?"),
    ("Reachable user or system surface", "does it satisfy the ORIGINAL requirement?"),
    ("Acceptance", None),
]


def fig4():
    W, step, top = 880, 52, 58
    c = Plate(W, top + step * (len(RUNGS) - 1) + 44, "The seam walk, from requirement to acceptance")

    c.lane(0, 30, "THE WALK")
    c.lane(W, 30, "EACH RUNG NAMES WHAT SHOULD EXIST NEXT", anchor="end")
    spine = 58
    c.vrule(spine, top - 14, top + step * (len(RUNGS) - 1))

    for i, (label, question) in enumerate(RUNGS):
        y = top + i * step
        last = question is None
        c.rule(0, W, y - 24, "rule rule--faint")
        c.idx(0, y + 4, f"{i + 1:02d}")
        c.dot(spine, y, "dot--ok" if last else "dot")
        c.name(spine + 18, y + 5, label, "name name--key" if last else "name", row=i)
        if question:
            c.note(W, y + 4, question, anchor="end", row=1000 + i)
        else:
            c.tag(W - mono_w("[ACCEPTED]", FS_LANE, 0.08), y + 4, "ACCEPTED", "ok", row=1000 + i)
    return c


# ── FIG 5 — the learning loop, as a serpentine ───────────────────────────────

def fig5():
    """A ledger of the run, its two answers, and the return that closes the loop."""
    W = 880
    step, top = 48, 76
    spine, spine2 = 44, 104
    stages = [
        ("Run", None),
        ("Observed divergence", "what diverged from the operating contract"),
        ("Owning layer and root cause", "which earlier layer let it through"),
        ("Mechanical check, bounded rule, or expiring note", "the three grades of learning"),
        ("Next run", "the lesson is now in the system, not in a memory"),
        ("Did the mechanism fire?", None),
    ]
    answers = [
        ("Keep and measure", "the mechanism fired", "KEPT", "ok"),
        ("Retire, preserve history", "surface gone or rule cold", "RETIRED", "bad"),
    ]
    last_stage_y = top + step * (len(stages) - 1)
    a1 = last_stage_y + step
    a2 = a1 + step
    H = a2 + 104
    c = Plate(W, H, "The learning loop: a lesson becomes a mechanism, then retires")

    c.lane(0, 32, "THE LOOP")
    c.lane(W, 32, "AND THE RETURN THAT CLOSES IT", anchor="end")
    c.vrule(spine, top - 16, last_stage_y)

    for i, (label, note) in enumerate(stages):
        y = top + i * step
        key = label.startswith("Mechanical") or label.startswith("Did the")
        c.rule(0, W, y - 22, "rule rule--faint")
        c.idx(0, y + 4, f"{i + 1:02d}")
        c.stop(spine, y, label, key=key, row=i)
        if note:
            c.note(W, y + 4, note, anchor="end", row=1000 + i)

    # the fork: two answers, indented under the question
    c.vrule(spine2, last_stage_y + 8, a2)
    c.flow(f"M{spine:.1f} {last_stage_y + 8:.1f} V{last_stage_y + 24:.1f} "
           f"H{spine2:.1f}", head=False)
    for (label, reason, tag, state), y in zip(answers, (a1, a2)):
        c.rule(0, W, y - 22, "rule rule--faint")
        c.flow(f"M{spine2:.1f} {y:.1f} H{spine2 + 14:.1f}")
        c.stop(spine2 + 22, y, label, row=10 + y, dotcls=f"dot--{state}", gap=16)
        tag_x = W - mono_w(f"[{tag}]", FS_LANE, 0.08)
        c.tag(tag_x, y + 4, tag, state, row=1010 + y)
        c.note(tag_x - 16, y + 4, reason, anchor="end", row=1010 + y)

    # the return: down past the answers, up the margin, and back into stage 01
    c.flow(f"M{spine2:.1f} {a2 + 8:.1f} V{a2 + 36:.1f} H22 V{top - 36:.1f} "
           f"H{spine:.1f} V{top - 18:.1f}", cls="flow flow--dash")
    c.note(spine2 + 22, a2 + 62, "every run re-enters with whatever the last one "
                                 "made mechanical", cls="note note--foot", row=99)
    return c


FIGURES = {"fig-1": fig1, "fig-2": fig2, "fig-3": fig3, "fig-4": fig4, "fig-5": fig5}


def main():
    check_only = "--check" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, build in FIGURES.items():
        plate = build()
        n = plate.verify()
        total += n
        if not check_only:
            (OUT / f"{name}.svg").write_text(plate.render(), encoding="utf-8")
        print(f"{name}: {n} labels, {plate.w}x{plate.h}, geometry asserted")
    print(f"\n{len(FIGURES)} plates, {total} labels, every assertion held"
          + ("" if check_only else f" — written to {OUT.relative_to(ROOT)}/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
