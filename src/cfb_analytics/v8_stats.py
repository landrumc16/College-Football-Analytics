"""V8 M2: offense/defense statistics from derived per team-game counts.

Views (every number carries its sample size):
  raw       all games played (FCS opponents included and counted separately)
  power     games against power-conference opponents only (competition filter, not a strength rating);
            power = ACC, Big Ten, Big 12, SEC, plus Pac-12 through 2023, plus independent Notre Dame
  adjusted  all-FBS opponent-adjusted rating from a weighted ridge fit of
            game value = mean + offense(team) + defense(opponent) + home-field * site,
            solved jointly so schedule strength is counted once; shrinkage protects small samples.
            FCS games are excluded from the fit (poorly connected).
Trends and volatility use opponent-adjusted game values: value minus what an average unit would be expected
to record against that opponent at that site. A trend is labelled only when it exceeds 1.645 standard errors.
All functions accept an as-of cutoff and never read games on or after it.
"""
import argparse
import gzip
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("research/v8")

POWER_THROUGH_2023 = {"ACC", "Big Ten", "Big 12", "SEC", "Pac-12"}
POWER_FROM_2024 = {"ACC", "Big Ten", "Big 12", "SEC"}
POWER_INDEPENDENTS = {"Notre Dame"}

# key: (label, numerator, denominator, offense higher is better, ridge prior in denominator units, group)
METRICS = {
    "ppd": ("Points per drive", "drive_pts", "drives", True, 25, "scoring"),
    "ypp": ("Yards per play", "yards", "plays", True, 150, "efficiency"),
    "sr": ("Success rate", "succ", "plays", True, 150, "efficiency"),
    "epa": ("Expected points added per play", "ppa", "ppa_n", True, 150, "efficiency"),
    "expl": ("Explosive play rate", "expl", "plays", True, 150, "efficiency"),
    "rush_ypc": ("Yards per carry", "rush_yds", "rush", True, 80, "rushing"),
    "rush_sr": ("Rushing success rate", "rush_succ", "rush", True, 80, "rushing"),
    "rush_expl": ("Explosive run rate (10+ yards)", "rush_expl", "rush", True, 80, "rushing"),
    "stuff": ("Run stuff rate (no gain or loss)", "rush_stuff", "rush", False, 80, "rushing"),
    "pass_ypd": ("Yards per dropback", "db_yds", "db", True, 80, "passing"),
    "pass_sr": ("Passing success rate", "db_succ", "db", True, 80, "passing"),
    "pass_expl": ("Explosive pass rate (20+ yards)", "db_expl", "db", True, 80, "passing"),
    "sack": ("Sack rate", "sacks", "db", False, 80, "passing"),
    "third": ("Third-down conversion rate", "third_conv", "third", True, 40, "situational"),
    "rz_td": ("Red-zone touchdown rate", "rz_td", "rz_trips", True, 12, "situational"),
    "rz_pts": ("Points per red-zone trip", "rz_pts", "rz_trips", True, 12, "situational"),
    "late": ("Close-game 4th-quarter success rate", "late_succ", "late_plays", True, 60, "situational"),
    "to": ("Turnovers per drive", "turnovers", "drives", False, 25, "situational"),
}
TREND_KEYS = ("epa", "sr", "ppd")
MIN_GAMES_VOLATILITY = 5


def power_conferences(season: int):
    return POWER_THROUGH_2023 if season <= 2023 else POWER_FROM_2024


def is_power(team: str, conference: str | None, season: int) -> bool:
    return team in POWER_INDEPENDENTS or conference in power_conferences(season)


def load_rows(season: int, root: Path = ROOT):
    return json.loads(gzip.decompress((root / "team-games" / f"{season}.json.gz").read_bytes()))["rows"]


def before(rows, as_of):
    """Rows strictly before the cutoff (ISO date or datetime string); None keeps all."""
    return rows if not as_of else [r for r in rows if (r.get("date") or "") < as_of]


def pair_units(rows):
    """[(team, opp, site, off_counts, def_counts, row)] for rows whose game has counts on both sides."""
    by_game = defaultdict(dict)
    for r in rows:
        by_game[r["game_id"]][r["team"]] = r
    units = []
    for r in rows:
        other = by_game[r["game_id"]].get(r["opp"])
        if r.get("off") and other and other.get("off"):
            units.append((r["team"], r["opp"], r["site"], r["off"], other["off"], r))
    return units


def ratio(num, den):
    return num / den if den else None


def aggregate(units, metric, side):
    """Sum numerator/denominator over a team's units; side 'off' or 'def'. Returns (value, denominator, games)."""
    _, num, den, *_ = METRICS[metric]
    n = d = 0.0
    games = 0
    for unit in units:
        counts = unit[3] if side == "off" else unit[4]
        if counts.get(den):
            n += counts[num]; d += counts[den]; games += 1
    return ratio(n, d), d, games


def site_sign(site):
    return 1 if site == "home" else -1 if site == "away" else 0


def adjust(units, metric, iterations=200):
    """Weighted ridge opponent adjustment. Returns dict with mean, home, off{team}, def{team}, se, residual sd."""
    _, num, den, _, prior, _ = METRICS[metric]
    obs = [(t, o, site_sign(s), off[num] / off[den], off[den]) for t, o, s, off, _d, row in units
           if off.get(den) and row["team_fbs"] and row["opp_fbs"]]
    if not obs:
        return None
    teams = sorted({t for t, *_ in obs} | {o for _, o, *_ in obs})
    off_r, def_r = dict.fromkeys(teams, 0.0), dict.fromkeys(teams, 0.0)
    wsum = sum(w for *_, w in obs)
    mean = sum(v * w for *_, v, w in obs) / wsum
    home = 0.0
    by_off, by_def = defaultdict(list), defaultdict(list)
    for item in obs:
        by_off[item[0]].append(item); by_def[item[1]].append(item)
    for _ in range(iterations):
        for t in teams:
            items = by_off.get(t, [])
            off_r[t] = sum(w * (v - mean - def_r[o] - home * h) for _, o, h, v, w in items) / (sum(w for *_, w in items) + prior)
        for o in teams:
            items = by_def.get(o, [])
            def_r[o] = sum(w * (v - mean - off_r[t] - home * h) for t, _, h, v, w in items) / (sum(w for *_, w in items) + prior)
        hw = sum(w * h * h for _, _, h, _, w in obs)
        home = sum(w * h * (v - mean - off_r[t] - def_r[o]) for t, o, h, v, w in obs) / hw if hw else 0.0
        mean = sum(w * (v - off_r[t] - def_r[o] - home * h) for t, o, h, v, w in obs) / wsum
    resid2 = sum(w * (v - mean - off_r[t] - def_r[o] - home * h) ** 2 for t, o, h, v, w in obs)
    unit_var = resid2 / len(obs)  # variance of a one-unit-weight observation
    off_w = {t: sum(w for *_, w in by_off.get(t, [])) for t in teams}
    def_w = {t: sum(w for *_, w in by_def.get(t, [])) for t in teams}
    return {"mean": mean, "home": home, "off": off_r, "def": def_r,
            "off_se": {t: math.sqrt(unit_var / (off_w[t] + prior)) for t in teams},
            "def_se": {t: math.sqrt(unit_var / (def_w[t] + prior)) for t in teams},
            "off_w": off_w, "def_w": def_w}


def game_adjusted(unit, metric, fit, side):
    """One game's opponent-adjusted value: actual minus an average unit's expectation vs this opponent/site."""
    _, num, den, *_ = METRICS[metric]
    team, opp, site, off, dfn, row = unit
    counts = off if side == "off" else dfn
    if not counts.get(den) or not (row["team_fbs"] and row["opp_fbs"]) or fit is None:
        return None
    h = site_sign(site)
    if side == "off":
        expected = fit["mean"] + fit["def"].get(opp, 0.0) + fit["home"] * h
    else:
        expected = fit["mean"] + fit["off"].get(opp, 0.0) - fit["home"] * h
    return counts[num] / counts[den] - expected


def mean_sd(values):
    if not values:
        return None, None
    m = sum(values) / len(values)
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1)) if len(values) > 1 else None
    return m, sd


def trend(values, window):
    """Recent-window mean minus full-season mean of game-adjusted values, with a 1.645-SE label rule."""
    if len(values) < window + 2:
        return None
    season_mean, sd = mean_sd(values)
    recent = values[-window:]
    recent_mean = sum(recent) / window
    earlier = values[:-window]
    se = sd * math.sqrt(1 / window + 1 / len(earlier)) if sd else None
    diff = recent_mean - sum(earlier) / len(earlier)
    label = "steady" if not se or abs(diff) <= 1.645 * se else ("improving" if diff > 0 else "declining")
    return {"recent": round(recent_mean, 4), "season": round(season_mean, 4), "change": round(diff, 4),
            "se": round(se, 4) if se else None, "label": label, "games": window}


def rank(values, higher_better):
    order = sorted((v, t) for t, v in values.items() if v is not None)
    if higher_better:
        order.reverse()
    out, previous, position = {}, None, 0
    for index, (value, team) in enumerate(order, 1):
        if value != previous:
            position, previous = index, value
        out[team] = position
    return out


def team_stats(rows, season, as_of=None):
    """Complete offense/defense profile for every FBS team, using only games before as_of."""
    rows = before(rows, as_of)
    units = pair_units(rows)
    fbs = sorted({r["team"] for r in rows if r["team_fbs"]})
    conf = {r["team"]: r["team_conf"] for r in rows if r["team_fbs"]}
    power = {t for t in fbs if is_power(t, conf.get(t), season)}
    mine = defaultdict(list)
    for u in units:
        mine[u[0]].append(u)
    for t in mine:
        mine[t].sort(key=lambda u: (u[5].get("date") or "", u[5]["game_id"]))
    played = defaultdict(list)
    for r in rows:
        played[r["team"]].append(r)
    fits = {m: adjust(units, m) for m in METRICS}
    out = {t: {"conference": conf.get(t), "power": t in power,
               "games": len(played[t]), "fcs_games": sum(not r["opp_fbs"] for r in played[t]),
               "games_with_play_data": len(mine[t]),
               "power_games": sum(is_power(u[1], u[5]["opp_conf"], season) for u in mine[t]),
               "points_per_game": round(sum(r["pf"] for r in played[t]) / len(played[t]), 2) if played[t] else None,
               "points_allowed_per_game": round(sum(r["pa"] for r in played[t]) / len(played[t]), 2) if played[t] else None,
               "offense": {}, "defense": {}, "trend": {}, "volatility": {}} for t in fbs}
    for m, (label, num, den, higher, prior, group) in METRICS.items():
        fit = fits[m]
        for side in ("off", "def"):
            better_high = higher if side == "off" else not higher
            raw, p4, adj = {}, {}, {}
            for t in fbs:
                value, d, games = aggregate(mine[t], m, side)
                pvalue, pd, pgames = aggregate([u for u in mine[t] if is_power(u[1], u[5]["opp_conf"], season)], m, side) if t in power else (None, 0, 0)
                a = None
                if fit and t in fit["off"]:
                    a = fit["mean"] + (fit["off"][t] if side == "off" else fit["def"][t])
                raw[t], p4[t], adj[t] = value, pvalue, a
                entry = {"raw": round(value, 4) if value is not None else None, "n": d, "games": games,
                         "power": round(pvalue, 4) if pvalue is not None else None, "power_n": pd, "power_games": pgames,
                         "adjusted": round(a, 4) if a is not None else None,
                         "se": round(fit[f"{side}_se"][t], 4) if fit and t in fit[f"{side}_se"] else None}
                out[t]["offense" if side == "off" else "defense"][m] = entry
            for view, values, pool in (("raw", raw, fbs), ("power", p4, power), ("adjusted", adj, fbs)):
                ranks = rank({t: values[t] for t in pool}, better_high)
                for t in fbs:
                    out[t]["offense" if side == "off" else "defense"][m][f"{view}_rank"] = ranks.get(t)
    for t in fbs:
        for m in TREND_KEYS:
            for side in ("off", "def"):
                values = [v for v in (game_adjusted(u, m, fits[m], side) for u in mine[t]) if v is not None]
                if side == "def":
                    values = [-v for v in values]  # positive = better defense
                key = f"{'offense' if side == 'off' else 'defense'}_{m}"
                out[t]["trend"][key] = {"last3": trend(values, 3), "last4": trend(values, 4)}
                m_, sd = mean_sd(values)
                out[t]["volatility"][key] = ({"sd": round(sd, 4), "games": len(values)}
                                             if sd is not None and len(values) >= MIN_GAMES_VOLATILITY else None)
    league = {m: {"mean": round(f["mean"], 4), "home": round(f["home"], 4)} for m, f in fits.items() if f}
    return {"season": season, "as_of": as_of, "teams": out, "league": league,
            "power_conferences": sorted(power_conferences(season)) + sorted(POWER_INDEPENDENTS),
            "power_teams": len(power), "fbs_teams": len(fbs)}


def definitions():
    return {m: {"label": label, "numerator": num, "denominator": den, "offense_higher_is_better": higher,
                "prior": prior, "group": group} for m, (label, num, den, higher, prior, group) in METRICS.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    stats = team_stats(load_rows(args.season), args.season, args.as_of)
    stats["definitions"] = definitions()
    stats["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = args.out or ROOT / f"team-stats-{args.season}.json"
    out.write_text(json.dumps(stats, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"{out}: {stats['fbs_teams']} FBS teams, {stats['power_teams']} power teams")


if __name__ == "__main__":
    main()
