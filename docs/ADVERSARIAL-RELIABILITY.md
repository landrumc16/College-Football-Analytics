# Public-beta adversarial reliability verification — 2026-11-14

Production application tested: `2c47bec5935fd32844ef20c307e3aab4c201d052`.
The current production branch receipt, `6dfb59975d3d6333744227b48a6201afb1811176`,
adds only beta-readiness documentation; application/data source is identical.
Live URL: https://landrumc16.github.io/College-Football-Analytics/ .

**Production result: FAIL / NO-GO for beta invitations until PR #29 is approved,
merged and verified in production.** Version 6 remains closed. This is a narrow
reliability correction, not a new feature or development cycle. No production
change or merge is authorized by this report.

## Exact build and isolation

The experiment downloads the actual `github-pages` artifact from deployed run
[43649840894](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43649840894),
artifact `14134914909`, rather than substituting a demo or rebuilding the baseline.
Its ZIP SHA-256 is `57a5dad4f8b3ef4fe6f81e73c446ed0f76a7bcf76d5c771fde78c47481a31a81`.
The extracted tar SHA is retained with each experiment. All browser load, request
bursts and intercepted fixtures target `127.0.0.1:4190`. External browser requests
are aborted. Live publication bytes are never altered.

Candidate builds replace only the frontend bundle; every top-level production
JSON file is restored from the exact deployed artifact and checked byte for byte.
The workflow guards Python, data/research, scenario engine/worker, PWA assets and
dependencies against the deployed commit. The final tested candidate SHA, run,
case totals and retained artifact are recorded in PR #29's acceptance receipt.

Environment: Ubuntu 24.04 GitHub Actions, Python 3.11, Node 20, Playwright 1.56.1,
headless Chromium. Viewports: 375, 390, 430, 768 and 1536 pixels. Android/PWA checks
use Chrome emulation; this is not a claim of physical-device testing or CDN
capacity certification.

## Verified production failures and reproduction

Use the deployed artifact locally. In a fresh browser context intercept only the
named JSON response, preserving its original bytes except the stated mutation.
These are conditional bad-publication failures, not claims that live files are
currently corrupt.

| Isolated mutation and interaction | Observed production behavior | Narrow correction |
| --- | --- | --- |
| `season-report.json`: set `rankings` to `[null]`, then open Home | Uncaught null `team` read; whole application disappears | Reject invalid ranking rows before committing report state; retain existing retry |
| Same file: set `rankings` to `[]` | Apparently current homepage with no model rankings and missing rank information | Treat the incomplete core report as unavailable, with retry |
| `v6-program-context.json`: keep verified schema/status; replace programs with `[{team:"Texas Tech",season:2026}]`; Teams → Texas Tech → Historical Intelligence | Missing `recent.seasons` crashes the application | Contain optional-publication render failures within that section; retry refetches it |
| `v6-prediction-research.json`: keep experimental status/incumbent retained and `chronological_research.retrospective.games=3059`, omit scores; open Research | Missing `reference.brier_score` crashes the application | Independent research-section boundary and retry |
| `v5-forecast-evaluation.json`: keep verified status and incumbent `games=65`, omit scores; open Research | Missing numeric score crashes the application | Independent archive-section boundary and retry |
| `v6-scenario-input.json`: preserve report SHA/time but set `scale` to `"bad"`; Playoffs → Explore scenarios | Plausible-looking, invalid probabilities, including leading teams at 100% | Reject invalid scalar parameters before starting the existing worker |

The fault suite additionally probes null location adjustment, negative seed,
missing core/optional files, invalid JSON, malformed polls/teams, snapshot hash
mismatch, timestamps from 2020 and 2030, and recovery after restoring original
responses. Exact payload mutations are in `web/tests/adversarial-reliability.mjs`.
Known failures are first reproduced against the unchanged artifact, then the same
suite must pass against the candidate. The baseline step intentionally allows
failure so candidate acceptance can proceed; its raw failed results are retained.

## Stress conditions and regression evidence

- 100 destination changes; long, Unicode, empty and injection-like searches;
  31 school changes; 16 Profile section changes; repeated invalid/same-school
  comparisons and prediction searches.
- 20 favorite add/remove cycles, reload persistence, independent Tech/Georgia
  browser profiles, invalid JSON/wrong types/hostile strings in favorites, blocked
  storage and quota exceptions.
- Eight scenario start/unmount races, exact reset during computation and no
  surviving workers after unmount.
- Active shell-cache poisoning with obsolete JSON/index content, JSON HTTP 503,
  interrupted network navigation, offline page and return-online recovery. Normal
  PWA installability/update/offline checks also rerun in a fresh context.
- 80 navigation cycles with forced-GC checkpoints and retained heap/DOM readings;
  a 32 MiB total and 12 MiB late-growth ceiling. This is a finite soak, not proof
  against every possible long-session leak.
- Independent 1/10/25/50 browser visitor phases, mixed five-width layouts, with
  one in ten visitors executing the existing 2,000-draw worker. A separate
  1,000-request burst uses concurrency 25. All load is loopback only.
- Existing Monte Carlo implementations: eight unsigned-32 seeds × baseline /
  Army win / East Carolina win, 2,000 draws each, exact repeated outputs and
  Python/browser parity across all 138 teams. Check finite probabilities in
  [0,1], title ≤ field, field sum 12, national-title sum 1 and conference sums 1.
  Across baseline seeds, maximum probability deviation from the seed mean was
  0.0320625, below the conservative six-standard-error limit 0.0671820. This is
  simulation stability, not evidence of prediction accuracy.
- Default incumbent 10,000-draw runs reproduce exactly and match the deployed CFP
  report. Invalid game IDs, nonparticipants, started games, duplicate identities
  and nonfinite ratings are rejected by the Python path.
- All 549 existing Python regressions pass. Existing TypeScript/Vite builds,
  five-width browser journeys, historical publication safeguards, scenario
  fixtures, editorial parity and PWA regressions are rerun in PR acceptance.

The corrected initial baseline run
[43652760933](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43652760933)
passed 50 visitor journeys in 10.37 s and the 1,000-request burst with zero errors
(local p95 28.00 ms). Retained JS heap grew 173,068 bytes after 80 cycles; one DOM
document remained. These are isolated-run observations, not public-network latency
promises. Final-run measurements and raw receipts are attached to PR #29.

## Reproduce and approval boundary

The isolated workflow `.github/workflows/adversarial-reliability.yml` performs
artifact acquisition, guards, unchanged baseline, patched build, adversarial
browser pass, Monte Carlo experiment, full pytest and existing browser/PWA pass.
For an already extracted artifact and installed dependencies, run:

```sh
node web/tests/adversarial-reliability.mjs
python scripts/adversarial_monte_carlo.py
python -m pytest -q
node web/tests/mobile-smoke.mjs
```

Results and failure/containment screenshots are retained in Actions artifacts for
90 days. Test source, provenance and this report remain in Git history. Earlier
harness-only failures (an overly exact school label selector, optional-response
races and waiting for a scenario response before opening Playoffs) are not counted
as application defects. They were corrected without weakening app assertions.

PR #29 does not change either prediction/simulation engine, any statistical
calculation, verified archive, production data, design, navigation, dependency or
PWA behavior. Owner merge approval is still required. After approval, deploy and
verify production recovery and normal journeys before changing this NO-GO to GO.
