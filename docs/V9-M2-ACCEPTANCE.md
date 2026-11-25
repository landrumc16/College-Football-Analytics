# V9 Milestone 2 — implementation and acceptance

November 25, 2026. Base: 4f5df3df15578cc34eaa0e59d1bb3f7bcd1714ba.

## Implemented

- Actual React app, existing masthead, navy/gold editorial styles, statistical tiles, school search, independent saved favorites and model projections retained.
- Five primary destinations: Home, Rankings, Teams, Playoffs, Research. Market remains accessible within Research and existing game links.
- Home: first saved school's season/last-three briefing links to its canonical profile; existing favorite matchup, national, poll and postseason stories preserved.
- Rankings: named strength, current-level, adjusted offense/defense and schedule views. Earned records remain unranked; no unvalidated accomplishment score. Searchable school selection. Existing official ranking, conference views and polls preserved.
- Teams: source-backed three-perspective summary, unit evidence and explicit four/three-game windows, retained-observation chart and observation selector. Matchup context compares existing evidence without manufacturing a forecast. Historical program profiles and Official/Standard/Momentum remain available.
- Playoffs: existing simulations preserved; interpretation explains simplified selection and why quantified rooting advice remains withheld.
- Research: intelligence methodology and accountability caveats alongside existing forecast research; Market is a research tool.
- Offline review builder stages current repository report/polls/research plus the V9 contract and exact retained observations. Disables analytics; makes no CFBD calls. Development-only workflow uploads actual React review output, with no Pages publication or production schedule changes.

## Validation

- Full Python suite: 824 passed, 2 skipped before adding the review fixture. New representative-team/observation fixture: 1 passed separately.
- Foundation edge-case and evidence-path assertions passed.
- Strength tests: 8 cases, including exact TypeScript/Python parity across all 138 published FBS teams.
- Existing model-projection explanations: 7 cases, 131 published games.
- School search: 7 cases, every FBS full-name self-match.
- Existing takeaways: 4 cases; market calculator: 12 cases.
- TypeScript and Vite build passed: 77 modules, JS approximately 395 KB / 118.6 KB gzip; CSS 71.1 KB / 13.7 KB gzip. No dependency additions.
- Protected-path manifest pins exact navigation/home edits under owner-authorized V9 scope; statistical/model files remain byte-identical to base.

## Visual and interaction acceptance

Production homepage inspected in the actual cloud browser before edits. Existing serif masthead, gold rules, slate matchup panels, navigation icons and editorial grid are the design baseline. Source CSS was retained; additions extend existing profile classes. A live comparison is still required before visual acceptance. No screenshot is presented as proof of another viewport.

The local preview daemon reports loopback http://127.0.0.1:4173; that is not an Android-accessible URL. A separate owner-private review site is used for phone review, with public repository datasets only. It does not deploy or modify the GitHub Pages production application.

Review URL: https://college-football-v9-review.orderlykingfisher32.chatgpt.site/ (owner-private; frozen public repository data, analytics disabled).

The cloud browser reached the owner sign-in gate. Automatic approval review rejected Continue with ChatGPT at auth.openai.com because explicit reauthentication authorization was absent. No access controls were changed and no alternate browser path was attempted.

| Acceptance gate | Status |
| --- | --- |
| Production baseline | Observed before edits |
| Private review publication | Succeeded; browser interaction blocked by sign-in |
| Browser navigation, favorites, search, filters, charts, explanations | Pending access; unit evidence is separate |
| 375 / 390 / 430 / 768 / 1536 pixel comparison | All pending; no viewport checks claimed |
| Physical Android / PWA | Pending |
| Remote development workflow | Pending verification |

These gates are not inferred from passing unit tests.

## Handoff / readiness

Milestone 2 implementation is reviewable, but cannot be declared accepted while requested visual/interaction gates remain unverified. Milestone 3 can proceed with accountability work independently; release acceptance must wait. Accomplishment national ranking and quantified rooting advice remain conditional. Earlier snapshots are unavailable; no trajectory is inferred from one point. Source freshness labels describe the build-time age and expose actual receipts; review hosting is frozen evidence rather than a live refresh service.

Remote baseline investigation: the M1 foundation workflow passed (45700559659), while its general pytest job failed (45700559620). The general job installed Python only despite M1 publication tests requiring frontend esbuild. Added the existing Node/frontend dependency installation to that job; tests are not skipped or relaxed. Current remote runs must be checked after this harness correction.

Final regression correction: updated the legacy V7-only manifest inventory/current-navigation assertions for the separately owner-authorized V9 manifest. Added explicit rejection checks for main, forks, reliability branch, model/data edits and tampered hashes. The guard implementation and old V7 fixture are unchanged. The initial pre-commit suite did not exercise committed V9 pin changes; final post-commit suite is the acceptance result.

Final local acceptance after guard/harness corrections: **825 passed, 2 skipped**, 22.73 seconds. One external anyio/pytest deprecation warning. Development publication run [45703267216](https://github.com/landrumc16/College-Football-Analytics/actions/runs/45703267216) succeeded for implementation commit f6972043c57aa8664f5e35528531c89b06086f40. General CI for that commit failed before the documented harness/legacy-assertion corrections; final correction commit must pass remote CI separately.

## Owner Typography and Scenario Acceptance Correction

This is part of the existing Milestone 2 acceptance pass, not a new milestone. Base: 56a005748d787a14f6c97829e18fe70e0b4c95e0.

Audited all 42 TypeScript/React source files and 567 static interface labels. Corrected headings, buttons, dropdowns, metric labels, disclosures and source-supplied labels across all five destinations. The shared presentation-only formatter preserves acronyms and all 138 published school names; it handles minor words and hyphenated principal words. Removed uppercase CSS transforms from table headers and model/factor labels so rendered casing follows source labels. Existing paragraph text is protected by an acceptance receipt, independent of Git history depth. Editorial prose, numerical values, IDs, analytic events, school identities, model formulas and source datasets are unchanged. Browser selector fixtures were updated only for visible multiword labels; no browser execution is claimed.

Repeatable checks: `node scripts/audit_ui_titles.mjs --check` and `node tests/v9-typography.mjs`. Initial source findings are retained in evidence/v9/title-case-audit.json. Paragraph receipt: evidence/v9/sentence-case-prose.json.

The screenshot's scenario error was genuine integrity protection: the review report was dated November 25, while the copied public scenario packet was dated November 14, with different report SHA-256 values. The production dashboard workflow already stages/checks its paired packet; the isolated V9 review builder had omitted that step. The V9 builder now regenerates the scenario packet through the existing `scenario_input` adapter and hashes the exact report bytes staged alongside it. The client hash/timestamp/schema checks remain intact, as do the simulation scale, home edge, seed, draw count and all statistical formulas. No production publisher, refresh schedule, source archive or public scenario artifact was edited.

Four new tests verify exact adapter parity, byte-correction hashing, rejection of game-identity mismatches, and the complete review build's report/scenario pairing while checking protected source bytes remain unchanged. Scenario correctness is verified offline; actual Playoffs browser interaction remains gated by the previously documented owner sign-in restriction. All requested viewport and physical-device gates remain open.

Final correction validation: **829 Python tests passed, 2 skipped** (27.62 seconds; existing external anyio/pytest deprecation warning). Typography unit/render checks and the 567-label audit pass; TypeScript/Vite review build passes (78 modules). Published private review source ec43a7a5792c2ab23ca366cf2a845cb62feb28c0, deployment appgdep_6b0755624d188191b9bee4844bc7867e succeeded at the existing preview URL. Browser/device gates remain unverified. GitHub CI for the final correction commit is a separate recorded check.
