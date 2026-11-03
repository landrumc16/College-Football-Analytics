"""Normalize dated team-season statistics into scheme observations.

Season aggregates are not automatically known before games in that season.
Caller must supply independent published_at and observed_at timestamps.
"""
from math import isfinite
from .coaching import TENDENCIES
from .talent import validate_talent_observation


def normalize_scheme_statistics(records, *, cutoff):
    output = []
    seen = set()
    for row in records:
        if row.get("feature") not in TENDENCIES:
            raise ValueError("Unsupported scheme metric")
        key = (row.get("team"), row.get("feature"), row.get("published_at"))
        if key in seen:
            raise ValueError("Duplicate team-metric publication")
        seen.add(key)
        value = row.get("value")
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("Invalid scheme metric")
        if row["feature"] != "pace" and not 0 <= value <= 1:
            raise ValueError("Rate metric must be a fraction")
        if row["feature"] == "pace" and value < 0:
            raise ValueError("Pace cannot be negative")
        validate_talent_observation({**row, "feature": "on_field_contribution"}, cutoff)
        output.append(dict(row))
    return output
