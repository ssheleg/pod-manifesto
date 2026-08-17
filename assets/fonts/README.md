# Self-hosted faces

The SHELEG `instrument-console` style pack names two families. They are served from
this repository rather than a font CDN, so the document owes no third-party
request at read time and keeps its typography when a CDN changes or disappears.

| Family | Role in the pack | Upstream | Licence |
|---|---|---|---|
| Geist | display and body — the pack sets headlines in the same neutral grotesk | [vercel/geist-font](https://github.com/vercel/geist-font) | [SIL OFL 1.1](OFL-Geist.txt) |
| Geist Mono | telemetry — labels, section indices, tags, the console | [vercel/geist-font](https://github.com/vercel/geist-font) | [SIL OFL 1.1](OFL-Geist.txt) |

Each file is the variable woff2 built by Google Fonts, `latin` and `latin-ext`
subsets only, declared in [`fonts.css`](fonts.css) with `font-display: swap`.
Four files, 81 KB in total.

Both licences permit redistribution with the notices kept, which is what the two
`OFL-*.txt` files in this directory are.
