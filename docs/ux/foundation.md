<!-- Managed with super-ux (ux-contract v4). The WHY layer: update when the understanding of users changes. -->

# Proof of Done — UX foundation

## 1. Personas

These backwards-mode personas are inferred from the shipped routes and contribution
policy. They remain proposed until direct reader evidence confirms them.

### P-01: Human reader
- **Status:** proposed
- A software practitioner evaluating the manifesto. They want the complete argument, legible in their environment, without installing anything or enabling JavaScript.

### P-02: Machine reader or citer
- **Status:** proposed
- A crawler, language model, research tool, or person using a text-first client. They want an explicit machine-readable route and a stable versioned citation.

### P-03: Contributor or challenger
- **Status:** proposed
- A reader with a counterexample, correction, or translation. They want the right public route and the boundary between the manifesto and its reference implementation.

## 2. Jobs to Be Done

### JTBD-01: Evaluate and cite the standard
- **Status:** proposed
- **Statement:** When I need a trustworthy standard for agent-produced software, I want to read its complete argument and resolve its receipts, so I can evaluate or cite a version that does not move.
- **Personas:** P-01, P-02
- **Type:** functional
- **Forces:** push: completion claims are hard to audit; pull: one evidence-led standard with stable sources; anxiety: the page may be marketing or depend on scripts; habit: rely on an agent's final report.
- **Success metric:** reader reaches the canonical text and, when citing it, uses a versioned address.

### JTBD-02: Challenge or translate the document
- **Status:** proposed
- **Statement:** When I find a defect, counterexample, or translation opportunity, I want to reach the owner with the right evidence and version, so the contribution can be evaluated without losing context.
- **Personas:** P-03
- **Type:** functional
- **Forces:** push: a claim or receipt needs correction; pull: structured objection and translation routes; anxiety: disagreement may be unwelcome or sent to the wrong repository; habit: open an unstructured issue.
- **Success metric:** contributions identify the claim or language, source version, evidence, and expected resolution.

## 3. Customer journeys

### JRN-01: Reader — evaluate and cite (JTBD-01)
| # | Stage | User action | Touchpoint | Emotion (1-5) | Pain | Opportunity |
|---|---|---|---|---|---|---|
| 1 | Discover | follow a link or search result | canonical page | 3 | cannot yet judge authority | show title, position, author, version, source |
| 2 | Evaluate | read and follow receipts | HTML / Markdown | 4 | long document and external evidence | stable contents, anchors, plain text, resolvable receipts |
| 3 | Cite | choose a durable record | README / CFF / git tag | 4 | live URL can move | explicit versioned citation route |

### JRN-02: Contributor — challenge or translate (JTBD-02)
| # | Stage | User action | Touchpoint | Emotion (1-5) | Pain | Opportunity |
|---|---|---|---|---|---|---|
| 1 | Orient | read contribution boundary | README / contribution guide | 3 | manifesto and tooling have different owners | route by subject |
| 2 | Structure | choose a contribution form | GitHub issue chooser | 4 | issue can omit evidence or version | require the fields needed for evaluation |
| 3 | Resolve | follow decision or discussion | issue / pull request | 3 | authored text is not consensus text | make authority and release rules explicit |

## 4. User stories

### ST-001: Read and cite Proof of Done
- **Story:** As P-01 or P-02, I want the complete document in human- and machine-readable forms, so that I can evaluate and cite a stable version.
- **Traces:** JTBD-01, JRN-01/#1-3
- **Acceptance criteria:**
  - Given JavaScript is unavailable, when the reader opens the canonical or Markdown route, then the complete canonical text remains readable.
  - Given the current version is 1.1, when a citation tool or reader follows the versioned source, then the v1.1 text resolves and cannot move with the live page.
- **Priority:** must
- **Status:** delivered
- **Product:** unobserved

### ST-002: Submit an evidence-led contribution
- **Story:** As P-03, I want a route tailored to objections or translations, so that the maintainer receives the version and evidence needed to evaluate it.
- **Traces:** JTBD-02, JRN-02/#1-3
- **Acceptance criteria:**
  - Given a reader challenges a claim, when they open the objection form, then version, claim, kind, evidence, and expected resolution are required.
  - Given a reader is translating the manifesto, when they open the translation form, then language, source version, attribution, and licence commitments are required.
- **Priority:** must
- **Status:** delivered
- **Product:** unobserved

## 5. Monetization

None. The manifesto, site, source, and contribution routes are public and have no paid tier.

## Design tooling
- **Figma:** disabled
- **Figma file:** none — the static HTML/CSS source and browser render are the maintained design record

## Product mechanics
- **Personalization:** rule-based — optional remembered light/dark theme only
- **Engagement mechanics:** none
- **Accessibility regime:** EAA (EU) — maintained by the repository owner through semantic HTML, keyboard routes, contrast, reduced motion, and render checks
