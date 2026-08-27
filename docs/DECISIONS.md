# Repository decisions

## D-001 — The English Markdown file is canonical

- **Status:** accepted
- **Decision:** `manifesto.md` owns the canonical sentences. HTML renders them and may add navigation, metadata, evidence apparatus, and colophon material, but not alternate canonical prose.
- **Proof:** `python3 tools/check-parity.py --verbose` compares both surfaces.

## D-002 — Canonical changes are versioned; site corrections are not

- **Status:** accepted
- **Decision:** every canonical sentence change creates a changelog entry and annotated version tag. Presentation, tooling, governance, and evidence corrections do not.
- **Proof:** `CHANGELOG.md` states the rule and `python3 tools/check-version.py --verbose` enforces the current version surfaces.

## D-003 — Public proof has three levels

- **Status:** accepted
- **Decision:** focused repository checks prove individual invariants; the `validate` CI context proves the whole pull request; the live workflow proves the deployed subject.
- **Proof:** `.github/workflows/checks.yml`, `.github/workflows/live.yml`, and `tools/check-live.py`.

## D-004 — Integrations are documented by their owner

- **Status:** accepted
- **Decision:** DeepSeek Harness and other agent-runtime support belongs in `agent-stack`, `sshlg-skills`, and their generated site. This repository links to the reference implementation but does not duplicate its compatibility matrix.
- **Proof:** recorded under REQ-009 in `docs/evidence/verification.md`.
