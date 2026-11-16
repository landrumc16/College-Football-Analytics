"""V7 Milestone 1: verify CFBD /lines coverage against the verified results archive.

Research-only, read-only. Makes 20 CFBD calls (2016-2025 x regular/postseason) with
the existing CFBD_API_KEY secret and prints aggregate coverage, join quality, ATS/O-U
computability, spread-to-probability scale fit and a small hand-check sample.
Raw API responses are not written to disk, logs or artifacts (CFBD Terms s.5).
"""
import gzip
import json
import math
import os
import time
import urllib.request
from collections import Counter, defaultdict

API = "https://api.collegefootballdata.com/lines"
ALIASES = {"Miami": "Miami (FL)", "App State": "Appalachian State",
           "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}


def pick(row, *names):
    for n in names:
        if row.get(n) is not None:
            return row[n]
    return None


def fetch(year, season_type, key):
    req = urllib.request.Request(f"{API}?year={year}&seasonType={season_type}",
                                 headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def canon(name):
    return ALIASES.get(name, name)


def main():
    key = os.environ.get("CFBD_API_KEY", "")
    if not key:
        raise SystemExit("CFBD_API_KEY unavailable")
    archive = json.load(gzip.open("research/archive/verified/espn-games.json.gz"))
    by_id = {g["game_id"]: g for season in archive.values() for g in season}
    out = {"seasons": {}, "providers_by_season": {}, "hand_checks": [], "field_names_seen": set()}
    prob_rows = []
    for year in range(2016, 2026):
        games = []
        for st in ("regular", "postseason"):
            games += fetch(year, st, key)
            time.sleep(1)
        arch = [g for g in archive[str(year)] if g.get("fbs_participant")]
        arch_fbs = [g for g in arch if g.get("fbs_game")]
        s = Counter()
        providers = Counter()
        for g in games:
            out["field_names_seen"].update(g.keys())
            gid = str(pick(g, "id"))
            lines = g.get("lines") or []
            for ln in lines:
                out["field_names_seen"].update("line." + k for k in ln)
            a = by_id.get(gid)
            s["cfbd_games"] += 1
            s["cfbd_games_with_any_line"] += bool(lines)
            if not a:
                continue
            s["matched_archive"] += 1
            home, away = canon(pick(g, "homeTeam", "home_team")), canon(pick(g, "awayTeam", "away_team"))
            names_ok = {home, away} == {a["home"], a["away"]}
            s["team_names_agree"] += names_ok
            hs, as_ = pick(g, "homeScore", "home_score"), pick(g, "awayScore", "away_score")
            if hs is not None and as_ is not None:
                same = (hs, as_) == (a["home_score"], a["away_score"]) if home == a["home"] else (hs, as_) == (a["away_score"], a["home_score"])
                s["scores_compared"] += 1
                s["scores_agree"] += same
            if not lines:
                continue
            s["matched_with_line"] += 1
            s["matched_fbs_with_line"] += bool(a.get("fbs_game"))
            for ln in lines:
                providers[ln.get("provider")] += 1
            spreads = [ln for ln in lines if ln.get("spread") is not None]
            s["has_spread"] += bool(spreads)
            s["has_spread_open"] += any(pick(ln, "spreadOpen", "spread_open") is not None for ln in lines)
            s["has_total"] += any(pick(ln, "overUnder", "over_under") is not None for ln in lines)
            s["has_total_open"] += any(pick(ln, "overUnderOpen", "over_under_open") is not None for ln in lines)
            s["multi_provider"] += len({ln.get("provider") for ln in lines}) > 1
            if spreads and names_ok:
                cons = next((ln for ln in spreads if str(ln.get("provider")).lower() == "consensus"), spreads[0])
                spread = float(cons["spread"])  # CFBD convention: home spread, negative = home favourite
                ah, aa = (a["home_score"], a["away_score"])
                if home != a["home"]:
                    spread = -spread
                margin = ah - aa
                ats = margin + spread
                s["ats_computable"] += 1
                s["ats_push"] += ats == 0
                s["home_covers"] += ats > 0
                ou = pick(cons, "overUnder", "over_under")
                if ou is not None:
                    tot = ah + aa - float(ou)
                    s["ou_computable"] += 1
                    s["ou_push"] += tot == 0
                    s["overs"] += tot > 0
                if a.get("fbs_game") and margin != 0:
                    prob_rows.append((spread, 1 if margin > 0 else 0))
                    s["fav_straight_up"] += (spread < 0 and margin > 0) or (spread > 0 and margin < 0)
                    s["fav_games"] += spread != 0
            if "Texas Tech" in (home, away) and len(out["hand_checks"]) < 12 and year in (2016, 2020, 2025):
                out["hand_checks"].append({"season": year, "game_id": gid, "kickoff": a["kickoff"], "home": a["home"], "away": a["away"],
                                           "archive_score": f"{a['home_score']}-{a['away_score']}",
                                           "cfbd_score": f"{hs}-{as_}",
                                           "lines": [{"provider": ln.get("provider"), "spread": ln.get("spread"), "spreadOpen": pick(ln, "spreadOpen", "spread_open"),
                                                      "overUnder": pick(ln, "overUnder", "over_under"), "overUnderOpen": pick(ln, "overUnderOpen", "over_under_open")} for ln in lines]})
        s["archive_fbs_participant_games"] = len(arch)
        s["archive_fbs_vs_fbs_games"] = len(arch_fbs)
        out["seasons"][year] = dict(s)
        out["providers_by_season"][year] = dict(providers)
    # Spread -> win-probability scale: p(home) = 1/(1+10^(spread/scale)), as in model.py market_home_win_probability.
    def score(scale):
        b = l = 0.0
        for spread, y in prob_rows:
            p = 1 / (1 + 10 ** (spread / scale))
            p = min(max(p, 1e-6), 1 - 1e-6)
            b += (p - y) ** 2
            l -= y * math.log(p) + (1 - y) * math.log(1 - p)
        n = len(prob_rows)
        return round(b / n, 5), round(l / n, 5)
    grid = {sc: score(sc) for sc in [x / 2 for x in range(24, 61)]}
    best = min(grid, key=lambda k: grid[k][1])
    out["scale_fit"] = {"games": len(prob_rows), "current_19_5": grid[19.5], "best_logloss_scale": best, "best": grid[best],
                        "scale_15": grid[15.0], "scale_25": grid[25.0]}
    out["field_names_seen"] = sorted(out["field_names_seen"])
    os.makedirs("v7-evidence", exist_ok=True)
    with open("v7-evidence/cfbd-lines-summary.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
