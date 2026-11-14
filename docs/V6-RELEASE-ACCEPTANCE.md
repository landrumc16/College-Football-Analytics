# V6 Release Acceptance and Evidence Checklist

## Governance
Planning branch v6-planning is documentation only. After owner accepts planning PR, Work creates v6-development from current main. All implementation stays off main until explicit owner merge approval. The incumbent model requires a separate promotion approval even if release approval is granted.

## Milestone evidence
- M1: actual usable observations in each required domain, source registry, immutable snapshots, lineage/checksums, missingness/coverage, identity and strict pre-cutoff tests; an empty registry is not completion.
- M2: separately labelled authentic pregame baseline and chronological paired replay research, frozen pre-test protocol and challenger comparison, all promotion gates and decision, truthful UI metrics; no multi-season archived-forecast claim from the 65-game V5 cohort.
- M3: sourced program drivers, reproducible calculations, cross-page parity, missing-data handling.
- M4: static-host-compatible scenarios, consistency, reproducibility, zero-override/reference parity under declared error limits, invalid/completed-game override rejection, declared numeric runtime/draw-count budget and measured mobile journeys.
- M5: summary-first home, favorites, navigation, deep links, accessibility and PWA.
- M6: all of the below on exact final commit.

## Final gate
1. Python/model/data and frontend tests pass, including V5 regressions.
2. Build succeeds; generated datasets reproducible from retained inputs.
3. Prediction evaluation provenance, no-leakage and promotion policy pass.
4. CFP simulations obey scenario constraints and probability sanity.
5. Browser journeys at 375/390/430/768/1536, actual screenshots inspected; no navigation or overflow regressions.
6. Favorites independent and persistent; search/autocomplete, rankings, polls, team pages, comparisons, predictions, playoff views and research work.
7. Android Chrome PWA installability, update/reload, actual offline fallback, no live JSON caching, stale-data and refresh recovery verified; identify emulation versus physical-device evidence. Preserve the released network-only freshness contract.
8. Release notes include coverage, limitations, new features, operational changes, exact SHA, workflow URLs, test counts, screenshot inventory and known issues.
9. PR has no unresolved material review comments or failing required checks; owner explicitly approves merge.
10. After merge, verify GitHub Pages deployment, live data freshness, routes and essential mobile journeys; record production SHA and URL.

## Blockers and reporting
A failed required gate blocks release. Missing optional data can be disclosed if agreed capability is still genuinely delivered; otherwise request a scope decision. Report deliverables and evidence, not percent complete or number of commits. No fabricated source, test or deployment claims. Stop at the explicitly required planning-approval, model-promotion or release-merge checkpoints, or a concrete external blocker requiring user action. Planning approval alone authorizes neither model promotion nor development merge.
