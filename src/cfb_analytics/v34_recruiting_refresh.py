"""Fetch CFBD recruiting-team classes as a research snapshot, not pregame evidence.

Usage: CFBD_API_KEY=... python -m cfb_analytics.v34_recruiting_refresh --year 2026
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .v34_recruiting_ingestion import normalize_recruiting_classes


def fetch_classes(year, api_key):
    if not api_key:
        raise ValueError("CFBD_API_KEY required")
    url = "https://api.collegefootballdata.com/recruiting/teams?" + urlencode({"year": year})
    request = Request(url, headers={"Authorization": f"Bearer {api_key}",
                                    "Accept": "application/json"})
    with urlopen(request, timeout=45) as response:
        data = json.load(response)
    if not isinstance(data, list):
        raise ValueError("Unexpected recruiting response")
    return data


def refresh(year, output, api_key):
    raw = fetch_classes(year, api_key)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    classes = normalize_recruiting_classes(raw, retrieved_at=retrieved_at)
    if not classes:
        raise ValueError("Refusing empty recruiting snapshot")
    payload = {"year": year, "retrieved_at": retrieved_at,
               "source": "collegefootballdata.com/recruiting/teams",
               "historical_asof_verified": False, "classes": classes}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return len(classes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path("data") / f"cfbd-recruiting-{args.year}.json"
    print(json.dumps({"classes": refresh(args.year, output, os.getenv("CFBD_API_KEY", ""))}))


if __name__ == "__main__":
    main()
