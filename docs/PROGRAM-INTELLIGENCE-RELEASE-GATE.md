# Program Intelligence redesign — implementation and release gate

Development branch: `program-intelligence-redesign` · PR #14 · production branch: `main`.

## Published analysis contracts

- **Current strength:** incumbent model ranking/rating and season record from `season-report.json`; no challenger promotion.
- **Recent form:** last five completed, scored games, ordered by published week. **Season trend** compares non-overlapping five-game windows and is published only after ten scored, non-tied games; a difference of at least two wins indicates changing short-term results, not a change in model strength or multi-season trajectory.
- **Forecast performance:** wins above tracked expectation only with at least three archived forecasted games. No retrospective estimates are substituted.
- **Playoff outlook:** incumbent published CFP field probability, not a separately validated contender label.
- **Quality wins:** wins against opponents ranked in the **current** model Top 25, not historical opponent rank at kickoff.
- **Historical direction:** displayed only from `v4-program-intelligence.json` after `isPublishedHistoricalIntelligence` provenance gate; no missing seasons are imputed.
- **Polls:** current AP and Coaches ranks are separate from preseason expectations; absent rank is displayed as unavailable rather than assumed to indicate a specific historical standing.
- **Shared calculations:** `web/src/programMetrics.ts` is consumed by both `ProgramIntelligence.tsx` and `TeamProfile.tsx`.

## Historical publication coverage\n\nThe repository does not contain a committed `web/public/v4-program-intelligence.json` payload. The interface therefore keeps multi-season classifications gated and does not present them as established current evidence. Existing historical analysis code and tests are not a substitute for independently attested published source coverage. Current-season comparisons operate independently.\n\n## Verification and remaining release gates

The branch has a dedicated V4 validation trigger running the existing Python suite, frozen-model checks, frontend build, Chromium journeys at 375/390/768/1536 widths, PWA checks, and screenshot artifact upload. Browser checks include actual current-season rows, team navigation, sorting, and mobile overflow. Check the **latest commit's** workflow status; prior successful workflows do not validate later changes.

Historical program coverage and source attestation must be established from actual published data before long-term classifications are represented as complete. Verify screenshots by inspecting the actual artifact; a screenshot upload alone is not visual approval. Validate the exact commit, update this record with results, and obtain explicit owner approval **before** merging into `main`.

Known CI dependency issue observed November 9: intermittent npm registry 404 for Rollup 4.68.2 and missing `@rollup/rollup-linux-x64-gnu` optional native dependency. These are distinct from product assertions; do not mark the frontend green until an actual build and Chromium run succeed.
