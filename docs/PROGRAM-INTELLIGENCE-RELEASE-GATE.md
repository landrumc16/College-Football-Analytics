# Program Intelligence redesign — implementation and release gate

Development branch: `program-intelligence-redesign` · PR #14 · production branch: `main`.

## Published analysis contracts

- **Current strength:** incumbent model ranking/rating and season record from `season-report.json`; no challenger promotion.
- **Recent form:** last five completed, scored games, ordered by published week. **Season trend** compares non-overlapping four-game windows and is published only after eight scored, non-tied games; a difference of at least two wins indicates changing short-term results, not a change in model strength or multi-season trajectory.
- **Forecast performance:** wins above tracked expectation only with at least three archived forecasted games. No retrospective estimates are substituted.
- **Playoff outlook:** incumbent published CFP field probability, not a separately validated contender label.
- **Quality wins:** wins against opponents ranked in the **current** model Top 25, not historical opponent rank at kickoff.
- **Historical direction:** displayed only from `v4-program-intelligence.json` after `isPublishedHistoricalIntelligence` provenance gate; no missing seasons are imputed.
- **Polls:** current AP and Coaches ranks are separate from preseason expectations; absent rank is displayed as unavailable rather than assumed to indicate a specific historical standing.
- **Shared calculations:** `web/src/programMetrics.ts` is consumed by both `ProgramIntelligence.tsx` and `TeamProfile.tsx`.

## Historical publication coverage 
 
The repository does not contain a committed `web/public/v4-program-intelligence.json` payload. The interface therefore keeps multi-season classifications gated and does not present them as established current evidence. Existing historical analysis code and tests are not a substitute for independently attested published source coverage. Current-season comparisons operate independently. The overview suppresses the historical-direction column entirely until a source-attested payload is published, rather than repeating missing values for every team. 
 
## Verification and remaining release gates

The branch has a dedicated V4 validation trigger running the existing Python suite, frozen-model checks, frontend build, Chromium journeys at 375/390/768/1536 widths, PWA checks, and screenshot artifact upload. Browser checks include actual current-season rows, team navigation, sorting, and mobile overflow. Check the **latest commit's** workflow status; prior successful workflows do not validate later changes.

Historical program coverage and source attestation must be established from actual published data before long-term classifications are represented as complete. Verify screenshots by inspecting the actual artifact; a screenshot upload alone is not visual approval. Validate the exact commit, update this record with results, and obtain explicit owner approval **before** merging into `main`.

Known CI dependency issue observed November 9: intermittent npm registry 404 for Rollup 4.68.2 and missing `@rollup/rollup-linux-x64-gnu` optional native dependency. These are distinct from product assertions; do not mark the frontend green until an actual build and Chromium run succeed.

## Final candidate release evidence — November 9, 2026

- **Exact tested SHA:** `1d4f2e8d861ab7d8321ab360ff966abda338aa3c`. This is the current head of PR #14.
- **All six workflows passed on that SHA:** V4 development validation [42701884703](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701884703), Python model tests [42701884815](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701884815) and [42701896873](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701896873), V3.4.2 validation [42701896979](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701896979), V3 research validation [42701897402](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701897402), and V3 historical model research [42701897487](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701897487).
- **Visual evidence:** Chromium screenshots from the V4 validation artifact were inspected at 390px mobile and 1536px desktop for Program Intelligence. Cards and values are readable; the current-season comparison no longer repeats an unpublished historical-direction column. Browser suite also covers 375px, 768px, PWA, search/filter/sorting, team navigation and parity.
- **Historical boundary:** No attested historical intelligence JSON is published. Consequently 3/5/10-year program trajectory and historical preseason-to-final hype are **not release features** in this candidate. Current-season comparisons remain independently usable. Historical research may be a future evidence-backed enhancement, not a fabricated present-day claim.
- **Prediction safety:** Incumbent production model remains authoritative; no challenger promotion is part of this redesign.
- **Release notes:** Program Intelligence consolidates current rankings, records, conference standings, quality wins against the current model Top 25, last-five results, eight-game form trends, tracked pregame forecast performance, current AP/Coaches rankings, and CFP odds, with conference filtering, school search, sorting, and Team Profile drill-through. Unverified historical classifications are suppressed.
- **Release control:** This evidence does not authorize merging. PR #14 must receive explicit owner approval before `main` or GitHub Pages changes.

