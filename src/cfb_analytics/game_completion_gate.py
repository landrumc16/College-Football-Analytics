"""Gate frequent football refreshes on newly final CFBD games.

Daily baseline and manual runs always proceed. Polling runs only rebuild when a
previously pending game becomes final; failed API checks fail the workflow closed.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .refresh import fetch_cfbd_games
from .ingestion import normalize_cfbd_games


def should_refresh(event: str, schedule: str, snapshot: dict, raw: list[dict], now: datetime) -> tuple[bool, str]:
    if event != "schedule" or schedule == "23 11 * * *":
        return True, "baseline/manual"
    local_today = now.astimezone(ZoneInfo("America/Chicago")).date()
    pending = {}
    for game in snapshot["games"]:
        kickoff = game.get("start_date")
        if game.get("completed") or not kickoff:
            continue
        try:
            start = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
            local_start = start.astimezone(ZoneInfo("America/Chicago")).date()
        except (ValueError, TypeError):
            continue
        # Retain previous-day games for late-night and delayed final reports.
        if local_today - timedelta(days=1) <= local_start <= local_today:
            pending[int(game["game_id"])] = game
    if not pending:
        return False, "no pending games from today or yesterday"
    updated = {game.game_id: game for game in normalize_cfbd_games(raw, snapshot["season"])}
    newly_final = [gid for gid in pending if gid in updated and updated[gid].completed]
    return bool(newly_final), f"new final games: {newly_final}" if newly_final else "no newly final games"


def main():
    event = os.environ["EVENT_NAME"]
    schedule = os.environ.get("SCHEDULE", "")
    if event != "schedule" or schedule == "23 11 * * *":
        run, reason = True, "baseline/manual"
    else:
        snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
        # Avoid calling the API if no eligible games exist.
        now = datetime.now(timezone.utc)
        run, reason = should_refresh(event, schedule, snapshot, [], now)
        if reason != "no pending games from today or yesterday":
            raw = fetch_cfbd_games(2026, os.environ["CFBD_API_KEY"])
            run, reason = should_refresh(event, schedule, snapshot, raw, now)
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        print(f"run_refresh={str(run).lower()}", file=output)
    print(reason)


if __name__ == "__main__":
    main()
