"""Strict as-of historical input contract for future multi-season evaluations.

This module validates external research rows. It never creates missing seasons,
guesses dates, or labels retrospective rows as genuine archived forecasts.
"""
from __future__ import annotations

from datetime import datetime, timezone


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp must be ISO-8601 text with UTC offset")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamp requires explicit UTC offset")
    return result.astimezone(timezone.utc)


def validate_historical_rows(rows: list[dict]) -> dict:
    """Validate games and pregame data availability, with explicit provenance.

    All timestamps are absolute instants. Pregame feature publication must be
    strictly earlier than kickoff; archived forecasts must also predate kickoff.
    Historical reconstructed predictions remain retrospective regardless of
    their source dates.
    """
    seen = set()
    seasons = set()
    kinds = {"retrospective": 0, "prospective": 0}
    for item in rows:
        required = ("season", "game_id", "week", "kickoff_at", "home", "away",
                    "home_score", "away_score", "source", "source_as_of",
                    "prediction_kind")
        missing = [key for key in required if key not in item]
        if missing:
            raise ValueError("Missing required historical fields: " + ", ".join(missing))
        if not isinstance(item["season"], int) or not isinstance(item["week"], int) or item["week"] < 1:
            raise ValueError("Invalid season/week")
        key = (item["season"], item["game_id"])
        if key in seen:
            raise ValueError("Duplicate historical game")
        seen.add(key)
        if not item["game_id"] or not item["home"] or not item["away"] or item["home"] == item["away"]:
            raise ValueError("Invalid team or game identifier")
        if not item["source"]:
            raise ValueError("Historical source required")
        if any(not isinstance(item[k], int) or item[k] < 0 for k in ("home_score", "away_score")):
            raise ValueError("Completed game scores must be nonnegative integers")
        if item["home_score"] == item["away_score"]:
            raise ValueError("Completed games cannot be tied")
        kickoff = parse_utc(item["kickoff_at"])
        if parse_utc(item["source_as_of"]) >= kickoff:
            raise ValueError("Source information was not available before kickoff")
        kind = item["prediction_kind"]
        if kind not in kinds:
            raise ValueError("Unknown prediction kind")
        if kind == "prospective":
            if not item.get("predicted_at") or not item.get("archive_id"):
                raise ValueError("Prospective forecasts require immutable archive provenance")
            if parse_utc(item["predicted_at"]) >= kickoff:
                raise ValueError("Forecast was not archived before kickoff")
        kinds[kind] += 1
        seasons.add(item["season"])
    return {"games": len(rows), "seasons": sorted(seasons), "prediction_kinds": kinds,
            "eligible_for_release": False,
            "reason": "Validation alone does not establish complete held-out cohorts or frozen model parity"}
