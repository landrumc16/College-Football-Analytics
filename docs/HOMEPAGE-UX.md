# Homepage and mobile UX refinement

The owner approved the real-data 390px and 1536px browser previews in PR #21.
The normal application now uses that approved sports-publication layout.
This changes presentation and navigation only; the incumbent prediction engine,
verified records, source gates, statistical calculations and methods are retained.

## Find the full analytics

| Homepage preview | Full destination |
| --- | --- |
| Featured Matchups / All games | Existing Game Predictions, week filters, school autocomplete, explanations and comparison |
| My Teams row | Selected school's Team Profile, with Overview, Schedule & Predictions, Historical Intelligence and Program Report Card |
| Rankings Snapshot | Full model rankings; AP, Coaches and Stock Watch remain secondary tabs |
| Playoff Watch | CFP projections; Conference Races and Contenders & Pretenders remain secondary tabs |
| Program Spotlight | Highlighted school's Historical Intelligence section |

The spotlight uses the existing source-gated, reviewed rising trajectory, preferring
saved schools when available. Its percentages come directly from published windows.
AP/model disagreement is a rank comparison, never invented weekly movement.
Upset Watch remains available within full Game Predictions. Games That Matter
remains within full Playoffs. Comparisons, directory, Hype Index, Program Trajectory,
research, accuracy, methodology, sources and validation retain their full views.

The mobile bar has five labelled icons and remains fixed with safe-area clearance.
At 768px and above navigation remains horizontal. Secondary tabs scroll in one row
on phones. Focus scroll clearance protects controls from the bottom bar.
Home has no redundant This Week/Game Predictions tabs. Its compact Menu contains
About/privacy and installation guidance. Edit teams reuses the existing local
favorites/search controls; saved-team rows replace repeated action buttons.
Browser storage key and per-profile persistence are unchanged.

## Acceptance

`npm run build --prefix web` builds the actual app. No preview entry or feature
flag remains. `node web/tests/mobile-smoke.mjs` exercises the complete platform
at 375, 390, 430, 768 and 1536 pixels and Android Chrome emulation, including
installability, service-worker update/reload, real offline fallback, no live JSON
cache, recovery, favorite persistence/isolation, search, polls, predictions,
comparisons, all four Profile sections, historical source gates and research.

`node web/tests/editorial-home.mjs` checks the five previews against real retained
data, all deep links, keyboard navigation, scrollable tabs, no page overflow and
the two-screen phone target with three sample favorite teams. It captures actual
homepage and four Profile-section screenshots at every requested width, plus
phone bottom-of-page views so the fixed navigation can be inspected in context.

The V5 acceptance workflow stores the tested revision, source SHA-256 receipts,
checks, screenshots and production build as `v5-browser-and-build-evidence`.
Exact tested commit and run links belong in PR #21, where they can identify the
final revision without a self-referencing documentation-only commit.
Merge and production deployment still require explicit owner approval.
