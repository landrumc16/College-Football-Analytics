# Navigation consolidation

The owner explicitly authorized this Navigation & UX Consolidation after the
Version 5 release: “consolidate related pages into a cleaner, more intuitive
application and complete the implementation.” This scoped refinement supersedes
the prior release-only restriction on navigation work; it reorganizes the released
Version 5 interface. It does not change
prediction formulas, historical inputs, peer scoring, forecast verification or
research methodology. Production remains unchanged until owner approval of the
focused `ux-navigation-consolidation` pull request.

| Primary destination | Secondary views |
| --- | --- |
| Home (default) | This Week, Game Predictions |
| Rankings (second) | Model Rankings, AP Poll, Coaches Poll, Team Stock Watch |
| Teams | Team Profiles, Compare & What If, Program Directory, Hype Index, Program Trajectory |
| Playoffs | CFP Projections, Conference Races, Contenders & Pretenders |
| Research | Prediction Accuracy, Historical Research, Methodology, Data Sources, Model Validation |

The existing What If calculation lives in Compare, where the same venue selector,
projection, swap and reset controls already existed. Stock Watch and Contenders
keep the existing current-season comparisons and explicit limitations; no stock
index or contender classification is invented. Program Directory retains national
current-season comparisons and the existing sorting/filtering controls.

Team Profile is the school destination from favorites, rankings, program tables,
historical lists and comparisons. The selected school is shared with its schedule.
Its four sections contain:

- **Overview:** model rank/strength, record, projected wins and current AP/Coaches
  ranks. Form, conference, postseason, recruiting and forecast context are in a
  single disclosure, with existing explanations retained.
- **Schedule & Predictions:** the complete existing school schedule (location,
  scores, win probability and margin), tracked performance against expectations,
  the over/underachievement leaderboard, opponent strength and pick explanations.
  Missing final scores and identity-conflicting forecasts remain unavailable using
  the original Profile forecast guard.
- **Historical Intelligence:** verified FBS results and 3/5/10-year windows,
  long-term direction, historical expectations and coverage/source disclosures.
- **Program Report Card:** the existing shared category scores, overall grade,
  AP/Coaches records, methodology and source links.

Favorite schedule shortcuts open the correct school and Profile section directly.
Game cards still open filtered prediction lists, with the original autocomplete
and sharing behavior. The small Home playoff snapshot displays existing projected
seeds and opens the full projection; it introduces no new forecast calculation.

Primary controls fit across phone widths. Secondary tabs wrap, have 44px minimum
height, expose selected/panel relationships, and support Left/Right/Home/End keys.
The existing collegiate colors, typography, logo and PWA behavior are retained.

Verification reuses the release browser suite at 375, 390, 768 and 1536px. It covers
all five destinations, all secondary views, all four profile sections, source-backed
grade parity, ranking search, prediction autocomplete, isolated persistent favorites,
contextual links, What If controls, research, failure/retry and Android Chrome PWA
emulation (installability/update/offline/recovery). Both existing Chromium versions
are exercised by V4 and V5 acceptance. Exact tested SHA, final workflow results and
inspected screenshots are recorded in the pull request. The verified historical
archive and incumbent engine remain unchanged.
