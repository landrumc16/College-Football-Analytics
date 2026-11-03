"""Time-safe coaching and scheme observations for bounded challenger experiments.

These are attributable observations, not claims about a coach's causal effect.
No feature enters production predictions without chronological paired validation.
"""
from .talent import _timestamp

ROLES = frozenset({"head_coach", "offensive_coordinator", "defensive_coordinator"})
TENDENCIES = frozenset({"pace", "pass_rate", "explosive_play_rate",
                         "pressure_rate", "rush_success_rate", "pass_success_rate"})


def coaching_as_of(records, cutoff):
    """Return most recent staff assignments known strictly before cutoff."""
    limit = _timestamp(cutoff)
    if limit is None:
        raise ValueError("Cutoff must include timezone")
    selected = {}
    for row in records:
        if not isinstance(row, dict) or row.get("role") not in ROLES:
            raise ValueError("Unknown staff role")
        if not all(isinstance(row.get(key), str) and row[key].strip()
                   for key in ("team", "coach", "source")):
            raise ValueError("Missing staff identity or source")
        published, effective = _timestamp(row.get("published_at")), _timestamp(row.get("effective_at"))
        if published is None or effective is None:
            raise ValueError("Missing staff timestamps")
        if published >= limit or effective > limit:
            continue
        key = (row["team"], row["role"])
        previous = selected.get(key)
        if previous is None or published > _timestamp(previous["published_at"]):
            selected[key] = dict(row)
        elif published == _timestamp(previous["published_at"]) and row != previous:
            raise ValueError("Conflicting coaching assignments at same timestamp")
    return selected


def scheme_as_of(records, cutoff):
    """Select latest dated, source-backed tendencies by team and metric."""
    from .talent import validate_talent_observation
    limit = _timestamp(cutoff)
    if limit is None:
        raise ValueError("Cutoff must include timezone")
    selected = {}
    for row in records:
        if not isinstance(row, dict) or row.get("feature") not in TENDENCIES:
            raise ValueError("Unknown measurable scheme feature")
        published = _timestamp(row.get("published_at"))
        if published is None:
            raise ValueError("Missing scheme publication timestamp")
        if published >= limit:
            continue
        # Reuse the shared source, timestamp and numeric validation.
        validate_talent_observation({**row, "feature": "on_field_contribution"}, cutoff)
        key = (row["team"], row["feature"])
        previous = selected.get(key)
        if previous is None or published > _timestamp(previous["published_at"]):
            selected[key] = dict(row)
        elif published == _timestamp(previous["published_at"]) and row != previous:
            raise ValueError("Conflicting scheme observations at same timestamp")
    return selected
