<!-- Managed with super-ux (ux-contract v4). The design map: every screen and state with its Figma frame, wireframe, code coverage, and resources. Update in the same change as any interface change; when Figma is enabled, update the frame too. -->

# Public screen map

## Index
| ID | Screen | Used by | Figma | Status | Coverage |
|---|---|---|---|---|---|
| SCR-01 | Canonical document | SCN-001, SCN-002 | disabled | built | `./index.html:1` |
| SCR-02 | Missing address | SCN-004 | disabled | built | `./404.html:1` |

## Design system
- **Style pack:** custom — editorial memorandum with paper, mono telemetry, and one rust accent
- **Figma library:** none
- **Tokens in code:** `assets/style.css` token block
- **Component source:** static semantic structures in `index.html` and `404.html`
- **Assets:** `assets/`, with generated plates in `assets/figures/`

## Web surfaces
- **Web surfaces:** yes

## Screens

### SCR-01: Canonical document
- **Used by:** SCN-001, SCN-002
- **Purpose:** let a human or machine reader understand, inspect, and cite the current manifesto
- **Elements:** skip link; top bar; Plain text, Source, Install, and theme actions; masthead metadata; table of contents; canonical sections; evidence notes; machine routes; colophon
- **States:**
  | State | Trigger | Figma frame | Behavior |
  |---|---|---|---|
  | success | canonical page loads | disabled | complete document, metadata, navigation, evidence, and alternate formats render |
- **Web surface:**
  - **Route:** `/`
  - **Answers:** what Proof of Done requires from completion claims in agentic software development
  - **Indexable:** yes
  - **Without JS:** complete canonical document, navigation, evidence, and alternate-format links render in semantic HTML
  - **Entity:** schema.org/Article describing Proof of Done v1.1 and its author
- **Coverage:** root `index.html:1-879`, `assets/style.css:1`, `assets/main.js:1`
- **Scenarios:** SCN-001, SCN-002
- **Resources:** `manifesto.md`, `llms.txt`, `feed.xml`, `robots.txt`, `sitemap.xml`, `assets/`
- **Status:** built

### SCR-02: Missing address
- **Used by:** SCN-004
- **Purpose:** make an unresolved address explicit and provide direct recovery and reporting routes
- **Elements:** 404 statement; four-field report; Read the document, Plain text, and Report the link actions
- **States:**
  | State | Trigger | Figma frame | Behavior |
  |---|---|---|---|
  | error | nonexistent path returns HTTP 404 | disabled | states the failure and shows its scope and recovery routes |
  | success | reader follows a recovery action | disabled | canonical document, Markdown, or issue route opens |
- **Web surface:**
  - **Route:** any nonexistent path, rendered by `/404.html`
  - **Answers:** what happened when this address failed and how the reader can recover
  - **Indexable:** no — response and page metadata explicitly identify an error surface
  - **Without JS:** full error explanation and all recovery links render in semantic HTML
  - **Entity:** none — this is an error response, not a citable content entity
- **Coverage:** root `404.html:1-84`, `assets/style.css:1`, `tools/check-live.py:1`
- **Scenarios:** SCN-004
- **Resources:** `assets/style.css`, `manifesto.md`, repository issue route
- **Status:** built
