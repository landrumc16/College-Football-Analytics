"""Poll release polling: publish only complete, newly released verified rankings."""
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

CFP_DATES = {(11, 10), (11, 17), (11, 24), (12, 1), (12, 6)}

def release_window(now):
    local = now.astimezone(ZoneInfo("America/Chicago"))
    hour = local.hour + local.minute / 60
    if local.weekday() == 6 and 10.5 <= hour <= 16 and 8 <= local.month <= 12:
        return True
    if (local.month, local.day) in CFP_DATES and local.year == 2026:
        if local.weekday() == 6:
            return 10 <= hour <= 15
        return 17 <= hour <= 23
    return False

def choose_polls(weeks):
    # CFBD returns weekly records with polls, each containing ranked schools.
    candidates = {}
    for entry in weeks:
        if not isinstance(entry, dict) or entry.get("season") not in (None, 2026):
            continue
        week = entry.get("week")
        if not isinstance(week, int):
            continue
        for poll in entry.get("polls", []):
            name = str(poll.get("poll", "")).lower()
            key = ("ap_top25" if name in ("ap top 25", "ap") else
                   "coaches_top25" if "coaches" in name else
                   "cfp_top25" if "playoff" in name or name == "cfp" else None)
            if not key:
                continue
            rows = poll.get("ranks", [])
            if not isinstance(rows, list) or len(rows) != 25:
                continue
            cleaned = []
            for row in rows:
                rank, team = row.get("rank"), row.get("school")
                if not isinstance(rank, int) or not isinstance(team, str) or not team.strip():
                    break
                cleaned.append({"team": team.strip(), "rank": rank})
            if len(cleaned) != 25 or {r["rank"] for r in cleaned} != set(range(1, 26)):
                continue
            if key not in candidates or week > candidates[key][0]:
                candidates[key] = (week, cleaned)
    return candidates


def retained_verified_cfp(existing):
    """Retain a dated, sourced prior CFP publication; never date a new feed."""
    rows = existing.get("cfp_top25")
    try:
        published = date.fromisoformat(existing.get("cfp_published_at", ""))
    except (ValueError, TypeError):
        return {}
    if (published.year != 2026 or published > datetime.now(timezone.utc).date()
            or not str(existing.get("cfp_source", "")).startswith("https://")
            or not isinstance(rows, list) or len(rows) != 25
            or any(not isinstance(r, dict) or type(r.get("rank")) is not int
                   or not isinstance(r.get("team"), str) or not r["team"].strip() for r in rows)
            or {r["rank"] for r in rows} != set(range(1, 26))
            or len({r["team"] for r in rows}) != 25):
        return {}
    return {k: existing[k] for k in ("cfp_top25", "cfp_published_at", "cfp_source", "cfp_week") if k in existing}


def main():
    if os.getenv("GITHUB_EVENT_NAME") == "schedule" and not release_window(datetime.now(timezone.utc)):
        print("Outside verified announcement window")
        return
    api_key = os.environ["CFBD_API_KEY"]
    req = Request("https://api.collegefootballdata.com/rankings?year=2026&seasonType=regular",
                  headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    with urlopen(req, timeout=45) as response:
        weeks = json.load(response)
    if not isinstance(weeks, list):
        raise ValueError("Unexpected rankings response")
    found = choose_polls(weeks)
    path = Path("data/poll-2026-snapshot.json")
    existing = json.loads(path.read_text()) if path.exists() else {}
    output = {"season": 2026, "source": "CFBD rankings endpoint (2026 regular season)",
              "poll_weeks": {key: value[0] for key, value in found.items()}}
    for key, (week, rows) in found.items():
        output[key] = rows
    # Retain existing verified polls when the provider has not released the next poll.
    for key in ("ap_top25", "coaches_top25", "cfp_top25"):
        if key not in output and key in existing:
            output[key] = existing[key]
            output["poll_weeks"][key] = existing.get("poll_weeks", {}).get(key)
    if not found:
        print("No complete polls available; retaining last valid snapshot")
        return
    ap_week = output["poll_weeks"].get("ap_top25")
    coaches_week = output["poll_weeks"].get("coaches_top25")
    if ap_week is None or ap_week != coaches_week:
        print("AP and Coaches poll weeks not aligned; waiting for both")
        return
    output["week"] = ap_week
    # The CFBD weekly endpoint does not supply a verified CFP publication date.
    output.pop("cfp_top25", None)
    output["poll_weeks"].pop("cfp_top25", None)
    # CFBD's undated new CFP rows cannot replace an independently dated
    # publication. Keep its original date/week/source visibly intact.
    output.update(retained_verified_cfp(existing))
    if output != existing:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2) + "\n")
        print("New poll snapshot:", output["poll_weeks"])
    else:
        print("Polls unchanged")

if __name__ == "__main__":
    main()
