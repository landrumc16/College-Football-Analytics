# Navigation consolidation

The owner explicitly authorized this Navigation & UX Consolidation after the
Version 5 release: “consolidate related pages into a cleaner, more intuitive
application and complete the implementation.” This scoped refinement supersedes
the prior release-only restriction on navigation work; it reorganizes the released
Version 5 interface. It does not change
prediction formulas, historical inputs, peer scoring, forecast verification or
research methodology. The owner approved PR #18; the exact candidate was merged,
deployed and verified. This UX refinement is complete and closed.

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

Primary controls fit across phone widths. Secondary tabs wrap on wider screens and swipe horizontally on phones, have 44px
minimum height, expose selected/panel relationships, and support Left/Right/Home/End
keys. Compact About/privacy and Install controls keep help accessible without
pushing the first Profile metric below the initial phone viewport.
The existing collegiate colors, typography, logo and PWA behavior are retained.

Verification reuses the release browser suite at 375, 390, 768 and 1536px. It covers
all five destinations, all secondary views, all four profile sections, source-backed
grade parity, ranking search, prediction autocomplete, isolated persistent favorites,
contextual links, What If controls, research, failure/retry and Android Chrome PWA
emulation (installability/update/offline/recovery). Both existing Chromium versions
are exercised by V4 and V5 acceptance. Exact tested SHA, final workflow results and
inspected screenshots are recorded in the pull request. The verified historical
archive and incumbent engine remain unchanged.


## Production closeout — November 13, 2026

Andy explicitly approved [PR #18](https://github.com/landrumc16/College-Football-Analytics/pull/18)
at candidate `e7ea35d439bc51d97d63ba6f74d16de3ffe41a97`. It merged with an expected-head
SHA check. The deployed application tree matches that approved candidate exactly.

**Deployed and live-tested production commit:**
`34d12e3a6819caf17f1dc58bf60b0dc8ba35b5f1`.

[GitHub Pages build, deployment and live acceptance run 43547278678](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43547278678)
completed successfully. Its build passed 526 Python tests, strict workbook parity
(2,070 metrics; zero differences above 0.001), the production build and browser/PWA
acceptance before deployment. Post-deployment checks matched the published report
against its validated build artifact and ran the browser journeys against the
public URL.

Live verification passed at **375, 390, 768 and 1536px**, covering exactly five
primary destinations, every secondary view, all four Profile sections, rankings
and polls, prediction autocomplete, verified historical intelligence and grade
parity, comparison/What If, persistent isolated favorites, favorite schedule
shortcuts, first-screen phone metrics, tab scrolling, research and failure/retry.
Schedule regression checks retain unavailable states for missing final scores and
identity-conflicting forecasts.

Android Chrome emulation passed PWA installability, service-worker update,
genuinely disconnected offline fallback, uncached live JSON and recovery. This is
emulated Android testing, not a physical-device installation claim. Published
Report Cards, historical results, forecast evaluation, manifest and service-worker
bytes independently matched this production revision.

[Production browser screenshots and recorded production SHA](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43547278678/artifacts/14094795845)
are retained in the workflow artifact. ZIP SHA-256:
`9d7687723df69d0a000436754505ef3f9e03fd81ddb42caf825620387b94e22c`.
The artifact and recorded SHA were retrieved and checked; key phone, desktop,
historical/comparison and offline captures were visually inspected.

**Live URL:** https://landrumc16.github.io/College-Football-Analytics/

**Status: complete, deployed and formally closed. Remaining blockers: none.**
The incumbent engine, calculations, methodology and verified archive remain
unchanged. No subsequent version or unrelated feature work is started or
authorized by this closeout. Existing scheduled data updates continue normally.
