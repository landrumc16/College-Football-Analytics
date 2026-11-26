# Version 9 — Production Acceptance and Closeout

Version 9 is released and formally closed on November 26, 2026. The owner approved PR #63 at `7c29544764643689753c695fa332329a9154c8c7`. It merged as `283677f44915120d505beeedee29a71d3efe795f`. Production acceptance passed on `0cf736108d39b7d612c6a370c782d6a66a83c411`, including the narrow test correction described below.

Production: https://landrumc16.github.io/College-Football-Analytics/

Successful deployment and live acceptance: https://github.com/landrumc16/College-Football-Analytics/actions/runs/45891686912

## Roadmap Acceptance

| Milestone | Finished Evidence | Status |
| --- | --- | --- |
| M1 — Intelligence Foundation | Shared metric contracts; reused strength and last-three calculations; four-game unit trends with sample disclosures; earned record without unvalidated accomplishment ranks; opponent/schedule context; honest missing values; immutable snapshot retention and provenance | Closed |
| M2 — Complete Fan Experience | Approved React interface and five destinations; personalized favorite briefing; national intelligence; team diagnosis/trajectory/matchup; original models; postseason interpretation; Research/Market consolidation | Closed |
| M3 — Accountability and Release | Authentic pregame retention, strict scoring/calibration/common-game cohorts, guarded publication, independent acceptance, full regression, actual live five-width journeys, PWA and analytics verification, owner approval and deployment | Closed |

Conditional accomplishment rankings, quantified rooting guides and model promotion remain excluded. Their validation requirements are not waived. No Version 10 or new design cycle is authorized.

## Release and Test Evidence

- Approved exact-head PR CI: **17 successful checks, 2 expected gated skips**, including privacy/browser budget, visual comparison and WebKit/Chromium device profiles. See PR #63 for linked runs and independent acceptance records.
- The normal main data refresh immediately before merge was preserved. The subsequent refresh completed successfully as run **45891224744**, retained a new authentic strength observation, and committed `efeb35aade7600f8918223bc64b641e64b612fe3`. It did not modify formulas or the approved interface.
- Initial release builds failed safely **before deployment** at the ranking-search smoke assertion. The test selected every table, including V9's independent intelligence table. The fix at `0cf7361` scopes it to `.rankings-table`; it retains the nonempty and correct-result assertions. No application or prediction code changed. A local attempt also needed the historical-backtest fixture normally supplied by dashboard.yml; it was generated offline before the successful full run.
- Full merged-tree Python regression: **839 passed, 2 skipped** locally and in production CI. Final targeted archive/guard/reliability tests: **51 passed**. Real React build passes.
- Local complete-packet browser regression: 375/390/430/768/1536 plus Android Chrome-emulated installability/update/offline/recovery pass.
- Actual production supplemental Chromium/touch journeys: **all five widths**, all five destinations, zero horizontal overflow and zero page errors. Favorites persist independently of browsing, intelligence ranking filter/search, genuine trajectory points, matchup selections, Momentum projections, offense/defense, calibration and Research Market all pass. TCU-over-Texas-Tech scenario changed the displayed Texas Tech field estimate from 98.1% to 91.1%; reset restored the exact baseline. This is a scenario test, not validated quantified rooting advice.
- Permanent deployment workflow independently passes published data checks, live desktop/mobile/PWA journeys, controlled analytics and keeper. Its browser source and artifact links remain in GitHub. No manual owner testing was required.
- Workspace-only live Chromium initially lacked the network proxy and its already-provided trust certificate. Those environment settings were configured for testing; no TLS validation bypass was used and production was unchanged.

Machine-readable evidence: `evidence/v9/release/production-acceptance-2026-11-26.json` and `production-five-width-journeys.json`. Supplemental live journeys reuse the existing device-profile selectors with five requested Chromium viewports, the production URL and data-independent numeric assertions. No new production test service or external AI was introduced.

## Models, Archives and Data

All `src` and `web/src` files, device-profile test and device workflow remain byte-identical to the approved V9 candidate. Official, Standard, Momentum and Monte Carlo calculations are unchanged. The permanent test infrastructure is preserved; only the erroneous smoke-test selector changed.

Prior `research/archive`, immutable pregame files and historical evidence were not overwritten or deleted. There are **240 retained pregame files** and **3 committed retained strength observations** at acceptance. The deployed packet includes those observations and its current report observation; it is not a reconstructed weekly history. Report-generation and retention timestamps remain separate. Existing first-bundle hashes and guard tests pass.

Live report/scenario identity: `5e2cea2c53c2d91f468c1552e494193dcd6f23474ebdbc7d73121a2bcfe76f81`. Live intelligence covers **138 schools**; dual projections cover **71 games** and use the November 26 20:28 UTC source receipt. Source age is distinct from build time. Unit statistics still use November 22 18:02 UTC and are explicitly stale. The verified CFP snapshot is week 13, publication date November 24; AP/Coaches source receipt remains November 22. No unnecessary acquisition was dispatched for acceptance.

Accountability keeps **128 eligible existing-generation Official rows** separate from independently verified publication evidence and the new first-retention archive. There are no settled all-three common games at acceptance. Missing Standard/Momentum performance remains unavailable; no superiority or retrospective-authenticity claim is made.

The JavaScript comparison retains the **10,240-byte** growth allowance and assertion. Its approved privacy/browser CI passes. Independent same-environment local comparison remains +7,718 gzip bytes over current production frontend baseline; the release test fix adds no JavaScript. All protected-path, exact-manifest, privacy and fork safeguards remain intact.

## Analytics, Runtime and Operational Boundaries

The actual deployment's controlled production PostHog delivery check passes. Read-only project 737110 queries after 20:34 UTC observed 3 controlled test visits and 27 controlled test page views; test traffic remains excluded from beta behavior reporting. Non-test `cfa_application_error` and `$exception` counts were both zero in the short partial observation through approximately 20:38 UTC. This is an initial release observation subject to ingestion latency, not a guarantee about future traffic or human usability.

PR #56's freshness correction remains present. Keeper reports an existing watcher running or queued and preserves warnings it cannot independently assess. Existing quota and GitHub scheduling warnings are operational constraints, not concealed as fresh data. A build-time monitor packet can briefly retain the prior deployment-failure alert until the normal monitor observes success and republishes the critical-alert change; the successful release run is the deployment authority. No watcher was canceled, refresh schedule changed or extra acquisition dispatched by acceptance.

Physical Android/iPhone hardware was not tested. Cross-browser/device results are emulation. The headless Linux WebKit offline/update crash limitation remains owner-accepted. Previously documented baseline accessibility limitations and sparse historical/dual-model evidence remain documented; no new acceptance blocker was found. Existing runtime accessibility/performance evidence is reused because the approved interface is unchanged.

## Retained Operations and Recovery

The successful run retains live-browser artifact **15152007134** (through December 26), controlled analytics artifact **15152091830** (through February 24), and Pages artifact **15151109291** (default expiry November 27). Artifact digests are exposed by GitHub; the Pages digest is `sha256:08164ae81f645277a7d61050f38c09a12e86797eac078c4edcf48cef8150955b`.

The pre-V9 post-PR56 known-good SHA is `79a3b1bf42236a852caf11b15c78b12b5a636a7e`. If a genuine later incident requires recovery, restore an available known-good artifact through an approved deployment or prepare a targeted rollback PR. Preserve PR56, newest valid data and immutable archives. Never force-reset main or erase issued evidence. No rollback was needed: the false-positive gate prevented initial publication, and corrected production acceptance passed.

All three milestones and V9 release acceptance are closed. Normal scheduled/event-driven maintenance and error monitoring continue. This closeout authorizes no additional product development.
