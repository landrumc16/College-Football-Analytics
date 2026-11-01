# V2 observed workbook parity — first five rows

Source: original Google Sheet, `Predictions!B6:O10`, formula values and unformatted calculated values inspected on 2026-11-01.

Recalculated the workbook's independent projected margin (`F`), model-only probability (`N`), and market-assisted displayed probability (`H`) for these five fixtures:

| Home | Away | Neutral | Home spread | Model margin | Model home probability | Displayed home probability |
|---|---|---|---:|---:|---:|---:|
| Akron | Ohio | No | +12.5 | -7.51146947 | 0.27670251 | 0.18602992 |
| Miami (OH) | Buffalo | No | -6.5 | 9.38914301 | 0.76871548 | 0.68298599 |
| Massachusetts | Ball State | No | -4.5 | 4.20476794 | 0.63131906 | 0.62980160 |
| Sacramento State | Toledo | No | +27.5 | -16.50220939 | 0.10803365 | 0.03742636 |
| Eastern Michigan | Central Michigan | Yes | -1.5 | -0.68266863 | 0.47818188 | 0.54416508 |

All fifteen recomputed outputs match workbook values to floating-point precision. `tests/test_workbook_live_parity.py` stores rounded observed values for regression. This is **formula parity, not evidence of forecast accuracy**.

Important provenance issue to address before historical scoring: a completed-game record may be retrieved after kickoff, so `HistoricalGame.source_retrieved_at` must **not** be used as the timestamp for the pregame prediction's input snapshot. Forecast-input provenance needs a separate timestamp and source identity; otherwise valid archived forecasts can be incorrectly excluded. Do not publish a multi-season accuracy claim until this is fixed and tested.

CI remains unverified: the available GitHub connector only retrieves pull-request-associated workflow runs; absence of those is not evidence of a passing or failing branch push workflow.
