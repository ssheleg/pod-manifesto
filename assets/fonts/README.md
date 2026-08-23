# Self-hosted faces

Two families, two jobs. Both are served from this repository rather than a font
CDN, so the page owes no third-party request for its typography and keeps its
typography when a CDN changes.

| Family | Role | Upstream | Licence |
|---|---|---|---|
| Geist | body copy — the prose, the ledes, the table cells, the figure names | [vercel/geist-font](https://github.com/vercel/geist-font) | [SIL OFL 1.1](OFL-Geist.txt) |
| JetBrains Mono | the display, and everything that narrates system state: telemetry labels, section indices, tags, the console | [JetBrains/JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) | [SIL OFL 1.1](OFL-JetBrainsMono.txt) |

Four files, 124 KB in total: variable woff2 built by Google Fonts, `latin` and
`latin-ext` subsets only, declared in [`fonts.css`](fonts.css) with
`font-display: swap`.

## Two deviations from the pack, and one reversal

The SHELEG `instrument-console` pack specifies **Geist Sans for display and body,
Geist Mono for data**. This page keeps its body and deviates on two points:

- the **display** is set in mono, because the register asked for is a terminal;
- the mono is **JetBrains Mono** rather than Geist Mono, for the same reason.

A third deviation was tried and reverted: the whole document set in mono. At
8,000 words it cost more legibility than the register was worth — the reason the
pack states the rule is the reason it was put back. The reversal is recorded here
rather than deleted, because a decision that was tested is worth more than one
that was assumed.

Each `OFL-*.txt` is the SIL Open Font Licence 1.1 with its upstream copyright
line; both licences permit redistribution with the notice kept.
