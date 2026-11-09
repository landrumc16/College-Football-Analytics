# College Football Analytics V4.0 — Release Candidate Notes

**Status:** Development candidate; not authorized for production.  
**Validated executable commit:** `0096dab52584541c4b5234a0a2102681848c22b4`.  
**Validation:** [V4 workflow 42563594154](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42563594154) and [Python/dashboard workflow 42563594199](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42563594199) succeeded for this exact executable SHA.

## Fan-facing changes

- Historical Program Rankings: distinct from current-season power rankings, with 10-/5-/3-season strength windows, completeness requirements, source details, conference filters, and team navigation.
- Historical Hype Index: separate AP and Coaches preseason-to-final Top 25 expectations and outcomes, emphasizing recent completed seasons where a verified ten-season history exists; distinguishes historical tendency from current-season poll/model disagreement.
- Program Trajectory: independently calculated ten-season direction, five-season direction, and three-season momentum; verified season-by-season strength chart with gaps for missing years; derived combined interpretations of hype and momentum, not a new prediction score.
- Consolidated Team Profiles expose the available historical classifications; the primary dashboard stays focused on current football information.
- Current-season AP/Coaches poll comparisons use the incumbent model's rankings, support conference filtering independently of historical publication, and explicitly describe disagreement as **not** proven poll error.

## Important limitations

- **Historical publication gate:** Hype Index, historical Program Rankings, and trajectory values are not published without independently reviewed ten-season source provenance. Demo fixtures and synthetic test data do not establish historical coverage. Missing data must remain visibly unavailable, not silently estimated.
- **Current conference labels:** Conference discovery uses membership from the current standings report. It is not a historical realignment model.
- **Team Stock Watch:** Four-week stock movement requires dated snapshots and a validated stock formula. No unsupported stock index is displayed.
- **Contenders & Pretenders:** No unsupported independent expected-record or contender classifications are published.
- **Weekly perception movement:** No changes are inferred without dated poll snapshots.
- **Experimental challenger:** Research-only; not promoted. The incumbent prediction model remains the sole production prediction engine.
- **Visual acceptance:** Forty actual browser screenshots from V4 validation artifact `13647902100` (375, 390, 768, 1536 pixels; ten views) have been downloaded and visually inspected as a contact sheet. The Team Profile contrast defect was corrected and checked in a 390px capture. Full-resolution, long-page visual acceptance remains open.

## Release gate

The passing workflows verify regression, workbook parity, baseline provenance, frontend build, Chromium journeys, and PWA checks. They do **not** establish historical-source publication, complete feature acceptance, or visual signoff. Before merging: inspect desktop/mobile screenshots, resolve release-required product gaps, update evidence against the final executable SHA, and obtain explicit owner approval.

**No merge to `main`, GitHub Pages V4 deployment, or challenger promotion is authorized by these notes.**

## Final candidate follow-up (November 9)

- Historical discovery tables now initially display 25 rows with an explicit control to reveal all matching programs. Search and conference filters continue to operate on the complete data set.
- Full V4 workflow `42563594154` and Python model workflow `42563594199` both completed successfully for executable commit `0096dab52584541c4b5234a0a2102681848c22b4`.
- The V4 workflow uploaded 40 desktop/tablet/mobile browser captures as artifact `13650163957` (`v4-mobile-browser-evidence`). Captures exist but full-resolution human visual acceptance has not yet been established.
- **Owner approval remains blocked** until visual acceptance and explicit disposition of historical source authenticity and coverage. The November 6 decision permits honest unavailable states, not fabricated historical findings. No further features should be added solely to postpone this decision.
