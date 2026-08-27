# Public repository polish — design specification

Date: 2026-08-27  
Status: approved for implementation  
Decision: strengthen trust, governance, release, and machine-readable evidence without redesigning the manifesto.

## Global Constraints

- The canonical English manifesto remains byte-for-byte semantically unchanged unless an existing gate proves a defect.
- Existing visual hierarchy, theme behavior, reduced-motion behavior, and stable URLs remain intact.
- One fact has one owner. README links to deeper governance; it does not duplicate it.
- Every newly stated repository fact is either executable evidence or points to its proof.
- Public machine-reader routes continue to work without JavaScript.
- DeepSeek Harness support remains documented in the owning `agent-stack` and `sshlg-skills` repositories; this manifesto does not claim ownership of that integration.

## Evidence architecture

covers: REQ-001

Create a compact documentation control plane:

- `docs/DOCMAP.md` names authoritative homes and propagation paths;
- `docs/DECISIONS.md` records settled repository decisions;
- `docs/OPEN_QUESTIONS.md` is the only unresolved-question register;
- `docs/evidence/backlog.md`, `verification.md`, and `retro.md` carry delivery evidence;
- `scripts/check-docs.sh` validates required homes, links, version alignment, and the presence of the CI invocation.

Failure behavior: missing homes, broken internal references, a stale version, or an unwired checker must return non-zero with the exact failing invariant.

## Contributor and trust surfaces

covers: REQ-002

Add tailored conduct, security, support, governance, issue-form, pull-request,
ownership, and citation surfaces. Objections are first-class contributions;
translation requests are separated from changes to the canonical English text.

Failure behavior: issue forms must validate as YAML, required contact routes must
resolve, and the documentation gate must fail if a trust surface disappears.

## Repository governance

covers: REQ-003

Protect `main` with deletion and force-push prevention, linear history, pull
requests, resolved review threads, and the strict `validate` status context.
Protect `v*` tags against deletion and mutation. Allow squash and rebase merges,
disable merge commits, and delete merged branches.

Failure behavior: remote configuration is read back through the GitHub API and
compared with this policy before the task closes.

## Release truth

covers: REQ-004

Publish the existing annotated `v1.1` tag as the latest GitHub Release. Release
notes summarize the existing `CHANGELOG.md` entry and link to the stable site;
no new tag or manifesto version is created.

Failure behavior: the release API must report tag `v1.1`, latest=true, draft=false,
and prerelease=false.

## Delivery and discoverability

covers: REQ-005, REQ-006

Enable the repository-level Pages HTTPS setting, preserve the custom domain, and
verify redirect, TLS response, HSTS, rendered content, assets, crawler routes,
and 404 behavior. Upload the existing validated 1200×630 `assets/og.png` as the
GitHub social preview; the website's existing Open Graph image remains unchanged.

Failure behavior: the live gate must fail on content drift, blocked crawler
routes, asset failure, or missing 404 behavior. Remote settings are verified by
API or, where GitHub exposes no API, by a captured UI check.

## README and citation

covers: REQ-007

Keep the current hero and reading hierarchy. Add compact build, live, release,
and license status; link to governance, support, security, contribution, and a
machine-readable `CITATION.cff`. Avoid badge walls and duplicated prose.

Failure behavior: README links are covered by the repository link checker.

## Regression contract

covers: REQ-008

Modernize official checkout actions, add least-privilege workflow permissions,
and aggregate every existing job under a final `validate` job. Preserve all
thirteen focused checks, the 19 planted negative cases, render/print checks, and
live-site acceptance. Add compact scenarios for human, machine, and contributor
paths and audit their implementation evidence.

Failure behavior: `validate` fails if any dependency is skipped, cancelled, or
failed; local execution remains possible without GitHub.

## DeepSeek Harness boundary

covers: REQ-009

Verify, rather than duplicate, the existing support claims in the owning family
and member repositories and in their generated public site. Record file-and-line
evidence in the verification ledger.

Failure behavior: a missing family/member/site claim is a release blocker for
this task, but it is corrected in its owner repository—not in the manifesto.
