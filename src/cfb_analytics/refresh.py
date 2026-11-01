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
    if not isinstance(raw, list):
        raise RuntimeError("Unexpected CFBD response: expected a list of games")
    games = normalize_cfbd_games(raw, season)
    summary = snapshot_summary(games)
    if any(row.get("season") != season for row in raw):
        raise RuntimeError("Unexpected cross-season records in CFBD response")
    eligible_ids = {row.get("id") for row in raw
                    if row.get("home_team") and row.get("away_team")}
    if len(eligible_ids) != summary["scheduled"]:
        raise RuntimeError("Unexpected games with known participants omitted during normalization")
    if summary["scheduled"] == 0:
        raise RuntimeError("Refusing to publish an empty season snapshot")
    payload = {
        "season": season,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": "collegefootballdata.com/games",
        "summary": summary,
        "games": [g.__dict__ for g in games],
    }
    # Record both the last successful check and the last actual data change.
    if output.exists():
        try:
            existing = json.loads(output.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            existing = None
        comparable = ({key: value for key, value in existing.items() if key not in ("retrieved_at", "data_changed_at")}
                      if isinstance(existing, dict) else None)
        incoming = {key: value for key, value in payload.items() if key != "retrieved_at"}
        if comparable == incoming:
            payload["data_changed_at"] = existing.get("data_changed_at", existing.get("retrieved_at", payload["retrieved_at"]))
        else:
            payload["data_changed_at"] = payload["retrieved_at"]
    else:
        payload["data_changed_at"] = payload["retrieved_at"]
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
