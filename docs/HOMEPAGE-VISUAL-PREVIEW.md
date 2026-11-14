# Homepage visual approval preview

Status: visual design approval pending. This is an isolated, opt-in browser
preview of the owner's sports-publication direction, not a completed rollout.
The default application and production `main` remain unchanged.

The preview uses the checked-in 2026 season report and poll snapshot, and the
existing source-gated national Report Card publication. No outcome, probability,
rank, historical trend, source record or research method is invented or modified.
Screenshots use sample saved teams (Texas Tech, Texas A&M, Georgia) selected in
an isolated browser through the existing favorites controls.

The front page has five short sections: two featured matchups on phones (three
on desktop), compact saved-team rows, a model Top 5 with a real AP disagreement,
a short projected playoff outlook, and one verified program finding. The
spotlight chooses an already-published rising trajectory among saved schools;
Texas Tech's retained 3-year and 10-year FBS win rates support the preview copy.
No weekly movement, causal claim or new score is inferred.

The masthead is compact and retains the approved collegiate logo and palette.
About/privacy and installation guidance live in its secondary Menu. The phone
bottom bar has five labelled SVG icons and safe-area padding. Desktop keeps
horizontal five-destination navigation. Home has no This Week/Game Predictions
secondary buttons; Featured Matchups and All games open existing prediction views.

`web/editorial-preview.html` is a separate entry and builds to `editorial-dist`
with `vite.editorial.config.ts`. The normal entry keeps its existing default
behavior. The preview reuses the actual App's state and deeper views, with working
links to predictions, profiles, rankings, playoffs and historical intelligence.
The original favorite manager is available under Edit teams. Service-worker
registration is left to the normal entry during this isolated design checkpoint.

The preview workflow captures 390×844 and 1536×900 browser screenshots, plus
full-page captures and data SHA-256 receipts. It checks the five sections,
real-data spotlight, sample favorites, navigation, detailed-view links, page
width and a maximum two-phone-screen document height. Evidence and the exact
preview SHA are recorded in the draft pull request.

Visual approval is the next required owner decision. Complete integration,
375/390/430/768/1536 acceptance, regression, keyboard/mobile navigation and PWA
install/update/offline checks follow that approval. Nothing is merged or deployed
by the preview workflow. The prior PR #20 remains unmerged and is not included.
