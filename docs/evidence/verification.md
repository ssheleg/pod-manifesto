# Verification ledger

Run: public repository polish, 2026-08-27  
Scope: branch, pull request, repository settings, release, social preview, and deployed site.  
Canonical manifesto text: excluded from change; included in regression checks.

| Requirement | Proof | Result |
|---|---|---|
| REQ-001 | `bash scripts/check-docs.sh --self-test && bash scripts/check-docs.sh` | PASS locally: planted missing `SUPPORT.md` refused; complete tree accepted |
| REQ-002 | community profile API and documentation gate | local files PASS; hosted community profile pending push |
| REQ-003 | ruleset and repository-setting API readback | pending |
| REQ-004 | GitHub Release API readback for `v1.1` | pending |
| REQ-005 | Pages API readback plus `python3 tools/check-live.py --verbose` | pending |
| REQ-006 | visual readback of GitHub social-preview setting | pending |
| REQ-007 | `python3 tools/check-links.py` and YAML parse of `CITATION.cff` | PASS: 45 references, 0 unresolved; structured file parsed |
| REQ-008 | focused, negative, render, UX, CI, and live gates | local PASS: 330 canonical sentences; 19/19 planted defects; 0 contrast failures; 50,213 print characters; strict UX lint; live 0 failures; hosted CI pending |
| REQ-009 | owner-repository and generated-site evidence below | PASS |

## DeepSeek Harness evidence — REQ-009

- Member: [`agent-stack@5e4eb01:README.md:20-22`](https://github.com/ssheleg/agent-stack/blob/5e4eb01ba2e82f7493d8964b14281f586753bfb4/README.md#L20-L22) states that `dsh` loads the Agent Skills pack directly from `~/.agents/skills`, with no plugin to write.
- Family: [`sshlg-skills@e94e827:README.md:139-180`](https://github.com/ssheleg/sshlg-skills/blob/e94e827c28cd35d31f1032ac6caba5fa1594796b/README.md#L139-L180) explains the default subsystem, scan ranks, diagnostic command, disable keys, and skill/plugin distinction; [`skills.json:211-215`](https://github.com/ssheleg/sshlg-skills/blob/e94e827c28cd35d31f1032ac6caba5fa1594796b/skills.json#L211-L215) carries the generated agent record.
- Public site: [`skills.sshlg.me/agents/#dsh`](https://skills.sshlg.me/agents/#dsh) serves the dedicated DeepSeek Harness section, scan ranks, and no-plugin explanation; fetched successfully on 2026-08-27.
- Boundary: no DeepSeek compatibility copy was added to this manifesto, because `docs/DECISIONS.md` assigns runtime integrations to their owning repositories.

## Limits

This ledger is incomplete until the merged commit is deployed. A pending row is not a
pass and must not be summarized as one.
