"""Postseason games (conference championships filed as postseason, bowls, CFP) for event-driven publication.

  python -m cfb_analytics.postseason     # run by refresh-data.yml after the season report is rebuilt

Writes data/cfbd-2026-postseason.json (normalised CFBD rows, the watcher's calendar) and
web/public/postseason-2026.json (what the site shows). Predictions apply the existing official formula to the
published ratings: home rating - away rating + home edge (none at neutral sites), probability from the same
workbook logistic and scale (`model.model_home_margin`, `model.win_probability_from_rating_gap`). Postseason results
are published as results only and are not fed back into the ratings, so every model output is unchanged.

CFBD quota: CFBD lists no postseason games until bowls are announced, so the call is skipped before December unless
postseason games are already known. A failed call keeps the last good files.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from .ingestion import normalize_cfbd_games
from .model import model_home_margin, win_probability_from_rating_gap

SEASON = 2026
DATA = Path(f"data/cfbd-{SEASON}-postseason.json")
PUBLIC = Path(f"web/public/postseason-{SEASON}.json")
REPORT = Path(f"data/season-{SEASON}-report.json")
ALIASES = {"Miami": "Miami (FL)", "App State": "Appalachian State", "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}


def fetch(season, key):
    req = Request(f"https://api.collegefootballdata.com/games?year={season}&seasonType=postseason",
                  headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urlopen(req, timeout=45) as r:
        return json.load(r)


def should_fetch(now, existing):
    return now.month == 12 or now.month == 1 or bool(existing.get("games"))


def snapshot(raw, season, retrieved_at):
    notes = {int(r["id"]): (r.get("notes") or r.get("name") or "") for r in raw if isinstance(r, dict) and r.get("id") is not None}
    games = []
    for g in normalize_cfbd_games(raw, season):
        games.append({"game_id": int(g.game_id), "season": season, "week": g.week, "home": ALIASES.get(g.home, g.home),
                      "away": ALIASES.get(g.away, g.away), "completed": g.completed, "home_score": g.home_score,
                      "away_score": g.away_score, "neutral_site": g.neutral_site, "start_date": g.start_date,
                      "label": notes.get(int(g.game_id), "")})
    games.sort(key=lambda g: (g["start_date"] or "", g["game_id"]))
    return {"season": season, "season_type": "postseason", "source": "collegefootballdata.com/games?seasonType=postseason",
            "retrieved_at": retrieved_at, "games": games}


def public(snap, report):
    ratings = {r["team"]: r["rating"] for r in report["rankings"]}
    meta = report.get("model_metadata", {})
    edge, scale = meta.get("home_field_advantage", 3.0), meta.get("prediction_scale", 18.0)
    out = []
    for g in snap["games"]:
        row = {k: g[k] for k in ("game_id", "week", "home", "away", "neutral_site", "start_date", "label", "completed", "home_score", "away_score")}
        if not g["completed"] and g["home"] in ratings and g["away"] in ratings:
            margin = model_home_margin(ratings[g["home"]], ratings[g["away"]], neutral=g["neutral_site"], home_field_advantage=edge)
            p = win_probability_from_rating_gap(margin, scale)
            row["prediction"] = {"home_margin": round(margin, 2), "home_win_probability": round(p, 4),
                                 "predicted_winner": g["home"] if margin >= 0 else g["away"]}
        out.append(row)
    return {"season": snap["season"], "retrieved_at": snap["retrieved_at"], "ratings_from": report.get("retrieved_at"),
            "model_id": meta.get("model_id"), "games": out}


def main():
    now = datetime.now(timezone.utc)
    existing = json.loads(DATA.read_text()) if DATA.exists() else {}
    if not should_fetch(now, existing):
        print("postseason not scheduled yet; skipped (no CFBD call)")
        return
    try:
        raw = fetch(SEASON, os.environ.get("CFBD_API_KEY", ""))
    except Exception as error:                       # keep the last good files; football results are unaffected
        print(f"::warning::postseason refresh failed, keeping last good data: {str(error)[:200]}")
        return
    snap = snapshot(raw, SEASON, now.isoformat())
    if existing.get("games") and not snap["games"]:
        print("::warning::CFBD returned no postseason games after games were known; keeping last good data")
        return
    DATA.write_text(json.dumps(snap, indent=1) + "\n")
    PUBLIC.write_text(json.dumps(public(snap, json.loads(REPORT.read_text())), separators=(",", ":")) + "\n")
    print(f"postseason: {len(snap['games'])} games, {sum(g['completed'] for g in snap['games'])} final")


if __name__ == "__main__":
    main()
