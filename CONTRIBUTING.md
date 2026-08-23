# Disagreeing with this document

The licence says *argue with it*, and an invitation with no address is decoration. This is
the address.

## What a useful objection looks like

The document's own standard applies to objections to it. The strongest ones name a
specific sentence and say what would have to be observed for it to be wrong:

- **"This claim is false, and here is the case."** A run, a repository, a measurement where
  the rule produced the outcome it says it prevents. This is the most valuable kind and the
  rarest.
- **"This claim is unfalsifiable."** If no observation could contradict a sentence, it is a
  slogan wearing an argument's clothes, and it should be cut or sharpened.
- **"This costs more than it says."** The document claims proof should be produced as a
  side effect of the work. Where it isn't — where following this adds real overhead the
  text does not acknowledge — that is a defect in the document, not in your team.
- **"The receipt no longer says this."** Every case here resolves to a public commit. If
  one has gone stale, that is the failure the document is about, happening to it. Say so.

Less useful, and stated plainly so nobody spends an evening on it: that the document is
long, that manifestos should not have citations, or that agents will make all of this
unnecessary. The first is [`R10` in the audit](https://github.com/ssheleg/pod-manifesto/issues)
and known; the second is a genre preference; the third is a prediction, and predictions are
not evidence in either direction.

## Where to put it

**Open an issue.** One objection per issue, naming the section. `manifesto.md` line numbers
move between versions — quote the sentence instead, or cite the tag:
`https://github.com/ssheleg/pod-manifesto/blob/v1.0/manifesto.md`.

A pull request against the canonical text is welcome for a factual error, a broken
reference, a number that no longer computes, or a typo. For an argument, open the issue
first: the text is one author's position and a merged paragraph would make it two.

## Translations

There are none yet, and the licence permits them: CC BY 4.0, attribution and a link back.

If you translate it, open an issue with the address and it will be linked from here and
from the document. Two requests, both from the text's own doctrine: translate the canonical
sentences rather than a summary of them, and state the version you translated — a
translation of v1.0 stays a translation of v1.0 after this document reaches v1.1.

## The site and the tooling

Ordinary contributions. Every check runs on every push and is listed in
[`README.md`](README.md); `tools/negatives.py` feeds each of them a planted defect and
requires a refusal, so a new gate arrives with the case that proves it can fail. A gate
with no negative control will be asked for one.

## What is out of scope

The reference implementation lives in
[`sshlg-skills`](https://github.com/ssheleg/sshlg-skills) and
[`task-pipeline`](https://github.com/ssheleg/task-pipeline). Bugs in the tooling belong
there. The manifesto is not the authority for those repositories and they are not the
authority for it.
