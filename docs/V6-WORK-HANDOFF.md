# V6 Work Execution Handoff

## Scope and authority
Owner approved the six-milestone V6 product direction on 2026-11-14. This branch contains the proposed formal plan; it does not authorize an unreviewed production merge or a challenger promotion. Read AGENTS.md, docs/V6-ROADMAP.md, docs/V6-DATA-RESEARCH-PLAN.md, docs/V6-MODEL-EVALUATION.md, docs/V6-PRODUCT-UX-CONTRACT.md and docs/V6-RELEASE-ACCEPTANCE.md.

## First Work pass
1. Confirm the latest main branch includes the final V5 secondary-navigation fix; if it is pending, identify the dependency and do not overwrite it.
2. Review this planning PR and report any concrete conflicts with existing architecture or data. Make only necessary plan corrections.
3. After owner approval of planning PR, create v6-development from current main; do not implement on v6-planning.
4. Execute M1 as one complete data-foundation deliverable (registry, frozen evidence, transforms, tests and coverage). Then execute M2 incumbent baseline and challenger research with chronological validation.
5. Continue through M3–M6 in substantial end-to-end passes, with evidence at milestone gates. Do not stop for routine decisions; stop for owner-only approvals, unavailable external rights/access, or genuine scope changes.

## Rules
No new top-level nav, no design reset, no fabricated or retrospectively mislabeled pregame data, no silent source gaps, no model promotion without separate owner approval, no production merge without owner approval. Preserve incumbent and V5 features. Use the definitive finished criteria, not activity reports.

## Work reporting contract
For each completed milestone give: exact SHA, user-visible deliverable, provenance and coverage, executed tests/browser evidence, and real blockers. Avoid repeated status-only responses. Before release request, consolidate all acceptance evidence on one tested SHA.
