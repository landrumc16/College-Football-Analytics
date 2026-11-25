# Version 9 Release Candidate — Conditional Acceptance

The owner approved the current professional collegiate design. This pass closes implementation gaps without redesign. Engineering base: b2ee4bc8ec94b0becbdf34a19a9c965e3e48ee52. An exact final candidate is identified by the GitHub commit containing this document and its checks, not an untested future branch tip.

## Executive Decision

The candidate is ready for independent engineering review, **not authorization to deploy**. Offline implementation and statistical acceptance can be verified locally; browser, five-width, PWA lifecycle, accessibility/performance and physical-device acceptance remain open. The earlier browser auto-review denied entry to auth.openai.com absent explicit reauthentication authorization. No bypass, alternative authentication path or physical-device claim was used. The owner's visual approval is recorded separately from unperformed browser tests.

## Roadmap Acceptance

| Requirement | Implementation / Evidence | Acceptance |
| --- | --- | --- |
| Shared intelligence contracts, provenance, missing values | Existing M1 publisher/contracts and edge-case tests retained | Local acceptance passed |
| Accomplishment / strength / current level | Earned record only; validated existing rating and last-three function; new accomplishment rank withheld | Passed local |
| Opponent-adjusted units / schedule / four-game trends | Existing V8 calculations and explicit sample/window disclosures | Passed local; browser pending |
| Immutable authentic strength history | Content-addressed observations; no retrospective points | Passed local |
| Five destinations and approved design | Existing React components preserved; no new prototype | Owner design approved; viewport gates pending |
| Home briefing / rankings / team diagnostics / matchup | Existing M2 integration retained | Local tests/build passed; browser pending |
| Playoffs and scenario integrity | Existing simulator unchanged; exact report/packet pairing | Offline integration passed; actual interaction pending |
| Research consolidation | Authentic retained cohorts, verified publication subset and replay studies separately labelled; historical model comparison moved from Teams to Research | Implemented; browser pending |
| Authentic three-model archiving | Atomic first retention per game/model, timestamps before kickoff, source hashes, versions, immutable first-bundle receipt | Tested; future publication hooks prepared |
| Accuracy / calibration / identical-game comparison | Reuses v5_forecast_evaluation strict scorer; counts, empty-bin nulls and common-game cohort | Tested; insufficient settled dual data honestly suppressed |
| Historical reporting | Existing independent publication evidence and chronological studies retained | Reused; no invented historical predictions |
| Production reliability reconciliation | Main b204bd6 is a data-only refresh; PR #56 remains open/unmerged | No newly merged reliability code to reconcile; recheck before merge |
| Browser widths 375 / 390 / 430 / 768 / 1536 | Authentication blocked | All outstanding |
| Search / favorites / navigation / charts / dropdowns | Existing controls and unit checks; no new browser verification | Outstanding browser acceptance |
| Title Case | Full source audit plus acronym, school identity and paragraph checks | Local passed; visual check pending |
| Accessibility / performance / PWA | Semantic tables/labels/disclosures and existing assets preserved; artifact checks distinct from runtime behavior | Runtime acceptance pending |
| Physical Android / iPhone | No physical test performed | Outstanding |
| Production promotion | No merge, dispatch, purchase or production deployment | Requires explicit owner approval |

## Statistical Evidence and Boundaries

The existing legacy ledger supports 128 settled Official-model FBS forecasts after strict timestamp, source, identity, kickoff and final-score screening. This is generation-ledger evidence, not the independently verified 65-game publication subset; the two remain distinct. The new first-retention bundle contains 228 actual pregame observations across Official, Standard and Momentum. Standard and Momentum have zero settled retained forecasts, and the all-three common completed-game cohort is zero. Their accuracy, Brier, log loss and calibration are unavailable, never zero-filled. Future games must settle naturally; no historical replay can substitute.

Calibration uses the existing ten-bin home-win-probability evaluator with per-bin denominators. A 50% forecast is treated as choosing the home team for winner accuracy. Small bins are noisy. Identical games are necessary for comparison; differing information cutoffs/model versions still limit fairness. No superiority or promotion claim is made.

First observation files never overwrite issued values when later forecasts differ. Source reports and model versions remain traceable through receipt hashes and the capture base commit. Outcome corrections can change evaluation results while issued values remain frozen. The original mixed-evidence 2026 study is now explicit: only its Official probabilities were historically archived, while Standard/Momentum were retrospective pre-week calculations.

Official model code, strength calculations and simulator remain byte-identical to the base. Standard/Momentum and explanation publishers were rerun offline against retained November 25 inputs, yielding 71 upcoming games; formulas are unchanged. Explanation sums reproduce the current Official margins. Re-publishing on newer source data changes forecast values normally; it is not a model replacement. New published JSON files have exact reviewed guard pins.

## Publication and Freshness

The isolated V9 workflow retains new observations and uploads a real React build. The review builder never captures forecasts merely because someone builds a preview; it reads retained observations and evaluates them. Capture occurs explicitly in the retention command/approved candidate refresh hook.

Candidate-only refresh-data changes retain the unchanged models' newly issued values and strength snapshots before the existing data commit. Dual projections refresh through the existing offline publisher, with no additional CFBD calls. Candidate dashboard staging checks exact report identity and publishes V9 evidence; failure suppresses V9 packets with an honest unavailable state, without blocking core results. Watcher schedules, API calls and permissions are unchanged. None of these candidate hooks has run on main.

The private preview is a frozen review build, not an event-driven live service. Each source receipt remains visible. Projection source age is displayed; missing/older sources are not called fresh. Event-driven final scores and official poll requirements remain unchanged. Verify live post-merge freshness against actual event time, not merely build time.

## Release and Rollback Plan

1. Independent reviewer checks this exact candidate and all open gates in V9-CLAUDE-REVIEW.md. Recheck PR #56 and latest main; reconcile independently approved changes into V9 without copying unmerged reliability work. Retained data should be refreshed from approved main inputs and paired artifacts rebuilt before owner authorization.
2. Obtain explicit owner approval for the exact tested merge candidate. No automatic promotion from this document.
3. Merge only the authorized candidate. Existing main-only refresh/publication hooks then stage V9 evidence; verify generated artifacts, scenario/report identity, ledger retention and source freshness before calling release successful. Do not run extra acquisition to exercise tests.
4. Check five destinations, saved favorites, pregame cohorts, predictions, scenarios, service-worker update/offline recovery and independent freshness alerts. Do not compare static review timestamps with live freshness targets.
5. If acceptance fails, restore/redeploy the prior known-good Pages artifact first where supported. Otherwise revert the authorized V9 merge through a separately approved rollback PR. Preserve newest valid data, immutable prediction/strength archives and independent reliability fixes. Never delete evidence or force-reset main to erase history. Record exact deployment/rollback SHAs and incident cause.

## Remaining Release Blockers

Browser authentication and five-width functional/visual verification; runtime accessibility, performance and PWA lifecycle; physical-device testing; current-main/data reconciliation immediately before promotion; independent review of candidate workflow hooks; final owner approval. Quantified rooting advice, new accomplishment ranking and model promotion remain deliberately conditional and are not release promises.

Generated-data guard policy: exact published-JSON pins are validated against actual HEAD on v9-development. Main's ordinary post-release data refreshes must not be frozen to release-day JSON; guard-unit fixtures use the frozen reviewed hashes outside the release branch while still testing rejection of all unauthorized branches/forks/tampering. The guard implementation itself is unchanged. Snapshot regression now verifies the complete retained hash set rather than assuming history contains only one observation.

## Final Local Validation Receipt

Full Python regression: **836 passed, 1 skipped**, 27.18 seconds; one external anyio/pytest deprecation warning. Typography/render/prose tests: passed; 43 TS/TSX files and 592 static labels audited with zero inconsistencies. Strength tests: 8 cases with TypeScript/Python parity across 138 teams. V8 statistical helpers: 6 cases; freshness: 7 cases; model projection explanations: 7 cases; prediction explanations: 7 cases with every current Official margin reproduced across 71 games. TypeScript/Vite build and branded bundle verification pass. The actual source snapshot contains 697 eligible completed FBS games; 128 Official rows qualify, zero settled dual rows and zero all-three common games.

Static artifact checks verify exact scenario/report SHA-256 and receipt identity, PWA manifest/icon dimensions and shell presence, and unchanged model-code hashes. These checks do not establish browser accessibility, responsive fit, physical-device behavior, runtime performance or PWA lifecycle acceptance. Main JavaScript: approximately 402.5 KB raw / 122.1 KB gzip; CSS approximately 71.1 KB / 13.8 KB gzip. No Lighthouse or runtime performance result is claimed.

Updated private preview publication succeeded: hosted source ee0607151666bd7c00eee5b6871d54eb43ef0a34, deployment appgdep_6b075a5ec9fc8191b607b6f9ca45ae38. URL: https://college-football-v9-review.orderlykingfisher32.chatgpt.site/ . GitHub CI must be checked for the final exact candidate SHA; local evidence is not a claim that remote CI already ran.
