# Delivery retro — public repository polish

Status: complete.

## Run stamp

| Date | Topic | Delivered commit | Verdict | Counts |
|---|---|---|---|---|
| 2026-08-27 | Public repository polish | `156d56d` | PASS | 9/9 requirements verified; 0 carry-over; 0 standing instructions |

## Keep

- Preserve the existing focused gates and their planted negative controls.
- Keep canonical text, site presentation, runtime support, and repository governance in separate authoritative homes.

## Change

- Treat GitHub Pages origin readiness and Cloudflare edge readiness as separate
  checks. `gh api repos/ssheleg/pod-manifesto/pages` proves the former;
  `python3 tools/check-live.py --verbose` proves the deployed surface.
- For GitHub's UI-only social preview setting, finish on the post-upload
  `Remove image` readback. A successful file chooser alone does not prove the
  repository setting persisted.

## Learned

- **Symptom:** the first social-preview upload could open the chooser but could not
  transfer the file. **Surfaced at:** post-deploy acceptance. **Owned by:** delivery
  preflight. **Root cause:** Chrome extension access to local file URLs was disabled.
  **Fix:** enable that permission before UI-only uploads. **Check:** after upload,
  GitHub Settings → Social preview must expose `Remove image`. **Commit:** `156d56d`.
- A single aggregate `validate` job is the stable branch-ruleset contract even when
  the underlying suite fans out into many named jobs; hosted run
  [`33055027335`](https://github.com/ssheleg/pod-manifesto/actions/runs/33055027335)
  proves the current contract.
