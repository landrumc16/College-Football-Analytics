# V6 Release Acceptance and Evidence Checklist

## Governance
Planning branch v6-planning is documentation only. After owner accepts planning PR, Work creates v6-development from current main. All implementation stays off main until explicit owner merge approval. The incumbent model requires a separate promotion approval even if release approval is granted.

## Milestone evidence
- M1: source registry, immutable snapshots, lineage/checksums, missingness/coverage, identity and time-cutoff tests.
- M2: genuine pregame baseline, chronological evaluation, frozen challenger comparison, all promotion gates and decision, truthful UI metrics.
- M3: sourced program drivers, reproducible calculations, cross-page parity, missing-data handling.
- M4: scenario consistency, reproducibility, baseline-vs-override, input validation, runtime and mobile journeys.
- M5: summary-first home, favorites, navigation, deep links, accessibility and PWA.
- M6: all of the below on exact final commit.

## Final gate
1. Python/model/data and frontend tests pass, including V5 regressions.
2. Build succeeds; generated datasets reproducible from retained inputs.
3. Prediction evaluation provenance, no-leakage and promotion policy pass.
4. CFP simulations obey scenario constraints and probability sanity.
5. Browser journeys at 375/390/430/768/1536, actual screenshots inspected; no navigation or overflow regressions.
6. Favorites independent and persistent; search/autocomplete, rankings, polls, team pages, comparisons, predictions, playoff views and research work.
7. Android PWA install, update, offline, stale-data and refresh behavior verified.
8. Release notes include coverage, limitations, new features, operational changes, exact SHA, workflow URLs, test counts, screenshot inventory and known issues.
9. PR has no unresolved material review comments or failing required checks; owner explicitly approves merge.
10. After merge, verify GitHub Pages deployment, live data freshness, routes and essential mobile journeys; record production SHA and URL.

## Blockers and reporting
A failed required gate blocks release. Missing optional data can be disclosed if agreed capability is still genuinely delivered; otherwise request a scope decision. Report deliverables and evidence, not percent complete or number of commits. No fabricated source, test or deployment claims. Stop only at release-ready approval checkpoint or a concrete external blocker requiring user action.
