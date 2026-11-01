"""Fetch CFBD season games and publish an atomic validated JSON snapshot.

Usage: CFBD_API_KEY=... python -m cfb_analytics.refresh --season 2026
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from .ingestion import normalize_cfbd_games, snapshot_summary


def fetch_cfbd_games(season: int, api_key: str):
    if not api_key:
        raise ValueError("CFBD_API_KEY is required")
    url = f"https://api.collegefootballdata.com/games?year={season}&seasonType=regular"
    req = Request(url, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    with urlopen(req, timeout=45) as response:
        return json.load(response)


def refresh(season: int, output: Path, api_key: str):
    raw = fetch_cfbd_games(season, api_key)
    games = normalize_cfbd_games(raw, season)
    summary = snapshot_summary(games)
    if summary["scheduled"] == 0:
        raise RuntimeError("Refusing to publish an empty season snapshot")
    payload = {
        "season": season,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": "collegefootballdata.com/games",
        "summary": summary,
        "games": [g.__dict__ for g in games],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path("data") / f"cfbd-{args.season}-games.json"
    print(json.dumps(refresh(args.season, output, os.getenv("CFBD_API_KEY", ""))))


if __name__ == "__main__":
    main()
