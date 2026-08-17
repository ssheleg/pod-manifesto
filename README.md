# Proof of Done: The Agentic Software Development Manifesto

**A foundation for building software when agents write the code.**

> When agents write the code, done is not the last message of the run.
> Done is a state of the system that can be proven.

**Read it:** [podmanifesto.org](https://podmanifesto.org) &middot; **Full text:** [`manifesto.md`](manifesto.md)

---

## The reference implementation

The process this document argues for is packaged as installable skills and Claude Code
plugins — [`sshlg-skills`](https://github.com/ssheleg/sshlg-skills):

```bash
npx sshlg-skills install
```

The implementation is evidence that this process can run. It is not the authority for the
manifesto: the four-field protocol, the three graphs and the seam walk survive every tool
and package name in that repository changing.

---

## The smallest version of it

```text
DONE
  What became true.

PROOF
  What was executed or observed, and where the result lives.

SCOPE
  The commit, environment, requirements, and surfaces covered.

NOT VERIFIED
  What was not checked, could not be checked, or remains uncertain.
```

`NOT VERIFIED: none within the stated scope` is a valid answer. Silence is not.

---

## This repository

| Path | What it is |
|---|---|
| [`manifesto.md`](manifesto.md) | **The canonical text.** Everything else renders it; nothing else restates it. |
| `index.html` | The published document at [podmanifesto.org](https://podmanifesto.org). |
| `assets/` | Stylesheet and the small progressive-enhancement script. No frameworks, no CDN. |
| `llms.txt` | The document indexed for language models and crawling agents. |
| `tools/` | The two checks below. |
| `CNAME` | The custom domain served by GitHub Pages. |

### The checks

"The site matches the text" and "the references resolve" are commands with exit codes
here, not sentences in a commit message. Both run on every push
([`.github/workflows/checks.yml`](.github/workflows/checks.yml)):

```bash
python3 tools/check-parity.py --verbose   # every canonical sentence of manifesto.md is on the page
python3 tools/check-links.py              # every published reference resolves
```

The site is static, dependency-free, and readable with JavaScript disabled. The text is
addressed to two readers: a person, and the agent that will quote it.

## Licence

Text: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — quote it, translate it,
adopt it, argue with it; keep the attribution and the link.
Site code: [MIT](LICENSE).

## Author

Sergey Sheleg (Siarhei Sheleh) — [github.com/ssheleg](https://github.com/ssheleg)
