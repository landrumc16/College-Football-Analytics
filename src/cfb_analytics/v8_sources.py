"""V8 M1: CFBD source acquisition and per team-game derivation.

Fetches FBS membership, games, drives and plays from the CFBD API (existing CFBD_API_KEY) into a private
cache, then derives compact per team-game *counts* (never raw rows or play text) for public research use.
Only counts are published so every rate can be re-aggregated exactly over any window (season, last N games,
power-conference opponents only, or an as-of date).

Usage (CI only; needs CFBD_API_KEY):
  python -m cfb_analytics.v8_sources --seasons 2016-2026 --cache DIR [--refresh 2026] [--diagnose]
Offline re-derivation from a populated cache:
  python -m cfb_analytics.v8_sources --seasons 2016-2026 --cache DIR --offline
"""
import argparse
import gzip
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request
from .quota_client import urlopen

API = "https://api.collegefootballdata.com"
OUT = Path("research/v8")
SCHEMA_VERSION = 1

# Play classification (CFBD playType names). Sacks are pass plays (dropbacks).
RUSH = {"Rush", "Rushing Touchdown"}
PASS = {"Pass Reception", "Pass Incompletion", "Passing Touchdown", "Sack", "Pass Interception Return",
        "Interception Return Touchdown", "Pass Interception", "Interception", "Pass", "Pass Completion"}
FUMBLE = {"Fumble Recovery (Own)", "Fumble Recovery (Opponent)", "Fumble Return Touchdown"}
INTERCEPTION = {"Pass Interception Return", "Interception Return Touchdown", "Pass Interception", "Interception"}
TURNOVER = INTERCEPTION | {"Fumble Recovery (Opponent)", "Fumble Return Touchdown"}
EXPLOSIVE_RUSH, EXPLOSIVE_PASS = 10, 20  # yards; published definitions
GARBAGE = {2: 38, 3: 28, 4: 22}            # |score margin| above which a quarter's plays are garbage time
CLOSE_LATE_MARGIN = 8                       # 4th quarter (or OT) within one score


def pick(row, *names, default=None):
    for name in names:
        if isinstance(row, dict) and row.get(name) is not None:
            return row[name]
    return default


# ---------------------------------------------------------------- acquisition (CI only)

class Fetcher:
    def __init__(self, cache: Path, api_key: str | None, offline: bool, refresh: set[int]):
        self.cache, self.key, self.offline, self.refresh = cache, api_key, offline, refresh
        self.calls = 0
        cache.mkdir(parents=True, exist_ok=True)

    def get(self, path: str, season: int, force: bool | None = None, **params):
        name = path.strip("/").replace("/", "-") + "-" + "-".join(f"{k}{v}" for k, v in sorted(params.items()))
        file = self.cache / f"{name}.json.gz"
        stale = season in self.refresh if force is None else force
        if file.exists() and (self.offline or not stale):
            return json.loads(gzip.decompress(file.read_bytes()))
        if self.offline:
            raise FileNotFoundError(f"offline and not cached: {file.name}")
        if not self.key:
            raise SystemExit("CFBD_API_KEY is required to download")
        url = f"{API}{path}?{urlencode(params)}"
        for attempt in range(5):
            try:
                req = Request(url, headers={"Authorization": f"Bearer {self.key}", "Accept": "application/json"})
                with urlopen(req, timeout=120) as response:
                    data = json.load(response)
                break
            except HTTPError as error:
                if error.code in (429, 500, 502, 503, 504) and attempt < 4:
                    time.sleep(5 * (attempt + 1)); continue
                raise SystemExit(f"CFBD {path} {params}: HTTP {error.code}")
            except URLError:
                if attempt < 4:
                    time.sleep(5 * (attempt + 1)); continue
                raise
        self.calls += 1
        if not isinstance(data, list):
            raise SystemExit(f"CFBD {path} {params}: expected a list")
        file.write_bytes(gzip.compress(json.dumps(data, separators=(",", ":")).encode(), mtime=0))
        time.sleep(0.25)
        return data


def acquire(season: int, fetch: Fetcher):
    teams = fetch.get("/teams/fbs", season, year=season)
    games = []
    for kind in ("regular", "postseason"):
        games += [dict(g, seasonType=pick(g, "seasonType", "season_type", default=kind))
                  for g in fetch.get("/games", season, year=season, seasonType=kind)]
    fbs = {pick(t, "school") for t in teams}
    played = [g for g in games if pick(g, "completed") and (pick(g, "homeTeam", "home_team") in fbs
                                                        or pick(g, "awayTeam", "away_team") in fbs)]
    drives, plays = [], []
    for kind in ("regular", "postseason"):
        drives += fetch.get("/drives", season, year=season, seasonType=kind)
        weeks = sorted({pick(g, "week") for g in played if pick(g, "seasonType") == kind})
        for week in weeks:
            # In-season refresh: earlier weeks' plays are final; re-download only the latest two weeks.
            recent = season in fetch.refresh and week >= (weeks[-1] - 1)
            plays += fetch.get("/plays", season, force=recent if season in fetch.refresh else None,
                               year=season, week=week, seasonType=kind)
    return teams, games, drives, plays


# ---------------------------------------------------------------- derivation (pure, tested)

def is_garbage(period, margin):
    return period in GARBAGE and abs(margin) > GARBAGE[period]


def successful(down, distance, gained, touchdown):
    if touchdown:
        return True
    if down == 1:
        return gained >= 0.5 * distance
    if down == 2:
        return gained >= 0.7 * distance
    return gained >= distance


def empty_counts():
    return {k: 0 for k in (
        "plays", "yards", "succ", "expl", "ppa_n", "rush", "rush_yds", "rush_succ", "rush_expl", "rush_stuff",
        "db", "db_yds", "db_succ", "db_expl", "sacks", "third", "third_conv", "rz_trips", "rz_td", "rz_pts",
        "drives", "drive_pts", "drive_plays", "drive_secs", "late_plays", "late_succ", "turnovers")} | {"ppa": 0.0}


def offense_counts(game_plays, game_drives, team):
    """Offensive counts for one team in one game from scrimmage plays and drives (plain arithmetic)."""
    c = empty_counts()
    rz_drives = set()
    for p in game_plays:
        if pick(p, "offense") != team:
            continue
        kind = pick(p, "playType", "play_type", default="")
        down, distance = pick(p, "down"), pick(p, "distance")
        if kind not in RUSH | PASS | FUMBLE or down not in (1, 2, 3, 4) or distance is None:
            continue
        gained = pick(p, "yardsGained", "yards_gained", default=0) or 0
        period = pick(p, "period", default=0)
        margin = (pick(p, "offenseScore", "offense_score", default=0) or 0) - (pick(p, "defenseScore", "defense_score", default=0) or 0)
        touchdown = kind in ("Rushing Touchdown", "Passing Touchdown")
        turnover = kind in TURNOVER
        ok = successful(down, distance, gained, touchdown) and not turnover
        to_goal = pick(p, "yardsToGoal", "yards_to_goal")
        if to_goal is not None and to_goal <= 20 and pick(p, "driveId", "drive_id") is not None:
            rz_drives.add(str(pick(p, "driveId", "drive_id")))
        c["turnovers"] += turnover
        if down == 3:
            c["third"] += 1
            c["third_conv"] += (touchdown or gained >= distance) and not turnover
        if period >= 4 and abs(margin) <= CLOSE_LATE_MARGIN:
            c["late_plays"] += 1; c["late_succ"] += ok
        if is_garbage(period, margin):
            continue
        c["plays"] += 1; c["yards"] += gained; c["succ"] += ok
        ppa = pick(p, "ppa")
        if isinstance(ppa, (int, float)):
            c["ppa"] += float(ppa); c["ppa_n"] += 1
        if kind in RUSH:
            explosive = gained >= EXPLOSIVE_RUSH
            c["rush"] += 1; c["rush_yds"] += gained; c["rush_succ"] += ok
            c["rush_expl"] += explosive; c["rush_stuff"] += gained <= 0; c["expl"] += explosive
        elif kind in PASS:
            explosive = gained >= EXPLOSIVE_PASS
            c["db"] += 1; c["db_yds"] += gained; c["db_succ"] += ok
            c["db_expl"] += explosive; c["sacks"] += kind == "Sack"; c["expl"] += explosive
    for d in game_drives:
        if pick(d, "offense") != team:
            continue
        points = (pick(d, "endOffenseScore", "end_offense_score", default=0) or 0) - (pick(d, "startOffenseScore", "start_offense_score", default=0) or 0)
        points = max(points, 0)
        elapsed = pick(d, "elapsed", default={}) or {}
        c["drives"] += 1; c["drive_pts"] += points; c["drive_plays"] += pick(d, "plays", default=0) or 0
        c["drive_secs"] += 60 * (elapsed.get("minutes") or 0) + (elapsed.get("seconds") or 0)
        start_goal = pick(d, "startYardsToGoal", "start_yards_to_goal")
        if str(pick(d, "id")) in rz_drives or (start_goal is not None and start_goal <= 20):
            c["rz_trips"] += 1; c["rz_pts"] += points; c["rz_td"] += points >= 6
    c["ppa"] = round(c["ppa"], 4)
    return c


def derive_season(season, teams, games, drives, plays):
    """Per team-game rows for every completed game involving an FBS team (both sides), plus membership."""
    membership = {pick(t, "school"): pick(t, "conference") for t in teams if pick(t, "school")}
    plays_by_game, drives_by_game = defaultdict(list), defaultdict(list)
    for p in plays:
        plays_by_game[str(pick(p, "gameId", "game_id"))].append(p)
    for d in drives:
        drives_by_game[str(pick(d, "gameId", "game_id"))].append(d)
    rows = []
    for g in sorted(games, key=lambda g: (pick(g, "startDate", "start_date", default=""), str(pick(g, "id")))):
        home, away = pick(g, "homeTeam", "home_team"), pick(g, "awayTeam", "away_team")
        hp, ap = pick(g, "homePoints", "home_points"), pick(g, "awayPoints", "away_points")
        if not pick(g, "completed") or hp is None or ap is None or not (home in membership or away in membership):
            continue
        gid = str(pick(g, "id"))
        gp, gd = plays_by_game.get(gid, []), drives_by_game.get(gid, [])
        neutral = bool(pick(g, "neutralSite", "neutral_site", default=False))
        for team, opp, pf, pa, side in ((home, away, hp, ap, "home"), (away, home, ap, hp, "away")):
            rows.append({
                "game_id": gid, "season": season, "week": pick(g, "week"), "season_type": pick(g, "seasonType"),
                "date": pick(g, "startDate", "start_date"), "team": team, "opp": opp,
                "site": "neutral" if neutral else side,
                "team_conf": membership.get(team) or pick(g, f"{side}Conference", f"{side}_conference"),
                "opp_conf": membership.get(opp) or pick(g, ("away" if side == "home" else "home") + "Conference"),
                "team_fbs": team in membership, "opp_fbs": opp in membership,
                "pf": pf, "pa": pa, "has_plays": bool(gp), "has_drives": bool(gd),
                "off": offense_counts(gp, gd, team) if gp else None,
            })
    return membership, rows


def write_gz(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(), mtime=0))


def coverage(season, rows):
    fbs_games = {r["game_id"] for r in rows if r["team_fbs"]}
    with_plays = {r["game_id"] for r in rows if r["team_fbs"] and r["has_plays"]}
    with_drives = {r["game_id"] for r in rows if r["team_fbs"] and r["has_drives"]}
    return {"season": season, "completed_games": len(fbs_games), "games_with_plays": len(with_plays),
            "games_with_drives": len(with_drives),
            "team_games": sum(r["team_fbs"] for r in rows),
            "team_games_with_plays": sum(r["team_fbs"] and r["has_plays"] for r in rows)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2016-2026")
    ap.add_argument("--cache", required=True, type=Path)
    ap.add_argument("--refresh", default="", help="comma-separated seasons to re-download (in-season)")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--diagnose", action="store_true", help="print response field names only (no values)")
    args = ap.parse_args(argv)
    first, _, last = args.seasons.partition("-")
    seasons = list(range(int(first), int(last or first) + 1))
    fetch = Fetcher(args.cache, os.environ.get("CFBD_API_KEY"), args.offline,
                    {int(s) for s in args.refresh.split(",") if s.strip()})
    # A partial run (e.g. the in-season refresh of one season) updates only its seasons in the shared records.
    membership_path, receipt_path = OUT / "fbs-membership.json", OUT / "sources-receipt.json"
    membership_all = json.loads(membership_path.read_text()) if membership_path.exists() else {}
    previous = json.loads(receipt_path.read_text()).get("coverage", []) if receipt_path.exists() else []
    manifest = []
    for season in seasons:
        teams, games, drives, plays = acquire(season, fetch)
        if args.diagnose:
            for label, data in (("teams", teams), ("games", games), ("drives", drives), ("plays", plays)):
                keys = sorted({k for row in data[:200] for k in row}) if data else []
                print(f"{season} {label}: {len(data)} rows; fields={keys}")
            kinds = defaultdict(int)
            for p in plays:
                kinds[pick(p, "playType", "play_type")] += 1
            print(f"{season} playType counts: {dict(sorted(kinds.items(), key=lambda kv: -kv[1]))}")
        membership, rows = derive_season(season, teams, games, drives, plays)
        membership_all[str(season)] = dict(sorted(membership.items()))
        write_gz(OUT / "team-games" / f"{season}.json.gz", {"schema_version": SCHEMA_VERSION, "season": season, "rows": rows})
        manifest.append(coverage(season, rows))
        print(json.dumps(manifest[-1]))
    membership_path.write_text(json.dumps(membership_all, indent=1, sort_keys=True) + "\n")
    manifest = sorted([c for c in previous if c["season"] not in seasons] + manifest, key=lambda c: c["season"])
    receipt = {"schema_version": SCHEMA_VERSION, "source": "CollegeFootballData API (api.collegefootballdata.com)",
               "endpoints": ["/teams/fbs", "/games", "/drives", "/plays"],
               "derived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "published": "per team-game offensive counts only; raw rows and play text stay private",
               "definitions": {"garbage_time": {f"Q{k}": f"|margin|>{v}" for k, v in GARBAGE.items()},
                               "explosive": {"rush_yards": EXPLOSIVE_RUSH, "pass_yards": EXPLOSIVE_PASS},
                               "close_late": f"4th quarter or OT, |margin|<={CLOSE_LATE_MARGIN}",
                               "success": "1st down 50%, 2nd 70%, 3rd/4th 100% of distance; touchdowns succeed; turnovers fail"},
               "coverage": manifest}
    receipt_path.write_text(json.dumps(receipt, indent=1) + "\n")
    print(f"api_calls={fetch.calls}")


if __name__ == "__main__":
    main()
