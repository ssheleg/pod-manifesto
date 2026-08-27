# Documentation map

This file names the authoritative home of each public fact and the places that
must move with it. A link may repeat; a fact may not.

| Fact | Authoritative home | Required propagation | Executable proof |
|---|---|---|---|
| Canonical manifesto text | `manifesto.md` | `index.html` canonical paragraphs | `tools/check-parity.py` |
| Current manifesto version | newest annotated `v*` tag | `CHANGELOG.md`, HTML/JSON-LD, feed, sitemap, README citation, `CITATION.cff` | `tools/check-version.py` |
| Canonical-text change history | `CHANGELOG.md` | GitHub Release notes link back; do not restate elsewhere | release API + `tools/check-version.py` |
| Published dates | git history of the files described | HTML/JSON-LD, sitemap, `llms.txt` | `tools/stamp-dates.py --check` |
| Citation claims | cited source at its pinned address | notes and machine-readable routes | `tools/check-links.py`, `tools/check-currency.py` |
| Reference implementation behavior | owning `sshlg-skills` / member repositories | this repo links to the owner only | owner repository checks |
| Contribution policy | `CONTRIBUTING.md` | issue forms and README link here | `scripts/check-docs.sh` |
| Canonical-change authority | `GOVERNANCE.md` | README links here | `scripts/check-docs.sh` |
| Security reporting | `SECURITY.md` | issue chooser and README link here | `scripts/check-docs.sh` |
| Reader behavior | `docs/ux/scenarios.md` | implementation and audit report move in the same change | `docs/ux/lint.py` + UX audit |
| Settled repository decisions | `docs/DECISIONS.md` | implementation and governance link to the decision | review + `scripts/check-docs.sh` |
| Unresolved repository questions | `docs/OPEN_QUESTIONS.md` | backlog item links here | review + `scripts/check-docs.sh` |
| Delivery evidence | `docs/evidence/verification.md` | completion report links here | commands recorded with outcomes |

## Propagation rule

Canonical text changes are the only changes that create a manifesto version. Site,
tooling, accessibility, governance, and evidence corrections move their own files and
tests without editing `manifesto.md` or `CHANGELOG.md`.
