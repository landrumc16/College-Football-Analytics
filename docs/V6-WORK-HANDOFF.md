# V6 Work Execution Handoff

## Scope and authority
Owner approved the six-milestone V6 product direction on 2026-11-14. This branch contains the proposed formal plan; it does not authorize an unreviewed production merge or a challenger promotion. Read AGENTS.md, docs/V6-ROADMAP.md, docs/V6-DATA-RESEARCH-PLAN.md, docs/V6-MODEL-EVALUATION.md, docs/V6-PRODUCT-UX-CONTRACT.md and docs/V6-RELEASE-ACCEPTANCE.md.

## First Work pass
1. Planning review confirmed main `a8fff1f2c03b6d4577895617ac36da1b9840650b` includes PR #23 at `56abff306eb3f5f60f3356e01dcdacff68f1b4e9`, whose Pages/live five-width/PWA run 43598684277 passed. Main has a later CFBD data refresh; retain it. Recheck latest main before creating development.
2. Review this planning PR and report any concrete conflicts with existing architecture or data. Make only necessary plan corrections.
3. Present the corrected planning PR #24 for explicit approval. Only after approval, merge its documentation, create v6-development from latest main and begin implementation; do not implement on v6-planning.
4. Execute M1 as one complete data-foundation deliverable (registry, frozen evidence, transforms, tests and coverage). Then execute M2's distinct authentic-forecast and chronological replay lanes. Freeze eligibility, exactly four primary holdouts and numeric calibration/coverage tolerances before challenger testing. Existing recruiting research is not historically as-of verified; do not silently promote it to pregame input.
5. Continue through M3–M6 in substantial end-to-end passes, with evidence at milestone gates. Do not stop for routine decisions; stop for owner-only approvals, unavailable external rights/access, or genuine scope changes.

## Rules
No new top-level nav, no design reset, no fabricated or retrospectively mislabeled pregame data, no silent source gaps, no model promotion without separate owner approval, no production merge without owner approval. Preserve incumbent and V5 features. Use the definitive finished criteria, not activity reports.

The application is static React/Vite on GitHub Pages, with Python/Actions JSON generation. Reuse the current simulator, publication safeguards and browser/PWA journeys; do not assume a live simulation backend or add a router to satisfy existing in-app shortcuts.

## Work reporting contract
For each completed milestone give: exact SHA, user-visible deliverable, provenance and coverage, executed tests/browser evidence, and real blockers. Avoid repeated status-only responses. Before release request, consolidate all acceptance evidence on one tested SHA.
