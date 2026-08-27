<!-- Managed with super-ux (ux-contract v4). Update in the same change as any user-facing behavior change. -->

# Public reader scenarios

| ID | Title | Feature | Persona | Traces | Status | Last audit |
|---|---|---|---|---|---|---|
| SCN-001 | Read the canonical document | reading | P-01 | ST-001 | implemented | 2026-08-27 PASS |
| SCN-002 | Retrieve a stable machine-readable version | citation | P-02 | ST-001 | implemented | 2026-08-27 PASS |
| SCN-003 | Challenge a claim or register a translation | contribution | P-03 | ST-002 | implemented | 2026-08-27 PASS |
| SCN-004 | Recover from a missing address | recovery | P-01 | — | implemented | 2026-08-27 PASS |

## Personas

Personas P-01 through P-03 are defined in [`foundation.md`](foundation.md).

## Reading

### SCN-001: Read the canonical document
- **Persona:** P-01
- **Feature:** reading
- **Traces:** ST-001 (JTBD-01, JRN-01/#1-3)
- **Entry point:** `https://podmanifesto.org/`
- **Preconditions:** a browser or text-capable web client; JavaScript may be disabled
- **Steps:**
  1. Reader opens the canonical URL -> system serves the titled manifesto and its current version over HTTPS
  2. Reader follows the table of contents or scrolls -> system exposes every canonical section in document order
  3. Reader chooses Plain text -> system serves `/manifesto.md` without requiring JavaScript
  4. Reader changes colour theme when JavaScript is available -> system applies and remembers the chosen theme
- **Expected result:** the reader can consume the full canonical document and identify its version, author, source, and plain-text form
- **Alt paths:** reduced-motion preference -> system removes non-essential motion; print -> system renders the complete document rather than hidden reveal states
- **UI elements:** skip link, top bar, table of contents, section anchors, Plain text link, theme button, print stylesheet
- **States covered:** success
- **Errors & recovery:** script or storage unavailable -> document remains readable in the default theme and the plain-text route remains available
- **Status:** implemented
- **Coverage:** root `index.html:1-879`, `assets/style.css:1-900`, `assets/main.js:1-218`, `tools/check-render.py:1-319`
- **Product:** unobserved

## Citation

### SCN-002: Retrieve a stable machine-readable version
- **Persona:** P-02
- **Feature:** citation
- **Traces:** ST-001 (JTBD-01, JRN-01/#2-3)
- **Entry point:** canonical page metadata, `/llms.txt`, `/manifesto.md`, or repository README
- **Preconditions:** HTTP client or repository access
- **Steps:**
  1. Machine reader requests `/llms.txt` -> system names the canonical, Markdown, feed, source, and licence routes
  2. Citer reads the current version -> system reports `1.1` consistently in the published metadata and repository records
  3. Citer follows the versioned source address -> system resolves the immutable `v1.1/manifesto.md` record
  4. Citation tool reads `CITATION.cff` -> system provides title, author, release date, version, URL, repository, and licence
- **Expected result:** the reader can retrieve the text and cite a version whose address does not move
- **Alt paths:** reader follows `/feed.xml` -> system lists canonical-text releases and their versioned addresses
- **UI elements:** alternate-format links, JSON-LD, `llms.txt`, `manifesto.md`, `feed.xml`, `CITATION.cff`
- **States covered:** success
- **Errors & recovery:** live page moves to a later version -> versioned Git tag keeps the cited text reachable
- **Status:** implemented
- **Coverage:** `tools/check-version.py:1-130`, `tools/check-links.py:1-214`, `tools/check-live.py:1-356`
- **Product:** unobserved

## Contribution

### SCN-003: Challenge a claim or register a translation
- **Persona:** P-03
- **Feature:** contribution
- **Traces:** ST-002 (JTBD-02, JRN-02/#1-3)
- **Entry point:** repository README, `CONTRIBUTING.md`, or GitHub issue chooser
- **Preconditions:** GitHub account for opening an issue
- **Steps:**
  1. Challenger opens contribution guidance -> system explains what a useful objection contains and where tooling issues belong
  2. Challenger selects Objection or correction -> system asks for version, claim, objection kind, evidence, and expected resolution
  3. Translator selects Translation -> system asks for language, source version, state, address, attribution, and licence confirmation
- **Expected result:** the contribution reaches the repository that owns it with enough structure to evaluate it
- **Alt paths:** report concerns security -> system routes to a private vulnerability report; implementation support -> system routes to `sshlg-skills`
- **UI elements:** README contribution links, contribution guide, issue chooser, objection form, translation form, security and support links
- **States covered:** success, error
- **Errors & recovery:** contributor starts in the wrong repository -> support and issue chooser link to the owning repository without discarding the report context
- **Status:** implemented
- **Coverage:** `docs/../.github/ISSUE_TEMPLATE/objection.yml:1-55`, `docs/../.github/ISSUE_TEMPLATE/translation.yml:1-51`
- **Product:** unobserved

## Recovery

### SCN-004: Recover from a missing address
- **Persona:** P-01
- **Feature:** recovery
- **Entry point:** any nonexistent path on `podmanifesto.org`
- **Preconditions:** requested path does not exist
- **Steps:**
  1. Reader requests a missing address -> system responds with HTTP 404 and an explicit statement that the address does not resolve
  2. Reader chooses Read the document or Plain text -> system returns the canonical page or Markdown route
  3. Reader chooses Report the link -> system opens the repository issue route
- **Expected result:** the reader understands the failure and has direct recovery and reporting paths
- **Alt paths:** none; the page deliberately exposes the same three recovery routes to every missing path
- **UI elements:** 404 heading, four-field report, Read the document, Plain text, Report the link
- **States covered:** error, success
- **Errors & recovery:** target was intentionally removed -> versioned Git tags remain the recovery route for historical manifesto text
- **Status:** implemented
- **Coverage:** root `404.html:1-84`, `tools/check-live.py:1-356`, `assets/style.css:1-900`
- **Product:** unobserved
