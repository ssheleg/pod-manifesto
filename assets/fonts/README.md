# Self-hosted faces

The SHELEG `field-notes` style pack names three families. They are served from
this repository rather than a font CDN, so the document owes no third-party
request at read time and keeps its typography when a CDN changes or disappears.

| Family | Role in the pack | Upstream | Licence |
|---|---|---|---|
| Bricolage Grotesque | display — headings, the masthead claim | [ateliertriay/bricolage](https://github.com/ateliertriay/bricolage) | [SIL OFL 1.1](OFL-BricolageGrotesque.txt) |
| Geist | body copy | [vercel/geist-font](https://github.com/vercel/geist-font) | [SIL OFL 1.1](OFL-Geist.txt) |
| Geist Mono | annotation — eyebrows, section numbers, tags, the terminal | [vercel/geist-font](https://github.com/vercel/geist-font) | [SIL OFL 1.1](OFL-Geist.txt) |

Each file is the variable woff2 built by Google Fonts, `latin` and `latin-ext`
subsets only, declared in [`fonts.css`](fonts.css) with `font-display: swap`.
Six files, 187 KB in total.

Both licences permit redistribution with the notices kept, which is what the two
`OFL-*.txt` files in this directory are.
