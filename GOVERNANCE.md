# Governance

## Authority

Proof of Done is an authored manifesto maintained by Sergey Sheleg. Contributions are
welcome; merge authority and release decisions remain with the maintainer so the text
does not silently become a committee document.

## Changing the canonical text

Start with one objection issue that quotes or identifies the claim and supplies the
case against it. A canonical change to `manifesto.md` requires:

1. an accepted issue or an explicit maintainer decision;
2. matching updates to every rendered canonical sentence;
3. a new semantic version, changelog entry, feed entry, and annotated tag;
4. all parity, citation, version, render, negative, and live gates green;
5. a GitHub Release from that tag.

Translations name the source version and remain translations; they do not replace the
canonical English text.

## Changing the repository or site

Corrections to presentation, accessibility, tooling, citations, or repository
governance use an ordinary pull request. They do not create a manifesto version unless
the canonical text changes. The default branch is protected, release tags are immutable,
and the CI `validate` context is the merge gate.

## Decisions and unresolved work

Settled repository decisions live in [`docs/DECISIONS.md`](docs/DECISIONS.md).
Unresolved questions live in [`docs/OPEN_QUESTIONS.md`](docs/OPEN_QUESTIONS.md).
The documentation map identifies the authoritative home for every public fact.
