# Public beta readiness — verified and closed

**GO for an initial beta with 25–50 Texas Tech football fans.**
Verified and formally closed November 14, 2026 (America/Chicago).

Live application: https://landrumc16.github.io/College-Football-Analytics/

Deployed and production-tested commit:
`2c47bec5935fd32844ef20c307e3aab4c201d052`.

## Approved correction and live verification

The owner approved PR #28 at
`3b41d327c9a713f00113f720cd598f39c58d7653`; all required checks were passing.
The merged change updates only the official CFP comparison snapshot and its
publication receipt. All 25 November 10, 2026 positions, CFP week 11, source and
date match the reviewed official release. Direct browser inspection verified
all 25 rendered positions, including Texas Tech #12. Model rankings remain
separate; Texas Tech's model rank is #11 in this checked snapshot.

| Acceptance | Result |
| --- | --- |
| GitHub Pages build, deploy and anonymous HTTPS access | Passed |
| Full Python regressions / TypeScript and production Vite build | 549 passed / passed |
| Actual production browser journeys | Passed at 375, 390, 430, 768 and 1536px |
| Navigation, search, favorite persistence/isolation, Profile sections, history, comparisons and predictions | Passed |
| Android Chrome-emulated PWA install/update/offline/recovery | Passed; not a physical-device claim |
| Live report/scenario packet identity and timestamps | Exact byte identity; timestamps correctly retained |
| Model rankings, predictions, schedules, CFP simulations and model metadata | Exact canonical SHA-256 matches to the prior deployed release |
| Concrete app/source/feedback links | 48 checked, all HTTP 200 |
| Existing production runtime dependency audit | Zero reported vulnerabilities |

The game-data snapshot remains November 14 at **2:23:05 p.m. Central**, as
correctly shown by the application. It was 2.44 hours old at the 4:49 p.m.
verification. Publishing a poll correction does not falsely advance the game
retrieval timestamp. AP/Coaches remain week 11; the separately dated official
CFP snapshot is November 10. The app provides snapshot forecasts, not a live
score ticker. Routine refreshes may later advance these values.

No application code, navigation, branding, prediction engine, statistical
calculation, simulation logic, historical archive, favorites storage or PWA
contract changed. The incumbent remains authoritative; the experimental
challenger remains unpromoted. Version 6 remains closed.

## Evidence

- [Merged correction PR #28](https://github.com/landrumc16/College-Football-Analytics/pull/28).
- [Successful production build, deployment and live browser/PWA acceptance](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43649840894).
- [Exact 25-position, freshness, link and numeric-preservation audit](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43649997557).
- [Machine-readable final receipt](evidence/public-beta-ready-2026-11-14.json).
- [Retained primary-source CFP publication receipt](evidence/beta-cfp-publication-2026-11-10.json).

Both live evidence ZIP hashes and their deployed-source SHA receipts were
verified. Live screenshots at all five widths were inspected. Source review
also confirms that the previous release's application, engine and PWA code
are unchanged. The evidence-only audit branch does not deploy application code.

The earlier focused security review found no known-format credentials in 1,609
locally fetched reachable Git blobs or deployed files, no private source-cache
exposure, and no shared user database or analytics submission in reviewed app
code. This was scoped static/dependency/public-path verification, not a
penetration-test certification. Public aggregate research and provenance are
intentional. Favorites are independent between browser profiles; people sharing
a profile share that profile's local favorites. Hosting/network logs remain
possible, as disclosed in the existing About & privacy information.

## Beta feedback and scope

Use [feedback issue #27](https://github.com/landrumc16/College-Football-Analytics/issues/27),
which remains open. The app already links its issue form under Menu → About &
privacy. Fans without GitHub accounts may reply to Andy's beta invitation thread;
Andy can copy reproducible bugs into the tracker. Ask for page/team/game,
reproduction steps, expected/actual behavior, device/browser/PWA, displayed data
time and an optional screenshot without personal details.

Existing static Pages hosting is suitable for this initial small beta. No new
backend, account system, dependency or feedback service is required. This is
not a thousands-of-concurrent-users load-test claim. Start with the approved
25–50-person group and record real use before widening the invitation.

**No beta readiness blockers remain. Readiness verification is formally closed.**
No new feature, redesign, Version 7 or additional development cycle was begun.
Only closeout documentation changed after the deployed application commit above.

## JavaScript bundle-size baseline update (2026-11-17, PR #39)

The beta analytics workflow allows at most 10,240 gzipped JavaScript bytes of growth over a fixed
production baseline. The original baseline, `451f610` (pre-analytics), had been consumed by released
V7 work: production `474c72d` already measured 11,046 bytes over it, so every new PR failed regardless
of its own size. The baseline is now the verified GitHub Pages deployment `474c72d` (PR #38, deployed
2026-11-17), which PR #39 branches from. The 10,240-byte allowance is unchanged and is cumulative from
that release. The PR #39 school search adds 1,454 bytes.
