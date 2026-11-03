"""Fetch multi-season recruiting classes for historical research, atomically.

Historical API retrieval does not establish original publication dates.
Never feed these snapshots into verified pregame accuracy calculations.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from .v34_recruiting_refresh import fetch_classes
from .v34_recruiting_ingestion import normalize_recruiting_classes


def refresh_history(years, output: Path, api_key: str):
    years = list(years)
    if not years or any(type(y) is not int or y < 2000 for y in years) or len(set(years)) != len(years):
        raise ValueError("Years must be distinct valid seasons")
    retrieved_at = datetime.now(timezone.utc).isoformat()
    collected = []
    counts = {}
    for year in sorted(years):
        classes = normalize_recruiting_classes(fetch_classes(year, api_key), retrieved_at=retrieved_at)
        if not classes:
            raise ValueError(f"Empty recruiting class response for {year}; preserving existing snapshot")
        collected.extend(classes)
        counts[str(year)] = len(classes)
    payload = {"seasons": sorted(years), "retrieved_at": retrieved_at,
               "source": "collegefootballdata.com/recruiting/teams",
               "historical_asof_verified": False,
               "class_counts_by_season": counts, "classes": collected}
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2) + "\\n", encoding="utf-8")
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    return counts
