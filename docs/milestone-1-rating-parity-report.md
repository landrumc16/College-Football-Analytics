# Milestone 1 — Eight-pass rating parity verification

**Reference:** Frozen 2026 Week 7 Google Sheets snapshot committed under `tests/fixtures/`.
**Coverage:** 138 teams, 510 completed games, 8 iterative rating passes (1,104 numerical comparisons).

## Independent calculation result

A fresh independent JavaScript implementation of the documented eight-pass formulas was executed against the frozen fixture records retrieved from GitHub. It reproduced the workbook's eight pass outputs with:
- **0 of 1,104 differences above 0.001**
- **Maximum absolute difference:** 7.105427357601002e-15
- **Mean absolute difference:** approximately 1.1496314166337602e-15

This confirms numerical parity for the eight iterative passes with the frozen source baseline, not yet for all model outputs.

## Regression gate

`tests/test_rating_parity.py` invokes the committed Python parity checker and fails if any compared metric differs by more than 1e-6. This gate covers additional metrics including adaptive rating, strength of schedule and wins/losses, whose results **have not yet been independently confirmed**. It is possible the gate will expose further differences; resolve them rather than weakening the tolerance.

## Still required before Milestone 1 closeout

- Verify the Python pytest workflow actually passes in GitHub Actions; investigate any failures.
- Reconcile adaptive ratings, strength of schedule, quality wins and bad losses.
- Capture remaining full schedule and compare projected wins, conference wins, ranking keys and Top 25 ordering.
- Compare the prediction probabilities against a frozen reference.
- Publish complete discrepancy counts and a verified CI run link.

**Important:** The independent calculation was executed in the tool runtime, not by running the committed Python package. Do not represent this report as a successful Python or CI test run.

## Additional independent reconciliation (2026-10-31)

Using the same frozen 138 teams and 510 completed games, six derived metrics per team (adaptive rating, SOS, wins, losses, quality wins and bad losses) were independently compared: **828 comparisons, zero differences above 1e-6**. This revealed and corrected a mistaken SOS column reference: Games!AJ/AK use Teams Rating_7, not Rating_8 (commit f06b85d).

The FullSchedule tab was frozen as **888 scheduled games**. Independent expected-win calculations matched all **138** Teams!AP values with zero differences above 0.001; maximum observed difference was approximately 3.55e-15. The committed Python parity CLI now checks projected wins as well. Its CI run has not yet been verified.
