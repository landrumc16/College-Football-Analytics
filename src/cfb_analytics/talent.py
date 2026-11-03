"""Dated, source-backed talent inputs for prospective challenger research.

No missing feature is imputed to zero. This module does not alter the live model.
All dates must be timezone-aware and strictly before the prediction cutoff.
"""
from datetime import datetime, timezone
import math

ALLOWED = frozenset({
    "high_school_recruiting", "transfer_additions", "transfer_departures",
    "returning_production", "roster_experience", "on_field_contribution",
})


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp.astimezone(timezone.utc) if stamp.tzinfo else None


def validate_talent_observation(row, cutoff):
    """Reject future, undated, unverifiable, or malformed observations."""
    limit = _timestamp(cutoff)
    if limit is None:
        raise ValueError("Forecast cutoff must have an explicit timezone")
    if not isinstance(row, dict) or row.get("feature") not in ALLOWED:
        raise ValueError("Unknown talent feature")
    if not isinstance(row.get("team"), str) or not row["team"].strip():
        raise ValueError("Missing team")
    if not isinstance(row.get("source"), str) or not row["source"].strip():
        raise ValueError("Missing source provenance")
    observed = _timestamp(row.get("observed_at"))
    published = _timestamp(row.get("published_at"))
    if observed is None or published is None or observed > published or published >= limit:
        raise ValueError("Observation must be published before forecast cutoff")
    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Talent value must be finite and numeric")
    if row["feature"] == "returning_production" and not 0 <= value <= 1:
        raise ValueError("Returning production must be a fraction in [0,1]")
    if row["feature"] == "roster_experience" and value < 0:
        raise ValueError("Roster experience cannot be negative")
    return {key: row[key] for key in ("team", "feature", "value", "source", "observed_at", "published_at")}


def features_as_of(rows, cutoff):
    """Latest available observation per team/feature, with provenance retained.

    Records not yet published at the cutoff are unavailable, not backfilled.
    Contradictory records with identical timestamps are rejected.
    """
    selected = {}
    for row in rows:
        if _timestamp(row.get("published_at")) is None:
            raise ValueError("Missing timezone-aware publication time")
        if _timestamp(row["published_at"]) >= (_timestamp(cutoff) or datetime.min.replace(tzinfo=timezone.utc)):
            continue
        valid = validate_talent_observation(row, cutoff)
        key = (valid["team"], valid["feature"])
        old = selected.get(key)
        if old is None or _timestamp(valid["published_at"]) > _timestamp(old["published_at"]):
            selected[key] = valid
        elif _timestamp(valid["published_at"]) == _timestamp(old["published_at"]) and valid != old:
            raise ValueError("Conflicting same-time talent observations")
    return selected
