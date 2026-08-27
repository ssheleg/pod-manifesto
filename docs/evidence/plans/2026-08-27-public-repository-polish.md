# Public repository polish — implementation plan

Date: 2026-08-27  
Branch: `codex/pod-public-polish`  
Brief: `docs/evidence/specs/2026-08-27-public-repository-polish-brief.md`  
Design: `docs/evidence/specs/2026-08-27-public-repository-polish-design.md`

## Tasks

1. **Adopt the evidence spine** — create the documentation map, decisions,
   questions, backlog, verification ledger, retro, and executable documentation
   gate; plant and prove a missing-file failure. Implements REQ-001.
2. **Add community health** — add conduct, security, support, governance,
   ownership, objection/translation issue forms, and a PR template. Implements
   REQ-002.
3. **Clarify status and citation** — add compact README status/navigation and
   `CITATION.cff`. Implements REQ-007.
4. **Describe and audit public behavior** — add the compact scenario contract,
   install the UX linter, and record implementation coverage. Implements REQ-008.
5. **Harden CI** — update official checkout actions, set least-privilege
   permissions, wire the documentation and UX gates, and add the final `validate`
   context. Implements REQ-001 and REQ-008.
6. **Run local certification** — run documentation, UX, parity, links, dates,
   version, currency, downloads, pack, figures, render, print, negative, and live
   probes; verify DeepSeek Harness claims in their owner repositories. Implements
   REQ-008 and REQ-009.
7. **Deliver through GitHub** — push, open a PR, wait for checks, configure and
   read back default-branch/tag rulesets and repository/Pages security settings,
   then merge the green PR. Implements REQ-003 and REQ-005.
8. **Publish the existing release** — create the latest non-prerelease GitHub
   Release from annotated tag `v1.1` and verify the API response. Implements
   REQ-004.
9. **Set social preview** — upload validated `assets/og.png` to the repository
   social-preview setting and verify the rendered setting. Implements REQ-006.
10. **Post-deploy acceptance** — wait for Pages, run the live suite against the
    merged commit, audit every requirement, and complete the verification ledger
    and retro. Implements REQ-005 and REQ-008.

## Dependency graph

- Tasks 1–5 can be implemented as one coherent local change.
- Task 6 depends on 1–5.
- Task 7 depends on 6.
- Tasks 8 and 9 depend on the merged result from 7.
- Task 10 depends on 7–9.

The executable graph lives in `.task-pipeline/graph.json`; the directory is
ignored because run state is not repository evidence.

## Self-review

- Requirement coverage is exact: REQ-001 through REQ-009 all have at least one
  implementing task; no task invents an unapproved requirement.
- Every implementation task names both files/surfaces and a proving check.
- Remote mutations occur only after local gates pass and are read back afterward.
- The plan contains no task that changes the canonical manifesto text.
