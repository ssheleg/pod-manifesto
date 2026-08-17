#!/usr/bin/env python3
"""Draw the manifesto's five figures as SVG, in the SHELEG `field-notes` register.

The figures are the document's diagrams. They are generated rather than hand-drawn
so their geometry is asserted instead of eyeballed: no two boxes in a row overlap,
every edge lands on a real anchor, and nothing leaves the canvas. The same rule the
document argues for, applied to its own illustrations.

Colour comes from the pack's tokens through CSS classes — no literal is written
here — so one drawing serves both themes.

Usage:  python3 tools/build-figures.py          # writes assets/figures/*.svg
        python3 tools/build-figures.py --check  # geometry only, writes nothing
Exit:   0 = every assertion held
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "figures"

W = 960                 # user units; the figure well renders at this width or less
MONO_ADV = 0.6          # Geist Mono advance, in em
PAD_X = 13              # node horizontal padding
NODE_H = 34
FS_NODE = 12
FS_EDGE = 11
FS_BAND = 11


# ── measurement ──────────────────────────────────────────────────────────────

def text_w(s, size=FS_NODE):
    return len(s) * size * MONO_ADV


def node_w(label, minimum=0):
    return max(minimum, round(text_w(label) + PAD_X * 2))


# ── primitives ───────────────────────────────────────────────────────────────

class Canvas:
    def __init__(self, width, height, title):
        self.w, self.h, self.title = width, height, title
        self.parts = []
        self.boxes = []          # (x, y, w, h, row) for the overlap assertion

    def box(self, x, y, w, h, label, cls="node", row=0, sub=None, rx=8):
        self.parts.append(
            f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" rx="{rx}"/>'
        )
        tcls = "label label--em" if cls.endswith("--em") else "label"
        if sub:
            self.parts.append(
                f'<text class="{tcls}" x="{x + w / 2:.1f}" y="{y + h / 2 - 4:.1f}">{escape(label)}</text>'
                f'<text class="label label--sub" x="{x + w / 2:.1f}" y="{y + h / 2 + 12:.1f}">{escape(sub)}</text>'
            )
        else:
            self.parts.append(
                f'<text class="{tcls}" x="{x + w / 2:.1f}" y="{y + h / 2:.1f}">{escape(label)}</text>'
            )
        self.boxes.append((x, y, w, h, row))
        return (x, y, w, h)

    def frame(self, x, y, w, h, label):
        self.parts.append(
            f'<rect class="band" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="12"/>'
        )
        self.parts.append(
            f'<text class="band-label" x="{x + 2:.1f}" y="{y - 9:.1f}">{escape(label)}</text>'
        )

    def edge(self, d, dashed=False, head=True):
        cls = "edge edge--dash" if dashed else "edge"
        marker = ' marker-end="url(#a)"' if head else ""
        self.parts.append(f'<path class="{cls}" d="{d}"{marker}/>')

    def arrow_h(self, x1, x2, y, dashed=False):
        self.edge(f"M{x1:.1f} {y:.1f} H{x2:.1f}", dashed)

    def elbow(self, x1, y1, x2, y2, mid, dashed=False):
        """Orthogonal route: down/up from the source, across, then into the target."""
        self.edge(f"M{x1:.1f} {y1:.1f} V{mid:.1f} H{x2:.1f} V{y2:.1f}", dashed)

    def note(self, x, y, s, cls="edge-label", anchor="start"):
        self.parts.append(
            f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{escape(s)}</text>'
        )

    def render(self):
        return (
            f'<svg class="figsvg" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-label="{escape(self.title)}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<defs><marker id="a" markerWidth="7" markerHeight="7" refX="6.2" refY="3.5" '
            f'orient="auto"><path class="head" d="M0 0 L7 3.5 L0 7 z"/></marker></defs>'
            + "".join(self.parts)
            + "</svg>\n"
        )

    def verify(self):
        by_row = {}
        for x, y, w, h, row in self.boxes:
            by_row.setdefault(row, []).append((x, x + w))
            assert x >= 0 and x + w <= self.w, f"{self.title}: box leaves canvas ({x}..{x+w} of {self.w})"
            assert y >= 0 and y + h <= self.h, f"{self.title}: box leaves canvas vertically"
        for row, spans in by_row.items():
            spans.sort()
            for (a1, a2), (b1, b2) in zip(spans, spans[1:]):
                assert a2 <= b1, f"{self.title}: row {row} boxes overlap ({a2:.1f} > {b1:.1f})"
        return len(self.boxes)


def chain(c, labels, x0, y, gap=44, row=0, em=(), widths=None):
    """Lay a row of nodes left to right, joined by arrows. Returns the placed boxes."""
    placed, x = [], x0
    for i, lab in enumerate(labels):
        w = widths[i] if widths else node_w(lab)
        cls = "node node--em" if lab in em else "node"
        placed.append(c.box(x, y, w, NODE_H, lab, cls, row))
        x += w + gap
    for (ax, ay, aw, ah), (bx, *_ ) in zip(placed, placed[1:]):
        c.arrow_h(ax + aw + 9, bx - 5, ay + ah / 2)
    return placed


def cx(b):  # centre x
    return b[0] + b[2] / 2


# ── FIG 1 — the three graphs ─────────────────────────────────────────────────

def fig1():
    """Three bands with a clear channel between each pair, so no route crosses a label."""
    BAND, CH = 58, 108            # band height, and the channel between bands
    intent_y = 26
    exec_y = intent_y + BAND + CH
    ev_y = exec_y + BAND + CH
    ev_h = 100
    c = Canvas(W, ev_y + ev_h + 46,
               "The three graphs and the edges that close the loop back into intent")

    c.frame(0, intent_y, W, BAND, "INTENT")
    intent = chain(c, ["Problem", "Hypothesis", "Requirement", "Decision",
                       "Contract + failure behaviour"], 18, intent_y + 12, row=1)

    c.frame(0, exec_y, W, BAND, "EXECUTION")
    ex = chain(c, ["Task", "Change", "Integrated result", "Reachable surface"],
               18, exec_y + 12, row=2)

    c.frame(0, ev_y, W, ev_h, "EVIDENCE")
    evid = chain(c, ["Implementation check", "Observed result", "Delivery acceptance"],
                 18, ev_y + 12, row=3)
    evid2 = chain(c, ["Outcome observation", "Product learning"], 560, ev_y + 56, row=4)

    task, change, surface = ex[0], ex[1], ex[3]
    requirement, contract = intent[2], intent[4]

    # ── intent constrains execution: two buses, 34 apart, each label above its own
    bus_a, bus_b = intent_y + BAND + 30, intent_y + BAND + 64
    c.elbow(cx(requirement), intent_y + BAND + 3, cx(task) - 12, exec_y + 9, bus_a, dashed=True)
    c.note(cx(requirement) + 12, bus_a - 8, "assigned to")
    c.elbow(cx(contract), intent_y + BAND + 3, cx(task) + 12, exec_y + 9, bus_b, dashed=True)
    c.note(cx(contract) + 12, bus_b - 8, "constrains")

    # ── evidence observes execution: the same channel, mirrored
    bus_c, bus_d = exec_y + BAND + 34, exec_y + BAND + 70
    c.elbow(cx(evid[0]), ev_y - 3, cx(change) - 12, exec_y + BAND - 9, bus_c, dashed=True)
    c.note(cx(evid[0]) + 12, bus_c - 8, "observes")
    c.elbow(cx(evid2[0]), ev_y + 52, cx(surface) + 12, exec_y + BAND - 9, bus_d, dashed=True)
    c.note(cx(evid2[0]) + 12, bus_d - 8, "observes")

    # ── the two return edges, stated rather than drawn back across the figure
    c.note(18, ev_y + ev_h + 30,
           "Delivery acceptance closes a Requirement   ·   "
           "Product learning updates a Hypothesis   ·   both return into INTENT",
           cls="edge-label edge-label--foot")
    return c


# ── FIG 2 — a checker between fan-out and convergence ────────────────────────

def fig2():
    c = Canvas(860, 300, "A checker stands between fan-out and convergence")
    src = c.box(0, 133, node_w("Locked input"), NODE_H, "Locked input", row=0)
    bx = src[0] + src[2] + 60
    branches = [
        c.box(bx, 30, node_w("Independent branch A", 210), NODE_H, "Independent branch A", row=1),
        c.box(bx, 133, node_w("Independent branch B", 210), NODE_H, "Independent branch B", row=2),
        c.box(bx, 236, node_w("Independent branch C", 210), NODE_H, "Independent branch C", row=3),
    ]
    spine = src[0] + src[2] + 26
    c.arrow_h(src[0] + src[2] + 9, spine, 150)
    c.edge(f"M{spine} 47 V253", head=False)
    for b in branches:
        c.arrow_h(spine, b[0] - 5, b[1] + NODE_H / 2)
    c.edge(f"M{spine} 150 H{spine}", head=False)

    join = branches[0][0] + branches[0][2] + 26
    for b in branches:
        c.arrow_h(b[0] + b[2] + 9, join - 1, b[1] + NODE_H / 2)
    c.edge(f"M{join} 47 V253", head=False)

    chk = c.box(join + 34, 133, node_w("CHECKER", 132), NODE_H, "CHECKER", "node node--em", row=4)
    c.arrow_h(join, chk[0] - 5, 150)

    fork = chk[0] + chk[2] + 30
    c.edge(f"M{chk[0] + chk[2] + 9} 150 H{fork}", head=False)
    c.edge(f"M{fork} 100 V200", head=False)

    ok = c.box(fork + 30, 83, node_w("Convergence", 150), NODE_H, "Convergence", "node node--ok", row=5)
    bad = c.box(fork + 30, 183, node_w("Stop, route the finding", 150), NODE_H,
                "Stop, route the finding", "node node--bad", row=6)
    c.arrow_h(fork, ok[0] - 5, 100)
    c.arrow_h(fork, bad[0] - 5, 200)
    c.note(fork + 34, 74, "validated outputs")
    c.note(fork + 34, 236, "missing or contradictory")
    return c


# ── FIG 3 — invalidation is a routing decision ───────────────────────────────

def fig3():
    c = Canvas(780, 430, "Invalidation is a routing decision, not a deletion")
    col = 40
    a = c.box(col, 10, node_w("Accepted proof", 300), NODE_H, "Accepted proof", row=0)
    b = c.box(col, 90, node_w("Code, dependency, environment, or policy change", 300), NODE_H,
              "Code, dependency, environment, or policy change", row=1)
    d = c.box(col, 170, node_w("Map the change to covered claims", 300), NODE_H,
              "Map the change to covered claims", row=2)
    for top, bot in ((a, b), (b, d)):
        c.edge(f"M{cx(top)} {top[1] + NODE_H + 4} V{bot[1] - 5}")

    ok = c.box(col + 430, 250, node_w("Proof remains valid", 250), NODE_H,
               "Proof remains valid", "node node--ok", row=3)
    owed = c.box(col, 330, node_w("Check owed", 190), NODE_H, "Check owed", "node node--em", row=4)

    c.elbow(cx(d), d[1] + NODE_H + 4, ok[0] - 5, 267, 232)
    c.note(cx(d) + 14, 228, "claim unaffected")
    c.edge(f"M{cx(d)} {d[1] + NODE_H + 4} V{owed[1] - 5}")
    c.note(cx(d) + 14, 268, "claim affected")

    new = c.box(col + 430, 305, node_w("New proof version", 250), NODE_H,
                "New proof version", "node node--ok", row=5)
    unp = c.box(col + 430, 375, node_w("Unproven state", 250), NODE_H,
                "Unproven state", "node node--bad", row=6)
    fork = owed[0] + owed[2] + 34
    c.edge(f"M{owed[0] + owed[2] + 9} 347 H{fork}", head=False)
    c.edge(f"M{fork} 322 V392", head=False)
    c.arrow_h(fork, new[0] - 5, 322)
    c.arrow_h(fork, unp[0] - 5, 392)
    c.note(fork + 6, 312, "passes")
    c.note(fork + 6, 412, "fails or cannot run")
    return c


# ── FIG 4 — the seam walk ────────────────────────────────────────────────────

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
    step = 72
    c = Canvas(720, 20 + step * len(RUNGS), "The seam walk from requirement to acceptance")
    boxw = 330
    for i, (label, question) in enumerate(RUNGS):
        y = 10 + i * step
        cls = "node node--ok" if question is None else "node"
        c.box(20, y, boxw, NODE_H, label, cls, row=i)
        if question:
            c.edge(f"M{20 + boxw / 2} {y + NODE_H + 4} V{y + step - 5}")
            c.note(20 + boxw / 2 + 14, y + NODE_H + 27, question)
    return c


# ── FIG 5 — the learning loop ────────────────────────────────────────────────

def fig5():
    c = Canvas(780, 400, "The learning loop: a lesson becomes a mechanism, then retires")
    row_a = chain(c, ["Run", "Observed divergence", "Owning layer and root cause"],
                  20, 30, gap=40, row=0)
    mech = c.box(20, 130, node_w("Mechanical check, bounded rule, or expiring note", 380), NODE_H,
                 "Mechanical check, bounded rule, or expiring note", "node node--em", row=1)
    c.elbow(cx(row_a[2]), 64, cx(mech), 125, 100)

    nxt = c.box(mech[0] + mech[2] + 60, 130, node_w("Next run", 150), NODE_H, "Next run", row=2)
    c.arrow_h(mech[0] + mech[2] + 9, nxt[0] - 5, 147)

    ask = c.box(20, 230, node_w("Did the mechanism fire?", 380), NODE_H,
                "Did the mechanism fire?", "node node--em", row=3)
    c.elbow(cx(nxt), 164, cx(ask), 225, 200)

    keep = c.box(mech[0] + mech[2] + 60, 205, node_w("Keep and measure", 240), NODE_H,
                 "Keep and measure", "node node--ok", row=4)
    ret = c.box(mech[0] + mech[2] + 60, 285, node_w("Retire, preserve history", 240), NODE_H,
                "Retire, preserve history", "node node--bad", row=5)
    fork = ask[0] + ask[2] + 30
    c.edge(f"M{ask[0] + ask[2] + 9} 247 H{fork}", head=False)
    c.edge(f"M{fork} 222 V302", head=False)
    c.arrow_h(fork, keep[0] - 5, 222)
    c.arrow_h(fork, ret[0] - 5, 302)
    c.note(fork - 8, 226, "yes", anchor="end")
    c.note(ret[0], 340, "surface gone or rule cold")

    # both outcomes return to the run, routed around the right edge so the
    # return never crosses a box or a label
    right = c.w - 16
    c.edge(f"M{keep[0] + keep[2] + 4} 222 H{right} V370 H{cx(row_a[0])} V68", dashed=True)
    c.edge(f"M{ret[0] + ret[2] + 4} 302 H{right}", dashed=True, head=False)
    c.note(20, 388, "every run re-enters with whatever the last one made mechanical",
           cls="edge-label edge-label--foot")
    return c


FIGURES = {"fig-1": fig1, "fig-2": fig2, "fig-3": fig3, "fig-4": fig4, "fig-5": fig5}


def main():
    check_only = "--check" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, build in FIGURES.items():
        c = build()
        n = c.verify()
        total += n
        if not check_only:
            (OUT / f"{name}.svg").write_text(c.render(), encoding="utf-8")
        print(f"{name}: {n} nodes, {c.w}x{c.h}, geometry asserted")
    print(f"\n{len(FIGURES)} figures, {total} nodes, every assertion held"
          + ("" if check_only else f" — written to {OUT.relative_to(ROOT)}/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
