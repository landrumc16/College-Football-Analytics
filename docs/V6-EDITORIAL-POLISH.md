# Version 6 — visual and editorial refinement

**Status: RELEASED AND CLOSED — November 14, 2026 (America/Chicago).**

The owner approved PR #26 after visual review, conditional on passing checks.
All required checks passed at `2c0bc1b50733272a1d5b76b755b652f1083c97e3`.
The approved refinement merged and deployed as
`195fbd143df002b733a4f36e6030b5677a9f19d4`. Production acceptance passed;
see [final acceptance](V6-PRODUCTION-ACCEPTANCE.md) and its retained receipt.

Review branch: `v6-editorial-polish`, originally based on released main
`70191e42df15f932733843df801a54de04847319`. This is a focused V6 refinement,
not a new version.

The reviewed V6 pages overuse nested framed panels and give routine statistics,
important findings and methodological notes similar visual weight. Compare puts
historical material ahead of its matchup answer; research leads with technical
provenance paragraphs. This pass uses the existing crest, navy/gold palette,
Georgia headlines, navigation and page structure to establish clearer priorities.

## Delivered presentation changes

- Home keeps all five previews and the same selected games, favorites and links.
  A gold-ruled lead matchup, quieter supporting fixtures, more deliberate serif
  hierarchy and distinct spotlight treatment replace uniform boxed presentation.
- Team Profile uses a compact school-picker row and a ruled overview stat line.
  Recent form is concise; exact form/forecast definitions remain in a native
  disclosure. No statistic or unavailable state is removed.
- Shared program intelligence uses short observations and legible values,
  including `pp` explicitly defined as percentage points. Source periods,
  missingness, cohort coverage and non-causal/roster/coaching limitations remain
  accessible in the same component on every page.
- Research leads with correct winners and the actual verified sample, while
  showing the small-sample/coverage limit immediately. Full error scores,
  confidence segments, source publication, calibration, uncertainty and gates
  remain available. Broader tracked-season results remain separate from the
  independently checked subset. No accuracy improvement is claimed.
- Compare presents the existing model answer immediately after school/venue
  selection. Full historical results and Report Cards remain in one clearly
  labelled native disclosure; current metrics and program context are preserved.
- Rankings use tighter rows and clearer rank typography. Scenarios use plain
  matchup/pick labels and a concise result status; timing/seed/uncertainty remain
  in the explanation. Scenario probabilities and constraints are unchanged.

## Verification and visual review

The existing full Python, build, mobile/desktop and Android PWA regression suites
remain required. Updated test expectations follow wording/disclosure changes;
all existing numeric/provenance/persistence/navigation assertions are retained.

The additional browser capture builds the released `web/src` and refined
`web/src` against exactly the same real publication bytes. It captures Home,
Rankings, Profile, program intelligence, Compare, Research and selected playoff
scenarios at 375/390/430/768/1536 px. It checks exact before/after data hashes,
visible numeric outputs, favorite slots, model matchup probabilities, scoring
and research tables, tracked ledger and deterministic scenario results/reset.
It also verifies the retained history, source and scoring disclosures open.

A source guard rejects changes to Python analytics, data/archive files, scenario
computation, navigation, logo/publication/PWA assets and dependencies. No new
runtime dependency is introduced. Final tested SHA, executed results, inspected
before/after screenshots and remaining limitations are recorded in the PR.
