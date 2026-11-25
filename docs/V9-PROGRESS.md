# V9 execution state — November 25, 2026

## Baseline and authority

Main inspected at 13fb09a924e7906aa6db474fc291a8544e1da3a0. Authenticated GitHub identity landrumc16 has admin permission. Full local clone, Python/Node dependencies and build environment work. AGENTS.md read in full. Open PRs are 56 (active freshness fix), 37 (research), 35 (release guard cleanup), 32 (older market plan). Their branches were not modified.

## Owner feedback and reuse

The owner rejected cheap/minimal/crowded standalone HTML previews. Use the actual application and existing components for all previews. Research/product-definition artifacts informed docs/V9-ROADMAP.md. Reuse EditorialHome.tsx, TeamProfile.tsx, OffenseDefense.tsx, ModelProjections.tsx, strengthScores.ts, v8_stats.py, forecast_ledger.py and existing archives. Published model rank combines projected wins and rating and must not be relabeled rating-only strength rank.

## Completed pass

- Isolated v9-development from the inspected main baseline.
- Definitive three-milestone roadmap.
- Offline immutable strength-report observation command scripts/v9_strength_snapshot.py. Example invocation uses --report data/season-2026-report.json --archive an isolated archive directory --source-commit the exact baseline SHA.
- Source SHA256, exact source commit, source receipt, report generation time and retention time are retained separately. Snapshot records are retained observations, not proof of original public availability.
- Atomic complete-file publication through same-filesystem hard link and idempotent retries.

## Actual verification

- Baseline python -m pytest -q: 820 passed, 2 skipped.
- New snapshot tests: 2 passed.
- npm run build in web: successful TypeScript and Vite build.
- Offline command against real report: successful, 138 teams.
- Frontend output unchanged by this pass. No API calls or workflow dispatches.

## Outstanding

No UI integration, source-contract registry, new accomplishment metric, publication-pipeline integration or historic backfill is complete. No five-width browser, visual baseline, PWA or physical-device evidence was collected in this pass. A normal Android-accessible isolated preview remains to be established using the actual web build. Prior session's cloud browser could not access local preview and rejected embedded URLs. Use an authorized actual-app preview host rather than another standalone prototype or any security-policy workaround.

Next pass should validate snapshot schema and corruption behavior more fully, integrate retention into an isolated offline build path, then implement the shared intelligence contract using existing functions. Keep actual publication time unknown unless independently evidenced. Reconcile PR56 only after its independent merge. Inspect protected-change guards before any protected path edit. Run targeted tests and relevant regression checks. Publish preview separately from production with analytics disabled. Do not treat retained report observation as historical pregame forecast evidence.

No owner decision blocks these routine steps. New accomplishment rankings, engine promotion and quantified rooting retain their validation gates. V9 merging requires explicit owner approval.

## Foundation publication pass

Added scripts/v9_intelligence.mjs. It bundles and calls the actual released strengthScores.ts, packages all 138 teams, retained record accomplishment, season strength, current three-game level, V8 adjusted units, four-game-requested trends with actual fallback window, schedule context, consistency and source metadata. New accomplishment national metric remains null. Retained snapshot history is integrated into an isolated offline publisher.

Added V9-only read-only-permission artifact workflow. It uses committed source files and no CFBD requests, schedules, Pages deployment or production secrets. It publishes the retained observation and shared intelligence JSON as an artifact. Workflow execution is not yet verified.

Verification: full Python suite 823 passed, 2 skipped. Targeted publication test passes with identical Official report and dual-projection hashes before/after and exact season-rating equality across 138 teams. Contract cases pass for missing stats, thin sample, duplicate teams and nonfinite rating. TypeScript/Vite build passes, same generated frontend asset names as baseline. No new forecast model or statistical improvement claim.

Acceptance remaining: source-age assessment is explicitly delegated to the consumer and lacks tested stale/future-time classification. Findings currently contain the season-strength statement with traceable evidence, while richer unit/schedule/current-level explanation rules remain to implement. Schema validation is partial, including consistency sample metadata. Thus Milestone 1 is not closed. These are engineering tasks, not an environment blocker. Continue them before Milestone 2 integration. Browser baselines remain unavailable in this pass and prior environment browser restrictions still apply. No actual-app external preview has been established.

Next targeted pass: complete field-level period/sample/uncertainty contracts, validate missing/future/stale timestamps, generate supported unit/current/schedule findings and test contradiction/rounding behavior. Add TypeScript consumer contract, independent all-team parity against existing unit fixture and archive corruption/schema tests. Verify isolated workflow artifact without touching production. Milestone acceptance requires those outcomes, not merely the new publisher.

## Milestone 1 acceptance — final foundation pass

Completed shared metric/finding contracts including a TypeScript consumer contract. Metric wrappers retain units, population, sample, period, source receipt, limitations and availability. Source-age classification tests cover missing, invalid, timezone-less, future, stale and current timestamps. The 24-hour default is an explicit configurable descriptive age threshold, not a claim of achieved event-driven freshness.

Added deterministic earned-record, current-level, adjusted-unit and schedule findings. Evidence paths resolve across all 138 published teams. Missing unit values suppress unit findings. Period-specific wording avoids a season/recent contradiction. No inferred personnel or causal claims. Existing production strength function is bundled directly. Four-game trend metadata preserves actual three-game fallback. Accomplishment remains actual earned record; unvalidated national metric stays unavailable.

Durable initial report observation retained in docs/evidence/v9/strength-history. Each future V9-only publication restores the retained history, archives the current report and commits new observations only to v9-development. Source bytes identify the observation. Repeated source bytes preserve the first retention/source commit. Tampered stored team values are rejected. Publication time stays unknown. Artifact retention alone is not relied upon for permanent history.

Snapshot and team-intelligence publication both ran successfully offline. Final targeted Python tests passed (4). Node missing-data/freshness/evidence cases passed. Full suite passed 824 with 2 skipped before the final retention wiring adjustment; targeted publication/archive tests reran after that adjustment. TypeScript/Vite build passed with unchanged frontend asset names. Official and dual source-artifact hashes preserved in publication regression tests. All-team season ratings equal source report values exactly. No predictive improvement or new statistical inference is claimed.

Milestone 1 data-foundation acceptance is satisfied locally. Remote workflow execution remains to be observed after commit. Browser visual baselines remain unavailable, with no new browser/physical-device pass claimed. The UI is unchanged. Milestone 2 may begin with the existing components while remote CI and preview-environment checks remain explicit release gates. No production workflows were dispatched or production API calls made.

## Milestone 2 implementation — November 25

Resumed from remote 4f5df3df15578cc34eaa0e59d1bb3f7bcd1714ba. Integrated foundation into real EditorialHome, TeamProfile, matchup, rankings and research. Research replaces Market in the five primary destinations; Market remains a Research section with existing links. All model functions and issued projections remain unchanged. Existing strength-ranking/blended-score panel is retained in a collapsed disclosure.

See V9-M2-ACCEPTANCE.md for the implementation checklist, evidence and honest pending gates. Review build: `node scripts/v9_preview.mjs`; artifacts in web/dist contain repository season report, polls, research, V9 metrics and retained observations, with analytics disabled. No CFBD quota or production workflows used. Development workflow now builds/uploads review artifacts; it does not publish GitHub Pages.

Private preview: https://college-football-v9-review.orderlykingfisher32.chatgpt.site/ . Publication succeeded. Cloud browser reached owner login; auto-review rejected reauthentication to auth.openai.com absent explicit authorization. Do not work around the gate. Five requested viewport checks and all actual new-UI interactions remain unverified, as does physical-device acceptance. Browser inspection of production before edits established the visual baseline; matching stylesheet/source reuse is not visual acceptance.

Validation: full Python 824 passed/2 skipped, added review fixture 1 passed; foundation contract edge cases passed; strength 8 cases with 138-team Python parity; projections 7 cases/131 real games; school search 7; takeaways 4; market calculator 12. React build passed with no dependency additions. New review fixture checks Texas Tech, Georgia, Baylor, Notre Dame and Boise State against report and retained observation identity. Artifact hashes: evidence/v9/m2-review-build.json.

Next: complete browser authentication with explicit authorization, run five-width journeys and compare against production; physical Android owner check separate. Then begin M3 authentic pregame accountability/calibration and release gates, retaining the existing models. M2 is implemented for review, not fully accepted. PR56/main/watchers/schedules remain independent and untouched.

Remote publication confirmed implementation commit f6972043c57aa8664f5e35528531c89b06086f40. General CI baseline 45700559620 failed in pytest while foundation 45700559659 passed. tests.yml omitted Node/frontend installation required by the existing M1 publisher test. Added setup-node and npm installation to the pytest job without skipping tests. Final preview assets match evidence/v9/m2-review-build.json; hosted source commit 52d8468bd295de38a2595f51aa4bae6b88099e26, private deployment appgdep_6b0750cffdb08191aec3e92748a8309b succeeded.

Final local suite after scoped guard/harness corrections: 825 passed, 2 skipped in 22.73 seconds. Remote development publication 45703267216 succeeded for f6972043c57aa8664f5e35528531c89b06086f40. General CI for f697 failed on the now-corrected dependency setup/legacy guard expectations; verify the follow-up commit remotely. Browser auth, five-width interaction/visual acceptance and physical devices remain open.

## Existing M2 Acceptance — Owner Typography and Scenario Correction

Resumed from 56a005748d787a14f6c97829e18fe70e0b4c95e0. Application-wide Title Case audit: all 42 TS/TSX source files, 567 static labels, plus dynamic/source-supplied labels. Formatter and CSS fixes apply only to presentation. Retained navy/gold, layout, typography families, numeric values and models. Paragraph-content hashes and 138-school identity checks pass. Updated exact protected navigation/home pins under the owner's explicit typography instruction. Browser selector wording follows new visible labels; actual execution remains unverified.

Root cause of screenshot error: isolated review build mixed November 25 report bytes (f9819610f47e61414ebecbb2022763bfcc9df82bfaded6b9098cc49598101ed7) with November 14 public scenario packet tied to e3081c8eb516d471ffaef8a1e3deae789e858b1de07e5c2d478984c9a0780a8c. Added offline scripts/v9_scenario_packet.py using the unchanged released adapter; V9 builder stages the paired packet with the exact report. Client integrity check remains unchanged. Production workflow already handles paired publication and was not modified.

Targeted scenario tests: 4 passed, including a full React review build. Typography convention/identity/prose/disclosure checks pass. Existing strength, model-projection explanations, prediction-explanation sums, statistical takeaways, V8 statistics, search and market unit checks pass. No CFBD calls, subscriptions or production deployment. Owner-private preview is refreshed at its existing URL after packaging. Browser reauthentication, all five viewports and physical devices remain outstanding; do not bypass the previously rejected authentication action.

Correction acceptance: final local suite 829 passed, 2 skipped (27.62s); typography/render/prose/identity checks pass, source audit reports zero inconsistent labels, React build passes. Private review publication succeeded: source ec43a7a5792c2ab23ca366cf2a845cb62feb28c0; deployment appgdep_6b0755624d188191b9bee4844bc7867e. Preview includes the corrected paired scenario packet. Preserve open browser-auth/viewport/device gates and verify final GitHub CI separately.
