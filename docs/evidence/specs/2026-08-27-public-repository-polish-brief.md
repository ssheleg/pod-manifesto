# Task brief — public repository polish

> Stage-0 intake artifact. Confirmed decisions are frozen for this run; the
> canonical manifesto text remains outside the change.

- **Date:** 2026-08-27
- **Task:** bring `pod-manifesto` to the same public-repository standard as the
  ssheleg skill family without changing the canonical manifesto.
- **UI verdict:** no product-behaviour change. The published document is audited
  as a web surface, but this run changes repository trust, governance and release
  surfaces rather than the reading experience.

## Knowledge sources

| Source | What it says about this task | Fresh? | Authority | Stale after this run? |
|---|---|---|---|---|
| `manifesto.md` | canonical text; it does not change without a version | current at `v1.1` | canonical content | no — unchanged |
| `README.md` | repository map, checks, citation and contribution paths | current at `f3be855` | repository documentation | yes |
| `CHANGELOG.md` | `v1.1` is the newest canonical version | current | version history | no |
| `.github/workflows/checks.yml` and `live.yml` | local and deployed gates already exist | current | executable mechanism | yes |
| `tools/` | 13 checks, negative controls, render and live verification | executed 2026-08-27 | code | yes |
| GitHub API: repository, Pages, rulesets, community profile, releases | no rulesets; community health 62%; tag `v1.1` exists but latest GitHub Release is `v1.0`; Pages reports `https_enforced: false` | measured 2026-08-27 | production state | yes |
| `https://podmanifesto.org/` | HTTP redirects to HTTPS; HTTPS serves HSTS; live bytes match the checkout | measured 2026-08-27 | production surface | yes |
| wiki: `projects/sshlg-home/concepts/crediting-prior-art.md` | the manifesto credits borrowed methods and measures the comparison | updated 2026-08-06 | context | no |
| wiki: `projects/sshlg-home/concepts/evidence-ledger-per-post.md` | public claims should ship with reachable evidence | updated 2026-08-05 | context | no |
| `/Users/sshlg/DATA/agent-stack/README.md` and `/Users/sshlg/DATA/sshlg-skills/README.md` | DeepSeek Harness support is documented; `dsh` reads Agent Skills directly | current | owner repositories | no |

**Contradictions:** GitHub Pages reports `https_enforced: false`, while the live
Cloudflare edge redirects HTTP to HTTPS and serves HSTS. This is not a live
availability failure; it is a settings-level gap to close and re-measure. GitHub
also presents `v1.0` as the latest Release while the annotated `v1.1` tag and every
in-document version statement agree on `v1.1`; the Release surface is stale.

## Documentation inventory

| Question | Answer |
|---|---|
| Regime | brownfield adoption approved for this run |
| Decision home | seed `docs/DECISIONS.md` (`DEC-####`) |
| Open questions | seed `docs/OPEN_QUESTIONS.md` (`OQ-####`) |
| Doc map | seed `docs/DOCMAP.md`, tailored to this repository |
| Gate | seed `scripts/check-docs.sh`, prove it with a planted failure, then add it to CI |
| Shared state | **ungated** — no `.claude/agent-sync.json`; one agent owns this run |
| Intent vs as-built | `v1.1` intent is current in the files; GitHub Release and repository protections lag it |

- **Artifact root:** `docs/evidence/` — the default; it did not exist before this run.
- **External doc systems:** GitHub repository settings and GitHub Pages.
- **Knowledge wiki:** present and queried; QMD collection is not configured, so
  GraphRAG plus targeted page reads were used.
- **Retro:** absent before this run; seed it during adoption.
- **Code graph:** `graphify` installed but no project graph built; build and compare
  it during close-out.

## Scope

### In scope

- Adopt a minimal, executable documentation regime appropriate for a public
  manifesto repository.
- Add the missing GitHub community-health surfaces and public trust metadata.
- Bring branch, tag, merge and security settings to the family standard.
- Publish the existing annotated tag `v1.1` as the latest GitHub Release.
- Ensure the repository has a correct 1200×630 social preview and upload it.
- Verify GitHub Pages HTTPS and the deployed document after merge.
- Keep DeepSeek Harness compatibility information accurate in its owning
  repositories; report its verified state here without duplicating it into the
  manifesto.

### Out of scope

- Any edit to `manifesto.md`, its rendered canonical prose, or the meaning of
  `v1.1`.
- A visual redesign, new Figma file, new JavaScript dependency, package release,
  translation, or new product claim.
- Back-filling historical repository decisions from git history.

## Requirements

| ID | Requirement | How it is verified | Status |
|---|---|---|---|
| REQ-001 | The project has one decision home, one doc map, an open-question register, a retro and an executable doc gate wired into CI. | `bash scripts/check-docs.sh`; planted-failure probe; workflow inspection | open |
| REQ-002 | GitHub community-health surfaces cover conduct, security, issues, pull requests, support and citation without duplicating the canonical manifesto. | GitHub community profile API; local link checks | open |
| REQ-003 | `main` and `v*` tags have active rulesets matching the public family baseline; merges are linear and stale branches are deleted. | GitHub rulesets and repository APIs | open |
| REQ-004 | The existing annotated `v1.1` tag is the latest GitHub Release with notes that match `CHANGELOG.md`. | GitHub Releases API; `git cat-file -t v1.1` = `tag` | open |
| REQ-005 | HTTPS is enforced at the repository setting and at the live edge without breaking the custom domain. | Pages API; HTTP redirect; HTTPS HSTS; `check-live.py` | open |
| REQ-006 | GitHub social preview uses the repository's validated 1200×630 image. | image dimensions plus visual inspection of repository settings | open |
| REQ-007 | README exposes build status, current version, site and licence at a glance while preserving its existing editorial hierarchy. | rendered README review; link check; canonical-parity suite | open |
| REQ-008 | Every existing local, render, negative and live gate remains green after the change. | full command set from `README.md`; GitHub Actions checks | open |
| REQ-009 | DeepSeek Harness support is demonstrably documented at the family, member and public-site levels, with no redundant manifesto claim added. | targeted `rg` across `agent-stack` and `sshlg-skills`; public-site check | open |

## Users and context

- **Readers:** engineers evaluating the manifesto, agents retrieving or citing it,
  contributors proposing objections or translations, and maintainers releasing a
  new canonical version.
- **Job:** determine quickly what is authoritative, how to cite it, how to challenge
  it, whether the repository is maintained, and whether its completion claims are
  mechanically supported.
- **Constraints:** static GitHub Pages site behind Cloudflare; zero application
  dependencies; dual licence; canonical prose is versioned and frozen for this run.

## Decisions locked

| # | Decision | Chosen | Rationale |
|---|---|---|---|
| 1 | Canonical text | preserve `v1.1` byte-for-byte | operator confirmed; no semantic defect was found |
| 2 | Change shape | repository trust and release polish, not redesign | the document/site already pass their own deep gates |
| 3 | Integration | branch → PR → green checks → squash merge | validates the protections being introduced |
| 4 | Release | publish the existing annotated `v1.1` tag; do not mint a new tag | the tag and document already agree; only the Release surface is stale |
| 5 | Documentation adoption | start today; do not reconstruct historical rationale | brownfield adoption must not invent history |
| 6 | DeepSeek Harness | keep the detailed claim in the skill-family owner repositories | avoids making the manifesto a second compatibility registry |

## Autonomy

| Stage | Question | Answer |
|---|---|---|
| run-wide | Model | current model, confirmed by the operator |
| run-wide | Escalation | decide reversible repository edits autonomously; stop on legal/canonical-text changes or new outward targets |
| run-wide | Pacing | loop mode off; advance autonomously between manual gates |
| 0 Harvest | External sources and write-back | GitHub and live site may be read; approved GitHub settings, Release, PR and merge may be written; wiki may be synced at stage 9 |
| 0 Duplicates | Which copies ship | `manifesto.md` is canonical; `index.html` renders it and `check-parity.py` enforces both directions; Pages deploys repository root from `main` |
| 0 Fixtures | Persistent local state | none; checks use repository files and isolated temp directories |
| 0 Source | Upstream freshness | `git rev-list --count HEAD..@{u}` → `0`; `@{u}..HEAD` → `0` before the first edit |
| 0 Work-list | Task register | none before adoption; use `docs/evidence/backlog.md` after seeding |
| 0 Setup audit | Run the entry audit | yes, explicitly approved 2026-08-27 |
| 0 Docs regime | Governance | seed one register and one gate; this run is `ungated`; floors start at the measured adoption baseline |
| 1 Docs | External contracts | current official GitHub documentation only for rulesets, Releases, Pages and community health |
| 2 Decompose | Shape | one release unit with local-file and remote-setting workstreams; deploy once after merge |
| 2–3 Spec | UI | no behaviour change and no scenario waiver needed; audit the existing live surface |
| 3 Design surface | Figma | off — no redesign; reuse and validate the existing `assets/og.png` |
| 4–5 Dev | Branch and commits | base `main`; branch `codex/pod-public-polish`; conventional focused commits; `main` is not edited directly |
| 5 Integration | Landing | PR, green required checks, squash merge; self-merge authorized |
| 6 Tests | Green | every command listed in README passes; negative controls refuse their plants; no known-red baseline |
| 7 Lint | Command | existing pack, HTML, parity, figures, version and link gates plus the new doc gate |
| 7 Deploy | Target and authorization | GitHub Pages production at `podmanifesto.org`, automatically from merged `main`; Release/settings/rulesets/PR/merge explicitly authorized after green checks |
| 8 Post-deploy | Health | `https://podmanifesto.org/`, Pages API, Actions `live` workflow and `tools/check-live.py` |
| 9 Docs and wiki | Sync | update README/community docs and the queried wiki project state; build/refresh graphify output and compare it to the doc map |
| 10 Acceptance | Sign-off | operator; deferred work goes to `docs/evidence/backlog.md`; seed and update `docs/evidence/retro.md` last |

## Done criteria

- All REQ rows are `verified` or carry an explicit, addressable deferral.
- Local full suite, negative controls, CI, Pages deployment and post-deploy live
  check are green.
- GitHub APIs show active protections, current Release, intended merge/security
  settings and HTTPS enforcement.
- The social preview is visibly installed.
- The repository is clean, pushed, merged, and local `main` matches `origin/main`.

## Open assumptions and risks

- GitHub may not expose social-preview upload through an API. If so, use the
  authenticated GUI and verify visually; do not claim success from the local file.
- Enabling Pages HTTPS may temporarily report `pending`; keep the live redirect in
  place and wait for the Pages health state rather than removing the custom domain.
- GitHub's community-health percentage may remain below 100 because the repository
  intentionally uses a dual custom licence; file presence and semantics matter more
  than the scalar.
