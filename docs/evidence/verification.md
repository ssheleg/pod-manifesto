# Verification ledger

Run: public repository polish, 2026-08-27  
Scope: branch, pull request, repository settings, release, social preview, and deployed site.  
Canonical manifesto text: excluded from change; included in regression checks.

| Requirement | Proof | Result |
|---|---|---|
| REQ-001 | `bash scripts/check-docs.sh --self-test && bash scripts/check-docs.sh` | PASS locally: planted missing `SUPPORT.md` refused; complete tree accepted |
| REQ-002 | `gh api repos/ssheleg/pod-manifesto/community/profile --jq '.health_percentage'` | PASS: GitHub reports `100`; the documentation gate accepts the hosted community files |
| REQ-003 | Ruleset API readback for `21637026` and `21637027`; repository API readback | PASS: default branch and `v*` tags are protected; `validate` is strict; squash/rebase and branch cleanup are enabled |
| REQ-004 | `gh api repos/ssheleg/pod-manifesto/releases/latest --jq '{tag_name,draft,prerelease,html_url}'` | PASS: `v1.1` is the latest published, non-draft, non-prerelease release |
| REQ-005 | Pages API readback plus `python3 tools/check-live.py --verbose` | PASS: Pages is built with HTTPS enforced; 9 assets resolved and the live check reported 0 failures |
| REQ-006 | GitHub Settings → Social preview readback plus `sips -g pixelWidth -g pixelHeight assets/og.png` | PASS: the settings menu exposes `Remove image` after upload; source asset is 1200×630 |
| REQ-007 | `python3 tools/check-links.py` and YAML parse of `CITATION.cff` | PASS: 45 references, 0 unresolved; structured file parsed |
| REQ-008 | focused, negative, render, UX, CI, and live gates | PASS: 330 canonical sentences; 19/19 planted defects; 0 contrast failures; 50,213 print characters; strict UX lint; hosted `validate` and live workflows succeeded |
| REQ-009 | owner-repository and generated-site evidence below | PASS |

## DeepSeek Harness evidence — REQ-009

- Member: [`agent-stack@5e4eb01:README.md:20-22`](https://github.com/ssheleg/agent-stack/blob/5e4eb01ba2e82f7493d8964b14281f586753bfb4/README.md#L20-L22) states that `dsh` loads the Agent Skills pack directly from `~/.agents/skills`, with no plugin to write.
- Family: [`sshlg-skills@e94e827:README.md:139-180`](https://github.com/ssheleg/sshlg-skills/blob/e94e827c28cd35d31f1032ac6caba5fa1594796b/README.md#L139-L180) explains the default subsystem, scan ranks, diagnostic command, disable keys, and skill/plugin distinction; [`skills.json:211-215`](https://github.com/ssheleg/sshlg-skills/blob/e94e827c28cd35d31f1032ac6caba5fa1594796b/skills.json#L211-L215) carries the generated agent record.
- Public site: [`skills.sshlg.me/agents/#dsh`](https://skills.sshlg.me/agents/#dsh) serves the dedicated DeepSeek Harness section, scan ranks, and no-plugin explanation; fetched successfully on 2026-08-27.
- Boundary: no DeepSeek compatibility copy was added to this manifesto, because `docs/DECISIONS.md` assigns runtime integrations to their owning repositories.

## Remote evidence

- Pull request: [`#2`](https://github.com/ssheleg/pod-manifesto/pull/2), merged as `156d56deb936037e3ea365f918c7d851dd62a0cc`.
- Hosted checks: [`checks` run 33055027335](https://github.com/ssheleg/pod-manifesto/actions/runs/33055027335), including the required `validate` job.
- Live check: [`live` run 33055084588](https://github.com/ssheleg/pod-manifesto/actions/runs/33055084588).
- Release: [`Proof of Done v1.1`](https://github.com/ssheleg/pod-manifesto/releases/tag/v1.1).
- Deployment: [`https://podmanifesto.org`](https://podmanifesto.org).

## Disclosures

- `abstained`: the canonical manifesto text was deliberately left unchanged.
- `unlooked`: third-party social-network caches were not forcibly refreshed; GitHub's
  repository setting itself was verified after upload.
