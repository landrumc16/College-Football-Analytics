# College Football Analytics V4.0 — Release Candidate Notes

**Status:** Development candidate; not authorized for production.  
**Validated executable commit:** `19e5db95124a30aae8a265bf80ccbabd55d3f5ab`.  
**Validation:** [V4 workflow 42544623801](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544623801) and [Python/dashboard workflow 42544623798](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544623798) succeeded.

## Fan-facing changes

- Historical Program Rankings: distinct from current-season power rankings, with 10-/5-/3-season strength windows, completeness requirements, source details, conference filters, and team navigation.
- Historical Hype Index: separate AP and Coaches preseason-to-final Top 25 expectations and outcomes, emphasizing recent completed seasons where a verified ten-season history exists; distinguishes historical tendency from current-season poll/model disagreement.
- Program Trajectory: independently calculated ten-season direction, five-season direction, and three-season momentum; verified season-by-season strength chart with gaps for missing years; derived combined interpretations of hype and momentum, not a new prediction score.
- Consolidated Team Profiles expose the available historical classifications; the primary dashboard stays focused on current football information.
- Current-season poll comparisons use the incumbent model's rankings and explicitly describe disagreement as **not** proven poll error.

## Important limitations

- **Historical publication gate:** Hype Index, historical Program Rankings, and trajectory values are not published without independently reviewed ten-season source provenance. Demo fixtures and synthetic test data do not establish historical coverage. Missing data must remain visibly unavailable, not silently estimated.
- **Current conference labels:** Conference discovery uses membership from the current standings report. It is not a historical realignment model.
- **Team Stock Watch:** Four-week stock movement requires dated snapshots and a validated stock formula. No unsupported stock index is displayed.
- **Contenders & Pretenders:** No unsupported independent expected-record or contender classifications are published.
- **Weekly perception movement:** No changes are inferred without dated poll snapshots.
- **Experimental challenger:** Research-only; not promoted. The incumbent prediction model remains the sole production prediction engine.
- **Visual acceptance:** Browser screenshot artifact exists but has not been independently inspected and approved as a final visual acceptance package.

## Release gate

The passing workflows verify regression, workbook parity, baseline provenance, frontend build, Chromium journeys, and PWA checks. They do **not** establish historical-source publication, complete feature acceptance, or visual signoff. Before merging: inspect desktop/mobile screenshots, resolve release-required product gaps, update evidence against the final executable SHA, and obtain explicit owner approval.

**No merge to `main`, GitHub Pages V4 deployment, or challenger promotion is authorized by these notes.**
