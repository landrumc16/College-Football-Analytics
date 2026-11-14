# Version 6.0 — production acceptance and formal closeout

**Status: RELEASED AND CLOSED — November 14, 2026 (America/Chicago).**

Production: https://landrumc16.github.io/College-Football-Analytics/

## Released identity and approval

The owner explicitly approved PR #25 at
`6bcaa3a649ff781d81906e7f11e468cf3abb23a9` after reviewing the actual build
screenshots. PR #25 merged as `60e5c8b762dfaab5f29c2e88389f3516f8edb61e`.
The merge also retained the intervening normal CFBD refresh at
`e910174db4e6b73cff7122df6697027f99105e97`; the differences from the approved
candidate were the existing live game/report and current Report Card refresh.
The verified historical archive and approved application implementation remain
preserved.

**Final deployed and production-tested commit:**
`fda1fc284a6214611eeae4451d67daaea722d670`.

One deployment-only correction was necessary. The original Pages workflow
rebuilt the season report after generating its scenario packet. The report's
`generated_at` changed, causing the packet's exact-byte freshness check to refuse
scenario controls. The corrected workflow regenerates/copies V6 packets after
the final report and verifies their exact SHA-256 identity before publishing.
Only `.github/workflows/dashboard.yml` changed in that correction; no application,
prediction-model, simulation calculation or historical-archive change was made.
The failure was reproduced, fixed and verified on the live site before closeout.

## Production evidence

- [Successful Pages build, deployment and live acceptance](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43632465602).
- [Additional live V6 acceptance at all five widths](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43632670251).
- [Live navigation/PWA screenshots](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43632465602/artifacts/14128583209).
- [Live V6 context/research/scenario screenshots and public-asset receipts](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43632670251/artifacts/14128553130).
- [Retained machine-readable acceptance receipt](evidence/v6-production-2026-11-14.json).

The supplementary workflow is on an evidence-only branch. Its checkout is pinned
to the actual deployed commit above; it points the existing browser harness at
the public production URL. Its artifact's `production-sha.txt` was inspected and
matches the deployed SHA. Application code was not changed by that harness.
Both production artifact ZIP checksums were independently verified before the
screenshots and receipts were inspected.

## Completed live acceptance

All 549 Python regressions and the production TypeScript/Vite build passed on
the deployed source. The final packaging identity guard passed. The deployment
smoke check verifies public report bytes against the actual validated build,
model provenance, official polls, research publications and source freshness.

Actual HTTPS production browser journeys passed at **375, 390, 430, 768 and
1536 pixels**. They cover all five main destinations, adaptive secondary/Profile
selectors and keyboard operation; rankings and polls; search/autocomplete;
complete Team Profiles and schedules/predictions; historical intelligence,
Hype/Trajectory/Report Cards and comparison shortcuts; independent persistent
favorites; and the existing research views. Homepage, program context, research
and scenario screenshots at all five widths were visually inspected. No page
overflow, overlapping navigation or page errors were found.

V6-specific live checks confirm identical sourced metrics across Profile,
Program Directory and Compare; truthful 3,059-game experimental research;
future-matchup/winner controls; computed CFP/conference results; exact seeded
scenario reset at every width; and agreement with the retained Python reference.
The 390px, 2,000-draw algorithm benchmark under Chromium 4× CPU throttling took
**1,694.9 ms**, within the predeclared 3,000 ms limit. Direct browser inspection
also confirmed that selecting Texas A&M over Texas changed conditional results
and reset returned to zero selected outcomes.

Android Chromium emulation passed installability, update/reload, actual network
outage/offline fallback, no live-JSON cache, refresh failure/recovery and return
online. These results are emulated browser evidence, not a physical-device claim.
The public application was left open on Home for the owner to explore.

## Prediction authority and preserved boundaries

The live report identifies `workbook_2026_baseline`, with status
`incumbent_not_v3_promoted`. The production model/pipeline/predictions source
hashes match the frozen incumbent receipt. The live research packet identifies
`experimental_not_promoted`, with `incumbent_retained: true`, `eligible: false`
and `authorized: false`. **No challenger promotion occurred.**

The challenger did not establish an advantage against the research proxy, and
historical incumbent-pairing/cutoff gaps remain explicit. This closes the approved
research-only release path; it does not assert a production accuracy improvement.
The separately verified authentic 65-game archive and frozen 178-game future
experiment remain intact. No new prospective score is invented.

The retained data foundation covers 1,452 classified team-seasons, with current
138/138 coverage in recruiting, rosters and coaching. Historical original
publication cutoffs, optional staff/transfer/playing-production details and
non-causal limits remain disclosed. Scenario committee/tiebreak approximations
and simulation uncertainty remain visible. Live data is network-only, with
explicit offline fallback rather than cached statistics presented as current.

All six milestone requirements are complete under the approved roadmap and its
research-only challenger path. Owner merge approval, deployment, live verification
and evidence recording are now complete. **No release blockers remain. Version
6.0 is formally closed.** Further development requires a new owner instruction;
no subsequent version or unrelated feature is authorized by this closeout.
