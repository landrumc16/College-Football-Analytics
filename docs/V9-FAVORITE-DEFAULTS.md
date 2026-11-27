# V9 Maintenance — Favorite-Team Defaults

This is one owner-requested V9 maintenance improvement. It is isolated on `v9-favorite-defaults`; main and production remain unchanged pending explicit owner merge approval. Baseline: `c9cde2ee7a8faf25aa6bab76d0590fe719f6f022`.

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
