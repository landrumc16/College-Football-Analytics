# V6 Product and UX Contract

## Preserve V5 design
Maintain collegiate logo, typography, palette, responsive spacing and current user journeys. Mobile: persistent five-item bottom nav Home, Rankings, Teams, Playoffs, Research; secondary section dropdowns instead of horizontally overflowing tabs. Desktop: horizontal navigation where it fits. No new top-level destination.

## Home is a summary, not a data dump
Five short previews: Featured Matchups, My Teams, Rankings Snapshot, Playoff Watch, Program Spotlight. Each answers what matters, why, and links directly to its full analysis. Do not put complete tables, repeated Profile/Compare/Schedule buttons, or a separate This Week/Game Predictions tab row on Home. Prefer first-screen usefulness and limited scrolling; measure on 375/390/430px screenshots.

## Full pages own detail
Rankings: model/AP/Coaches/Stock. Teams: profiles, compare, historical intelligence and Report Cards. Playoffs: conference/CFP outlook and scenarios. Research: forecast accuracy, methodology, provenance and limits. Team Profile: Overview, Schedule & Predictions, Historical Intelligence, Program Report Card. Preserve existing in-app shortcuts, selected-school/section behavior and browser back behavior. The current app uses React view state and callbacks, without a per-view URL/history router; this is not an instruction to add a routing system or new URL scheme.

## New V6 features
Integrate matchup drivers within game details; coaching/recruiting context within program analysis; scenario controls within Playoffs; favorite-team signals on Home. Never invent news, games, roster facts, causal explanations or prediction probabilities. Show as-of date, uncertainty, and unavailable states.

## Hosting and freshness constraints

The React/Vite app is a static GitHub Pages deployment, fed by Python/Actions
JSON publications. Interactive scenarios must fit this architecture and reuse
the existing model/simulation contract; do not introduce a backend, accounts or
new hosting as an implicit dependency. Match a zero-override run to its own seeded
baseline exactly, and verify any browser computation against retained Python
reference fixtures under a predeclared Monte Carlo error policy.

Offline currently means an explicit offline fallback and recovery, with live
JSON network-only. Preserve this safety contract and freshness warnings; do not
serve cached football statistics as current or promise full offline analytics.

## Acceptance
Real browser journeys and screenshots at 375, 390, 430, 768 and 1536 widths; keyboard/screen-reader labels; contrast and focus; no clipped navigation, hidden action, horizontal page overflow or blocking bottom bar; favorites persist independently across devices; PWA install/update/offline work. Visually inspect screenshots, not just green tests.
