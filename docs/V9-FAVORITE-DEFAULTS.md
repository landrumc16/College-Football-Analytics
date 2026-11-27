# V9 Maintenance — Favorite-Team Defaults

**Released and formally closed November 26, 2026 (America/Chicago).** The owner approved PR #72 at `364d948d4914f4a6b50a8d87f094f790af0c65b5`; it merged as `a3d5d79221f4c544d0a4fc5dd9c93215bfb75e55`. [Production deployment and live verification](https://github.com/landrumc16/College-Football-Analytics/actions/runs/45932815678) passed. This is one focused V9 maintenance improvement; it does not begin a new version. Baseline: `c9cde2ee7a8faf25aa6bab76d0590fe719f6f022`.

## Selection Contract

`FavoriteDefaultsProvider` reuses the existing `cfba-favorites-v1` storage key, three saved slots and favorite editor. There is no separate primary designation in the existing app; the first nonempty saved slot is the primary favorite. An ineligible primary does not silently fall through to a secondary favorite: each control retains its existing fallback.

`useFavoriteSelection` and pure helpers in `favoriteDefaults.ts` implement one eligibility, precedence and navigation policy for school, game and calculator-perspective controls. They retain explicit per-tool choices in memory across normal navigation, including explicit empty/all choices. Those choices never modify favorites. A primary change does not interrupt the active selection; its default applies on subsequent navigation. Storage events synchronize favorite changes across tabs. Reload/PWA relaunch reads the saved favorite; transient tool choices are not stored as new permanent preferences.

Explicit school/game actions and existing direct-view links keep their meaning. A game default never chooses a scenario winner. Comparison/opponent populations exclude the first school, so no identical pair is selected. Published rankings, national peer populations, model formulas and statistics remain unchanged. The four verified display-name pairs already used by the pipeline (Miami, App State, Sam Houston, UL Monroe) resolve against each picker’s actual options; ambiguous/fuzzy matching is never used. A national-leader row remains an explicit selection even when its statistics label differs from the rankings label. No backend, API acquisition, analytics properties, subscriptions or refresh schedules change.

## Complete School/Matchup Control Audit

| Destination / Feature | Control | Default / Explicit Behavior |
| --- | --- | --- |
| Home | Add Favorite Team | Intentionally unchanged: saved teams are excluded from the eligible add list. Never auto-add or duplicate a saved favorite. |
| Home | Favorite/profile/featured-game shortcuts; All Games | Explicit school/game shortcuts win. All Games explicitly clears the prediction school filter. |
| Rankings | Find School in Intelligence | Primary if eligible; All Schools remains an explicit unfiltered choice. |
| Rankings | Model and official poll Search Teams | National free-text searches remain blank by default: complete national rankings/polls are preserved. These are not single-school selection controls. |
| Rankings / Playoffs / Teams | Find a Program in Stock Watch, Contenders & Pretenders and Program Directory | Primary from the eligible published schools; manual exact or partial lookup remains available. |
| Teams | Choose School / Team Profile | Eligible favorite; otherwise existing first-ranked-school fallback. Explicit links and session choices win. |
| Teams | First School / Second School | First defaults to primary. Second uses primary only if eligible and different; otherwise remains empty. Manual swap/reset and distinct-school handling retained. |
| Teams | Choose Team / Offense & Defense | Favorite if present in published statistics. Existing fallback is retained when unavailable. National leaders stay national. |
| Teams | Choose Opponent | Favorite only when different from the selected team and eligible. Explicit opponent links win. |
| Teams | Find a Team / Model Projections | Eligible favorite; initial week uses an available game for that team. Manual team/week/model controls remain usable. |
| Teams / Historical tools | Choose Historical Program / Report Cards | Favorite if in the published historical population. Grades still use the complete national peer population. |
| Teams / Historical tools | Choose Historical Program / Verified Program Development | Favorite only when the picker has sufficient historical chart coverage. |
| Teams / Historical tools | Chart Program Strength / legacy fallback | Favorite only in the actual filtered chart-school population. |
| Playoffs | Scenario Matchup | Earliest eligible future matchup involving the favorite. Otherwise existing Choose a Game fallback. Completed/started games remain ineligible. |
| Playoffs | Scenario Winner | No automatic winner: retains Model Probabilities. A game selection cannot force a win or change the simulation. |
| Research | Market game / Find a Game by Team Name | Default game involves the primary where available. Search remains a transient game lookup; explicit game shortcuts/manual choices win. |
| Research | Calculator team-perspective radio buttons | Favorite when one of the two teams; otherwise existing home-team fallback. Input-flip and all underlying math remain unchanged. |
| All national/historical tools | Free-text national searches; conference, year, poll, evaluation, unit and model filters | Not school selections. Existing defaults and national populations preserved. |
| All charts | Retained observation / historical window | Not school selections. Source evidence and time-window semantics unchanged. |

Audited every `SchoolSearch`, native select, team radio group, datalist and free-text search in `web/src`. Historical Results/Coverage and team-specific program cards receive explicit parent schools; they do not own another school selector. No selector was added to duplicate a feature.

## Permanent Verification

- `web/tests/favorite-defaults-unit.mjs`: primary slots, zero/ineligible favorites, explicit/manual/empty precedence, navigation-gated primary changes, asynchronous eligibility, comparison exclusion and relevant-game selection.
- `web/tests/favorite-defaults.mjs`: zero/one/multiple/empty-first/ineligible cases; actual React interactions at 375/390/430/768/1536; per-tool manual persistence; primary removal; cross-tab changes; reload and standalone-display emulation; historical tools; Research game/calculator; national ranking population; scenario default without an outcome override; page errors and overflow.
- `.github/workflows/favorite-defaults.yml`: read-only PR/on-demand workflow, offline source staging, permanent focused suite, existing five-width/Android PWA suite and retained evidence. No production deployment or data acquisition.
- The legacy calculator acceptance now expects the explicitly chosen school to persist for the same pair after venue/navigation changes; its empty-entered-odds, math and privacy assertions remain strict.
- Existing device-profile infrastructure is retained. Its retained-data pregame fixture now fixes browser time to its report receipt using Playwright `setFixedTime`; otherwise the hardcoded upcoming TCU/Texas Tech scenario expires when wall-clock kickoff passes. Previously hardcoded rating, margin and settled-game numbers now come from the staged source packets. Production timing and scenario eligibility are unchanged; this is explicitly fixture-clock testing, not a live-data claim.

Local focused browser results are retained in `docs/evidence/v9/favorite-defaults/local-browser-results.json`. Full CI and exact commit are recorded in the pull request. Physical-device testing is not claimed; the existing accepted WebKit lifecycle limitation remains. Existing visual design, model and archive protections remain release requirements.

Local final focused verification: 37 policy assertions and 12 browser cases (six favorite-population cases, five viewport cases, cross-tab/standalone persistence) pass. Existing calculator, Market, strength, school search, unit-statistics, projections, prediction explanations, postseason and statistical explanations browser suites pass. The unchanged JavaScript budget passes at +9,214 gzip bytes versus its existing pinned baseline (limit 10,240); see the retained bundle-size receipt. GitHub CI remains the authoritative exact-head gate. No source API calls, production writes or physical-device claims were used.


## Production Release Acceptance

| Requirement | Verified Production Evidence | Status |
| --- | --- | --- |
| Approved head and CI | Exact approved SHA reconfirmed; 13 successful checks and one expected refresh-evidence skip; SHA-guarded merge | Passed |
| Build/deploy and regression | Run 45932815678: build, Pages, published-dashboard identity checks, live browser/PWA, controlled analytics and freshness keeper all successful. Merged-tree Python: 839 passed, 2 skipped | Passed |
| Favorite defaults and free switching | Live actual-clock suite: 12 cases, including all requested widths, zero/one/multiple/ineligible/alias favorites, primary changes and manual per-tool choices | Passed |
| Comparisons, tools, links and national data | Distinct comparisons; statistics/opponents; program/history pickers; projections; Market/game/calculator; default scenario game is outcome-neutral; 138 national ranking rows preserved; explicit school links win | Passed |
| Persistence | Reload, cross-tab favorite changes and standalone-display emulation retain favorites. Browsing does not edit saved schools | Passed |
| Existing users / no reinstall | Same pre-release context and active service worker: old asset index-CBZ_fw7I.js opened Georgia despite saved Texas Tech; ordinary post-deploy reload loaded index-F0FUwkAK.js and selected Texas Tech. Favorites stayed exactly unchanged. No storage clearing, worker removal or reinstall | Passed |
| PWA and analytics | Permanent production Android Chrome-emulated install/update/offline/recovery and controlled delivery checks pass; PostHog ingestion independently confirmed | Passed |
| Reliability and freshness | Published monitor active, no critical/scheduling alerts at inspection; only existing discretionary quota warning. Source receipts remain visible and unit statistics honestly stale | Passed within recorded operating constraints |
| Preservation | src, data, research, published archives, CSS and production refresh/watcher/deployment workflows byte-identical to baseline; model calculations and permanent testing infrastructure retained | Passed |

Live tests used actual wall-clock time and the deployed report, not the pinned pregame CI clock. When the favorite has no still-future scenario game, Choose a Game remains the correct fallback and no winner is forced. All browser automation used isolated test profiles; it did not change real fans' saved schools. Supplemental live steps reuse the permanent favorite-default suite against the production URL, with live eligibility handling and the workspace's standard trusted proxy certificate. No TLS bypass was used.

Existing users receive the code on normal reload or reopening the online browser/PWA. An already-open page keeps its loaded JavaScript until then. The real pre/post receipt in `evidence/v9/favorite-defaults/release/existing-user-update.json` verifies this without reinstalling. `live-browser-results.json` and `production-receipt.json` retain the detailed acceptance record.

PostHog project 737110 confirmed 1 controlled test visit and 9 controlled page views after 03:15 UTC November 27. The short initial post-release query found zero non-test cfa_application_error and $exception events; partial-window/ingestion limitations apply. Controlled tests remain excluded from beta behavior. No analytics configuration was changed.

Live report/scenario identity is `4d4f23d727d557ac6c7ecc5dc9fb5681eb93eb930fb10bce8f511583a0649e56`. Game-data receipt remains November 26 20:28 UTC; report generation is November 27 03:13 UTC and does not pretend new acquisition. Unit-statistics receipt remains November 22 18:02 UTC and is marked stale. Intelligence covers 138 schools; projections cover 71 games; authentic pregame archive has 240 files and no settled all-three common cohort. Prior model/accuracy limitations remain unchanged. No CFBD acquisition was dispatched for acceptance.

Retained GitHub production artifacts: browser evidence 15169965838 (through December 27 UTC), analytics receipt 15170050649 (through February 25), Pages artifact 15169211734 (default expiry November 28 03:14 UTC), Pages digest `sha256:38a89bf4f8163297e5ce5ca3ff85d5d488f99e1a3996f845e80e0a4cc25849a1`.

Physical Android/iPhone hardware was not tested; existing accepted WebKit offline/update limitations remain. The quota warning reported 20 calls left and four days to reset; source acquisition/scheduling constraints continue under the existing runbook. No manual owner testing is required.

If later recovery is needed, the prior known-good code is c9cde2ee7a8faf25aa6bab76d0590fe719f6f022. Restore an approved retained artifact or prepare a narrowly scoped rollback preserving valid data, immutable forecasts/history and PR56 reliability. Favorites use the unchanged storage schema, so no destructive preference migration is required. No rollback was needed.

The maintenance improvement is closed. No unrelated feature, redesign, model promotion, milestone or Version 10 is authorized.
