# Changelog

This document argues that a proof is scoped, versioned and perishable. It owes the same
to itself: a reader who quotes a sentence should be able to say which version they quoted,
and reach that version after the text has moved on.

**The rule from v1.0 onward:** any change to the canonical text in `manifesto.md` — a
sentence added, removed, reworded, or moved to a different section — is a new version with
an entry here. Corrections to the site, the tooling, the CI or the prose *about* the
document are not, and are not listed.

Every released version is a git tag. The tag is the citable address:

```
https://github.com/ssheleg/pod-manifesto/blob/v1.1/manifesto.md
```

---

## v1.1: 2026-08-25

The positioning line now names what the manifesto is for: **The standard for building
software with AI agents.** It replaces "A foundation for building software when agents
write the code."

No protocol, definition, belief or engineering requirement changed. This release changes
one canonical line so the manifesto, its site, repository and social preview introduce the
same thing in the same words.

---

## v1.0 — 2026-08-23

The first public release. The text was first published on 2026-08-17 and corrected in
place until this tag; from here it does not change without a version.

**What the document says.** Proof of Done requires every completion claim between an
intended outcome and an accepted result to point to its supporting record at an address
another actor can resolve. Eight sections and a declaration of seven beliefs, built on the
four-field report — `DONE`, `PROOF`, `SCOPE`, `NOT VERIFIED` — the three graphs, bounded
autonomy, the Proof record, the seam walk, and the learning loop.

**Corrected between first publication and this tag, and worth naming because the document
argues against silent correction:**

- A paragraph in §8 asserted for two days and six hours that four named requirements were
  open backlog rows. The first of them had closed on 2026-08-17 at 11:49; the paragraph
  was corrected on 2026-08-19 at 18:01. Both permalinks resolved throughout and the link
  check was green, because a permalink is pinned to a commit: a citation that resolves is
  not the same as a citation that is current. `tools/check-currency.py` exists because of
  this, and the interval above is recomputed from its endpoint commits rather than typed.
- The assertion moved to the front. The four values were a subsection of §2 and the
  declaration was the last page — seven thousand words stood between a reader and the
  thing they would quote. `## The manifesto` now opens the document and carries the
  declaration, the values and the protocol; nothing was rewritten to do it, and the coda
  keeps its ending under `## The close`. The seven beliefs are numbered so one can be named.
- Ten sentences stated a norm as a personal preference. "I treat a requirement with no
  observable as unfinished" invites the reader to answer "I don't", which is not what the
  sentence means. First person now marks witness only.
- §4 has asserted since publication that two agents agree independently only when their
  evidence paths differ, and cited nothing for it. The reference implementation built the
  mechanism at v1.74.0 — three readings that cannot see one another — and it is cited now.

**Corrected in the site rather than the text**, listed here only because two of them were
live and neither was visible to any check: the document printed 27 of its 30 pages blank,
and the edge was serving a `robots.txt` that disallowed nine AI crawlers on a document
written for them. Both are in `git log`; neither changed a canonical sentence.
