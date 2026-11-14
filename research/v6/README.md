# V6 verified research foundation

This extends, and does not rewrite, the verified V5 archive. `foundation.json.gz`
is a deterministic public **derived** team-season corpus. `sources.json` pins
38 original publisher inputs by immutable commit, Git blob and SHA-256, records
retrieval dates, upstream families and reuse conditions. `identities.json` freezes
the independently retained NCAA classification crosswalk. `manifest.json` hashes
the derived corpus and inherited inputs. See `COVERAGE.md` for denominators,
missingness and exclusions; transition/opt-out classifications are retained.

The publisher's pinned DESCRIPTION declares CC BY 4.0. Attribute
SportsDataverse/cfbfastR-cfb-data (Saiem Gilani), with ESPN roster, 247Sports
recruiting and CFBD coaching upstreams. CFBD's published API terms permit private
retention and derived analyses but restrict raw redistribution. Consequently,
raw coaching names and enriched athlete biographies stay in a private cache,
never in this repository, public browser files or CI artifacts. Public outputs
are aggregate recruiting composition, roster membership retention and derived
head-coach continuity, not a roster/coach database mirror.

No metric here is independently corroborated at individual-player level or
historically pregame-available merely because its season is old. Historical
experience attributes are excluded because biography backfills are not season
experience. Missing recruiting grades/stars are not zeros, grades use publisher
units without capping, and roster retention is not returning playing production.
Head-coach continuity is dominant-season attribution, not exact hire dates or
complete coordinator staffing. These limits are machine-readable and tested.

Reproduce with the optional research decoder (not an app runtime dependency):

```bash
python -m pip install -e '.[dev,research]'
python -m scripts.build_v6_foundation --cache /private/v6-inputs --check
python -m scripts.build_v6_foundation --cache /private/v6-inputs --offline --check
python -m pytest -q tests/test_v6_foundation.py
```

The first command downloads only absent, hash-pinned inputs. Changed bytes or
missing offline inputs fail rather than replacing history. The private cache
can be retained for future offline rebuilds; source URLs remain immutable.
The existing code in `talent.py`, `coaching.py` and V5 source review is reused for
availability semantics and canonical identities. Production model/report and
frontend remain unchanged during this milestone.
