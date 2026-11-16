"""V7 Milestone 2: historical market archive (CFBD closing spreads and totals).

Joins CFBD /lines to the verified results archive by game ID, selects one provider
per game and market with a deterministic, versioned policy, computes ATS and
over/under results, and publishes **derived team statistics only**.

Licensing boundary (CFBD Terms ss.4-5): raw responses, provider-level lines and
selected per-game lines stay private (runner workspace or the gitignored --cache).
Public outputs contain counts, W/L/P letters and rounded averages over at least
MIN_AVG_GAMES games, never per-game line values or cover margins.

Usage:
  CFBD_API_KEY=... python -m cfb_analytics.v7_market_archive --backfill 2016-2025
  CFBD_API_KEY=... python -m cfb_analytics.v7_market_archive --season 2026
  python -m cfb_analytics.v7_market_archive --check --cache .cache/v7-cfbd-lines
"""
import argparse
import gzip
import hashlib
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .forecast_ledger import ALIASES, aware_utc
from .refresh import fetch_cfbd_lines

POLICY_VERSION = 2
SCHEMA_VERSION = 1
DISPUTE_POINTS = 3.0
MIN_AVG_GAMES = 5
SEASON_TYPES = ("regular", "postseason")
PROVIDER_PRIORITY = ("consensus", "DraftKings", "ESPN Bet", "Bovada", "William Hill (New Jersey)",
                     "Caesars", "Caesars Sportsbook (Colorado)", "Caesars (Pennsylvania)",
                     "teamrankings", "numberfire", "SugarHouse")
ATTRIBUTION = "Data provided by CollegeFootballData.com"
SOURCE = "CollegeFootballData.com /lines"
ARCHIVE = Path("research/archive/verified/espn-games.json.gz")
CURRENT_GAMES = Path("data/cfbd-2026-games.json")
CURRENT_REPORT = Path("data/season-2026-report.json")
RECEIPTS = Path("data/v7-market-receipts.json")
PUBLIC = Path("web/public/v7-team-market-history.json")
DEFAULT_CACHE = Path(".cache/v7-cfbd-lines")
# Per completed season (docs/V7-M2-IMPLEMENTATION-PLAN.md s.8).
THRESHOLDS = {"matched": 0.99, "spread": 0.98, "total": 0.85, "disputed": 0.05, "truncation": 0.90}


class ArchiveRejected(RuntimeError):
    """Validation failure; outputs are not written and last-good files remain."""


# ---------------------------------------------------------------- source handling
def canonical_bytes(rows):
    return json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def acquire(season, season_type, key, cache, prior_receipt, *, offline=False, accept_upstream=False, fetch=fetch_cfbd_lines):
    """Return (rows, receipt). Detects upstream changes and truncation before acceptance."""
    path = Path(cache) / f"{season}-{season_type}.json" if cache else None
    if path and path.exists():
        data = path.read_bytes()
        rows = json.loads(data)
        retrieved_at = json.loads((path.with_suffix(".meta.json")).read_text())["retrieved_at"]
        data = canonical_bytes(rows)
    elif offline:
        raise ArchiveRejected(f"missing private snapshot {season}-{season_type}")
    else:
        rows = fetch(season, season_type, key)
        if not isinstance(rows, list):
            raise ArchiveRejected(f"unexpected CFBD response for {season} {season_type}")
        data = canonical_bytes(rows)
        retrieved_at = datetime.now(timezone.utc).isoformat()
    receipt = {"retrieved_at": retrieved_at, "sha256": sha256(data), "rows": len(rows)}
    if prior_receipt:
        if prior_receipt.get("rows") and len(rows) < THRESHOLDS["truncation"] * prior_receipt["rows"]:
            raise ArchiveRejected(f"truncated response {season} {season_type}: {len(rows)} < 90% of {prior_receipt['rows']}")
        if prior_receipt["sha256"] != receipt["sha256"]:
            if not accept_upstream:
                raise ArchiveRejected(f"upstream change {season} {season_type}: rows {prior_receipt['rows']} -> {len(rows)}; "
                                      "re-run with --accept-upstream-change after review")
        else:
            receipt["retrieved_at"] = prior_receipt["retrieved_at"]  # unchanged bytes keep provenance and determinism
    if path and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.with_suffix(".meta.json").write_text(json.dumps({"retrieved_at": retrieved_at, "sha256": receipt["sha256"]}))
    return rows, receipt


# ---------------------------------------------------------------- results (authoritative)
def historical_results(seasons, archive=ARCHIVE):
    data = json.loads(gzip.decompress(Path(archive).read_bytes()))
    out = {}
    for season in seasons:
        for g in data[str(season)]:
            if g.get("fbs_participant"):
                out[str(g["game_id"])] = {"game_id": str(g["game_id"]), "season": season, "season_type": g.get("season_type"),
                                          "kickoff": g["kickoff"], "home": g["home"], "away": g["away"],
                                          "home_score": g["home_score"], "away_score": g["away_score"],
                                          "neutral_site": bool(g.get("neutral_site")), "completed": True}
    return out


def current_results(season, games_path=CURRENT_GAMES, report_path=CURRENT_REPORT, now=None):
    snap = json.loads(Path(games_path).read_text())
    fbs = {t["team"] for t in json.loads(Path(report_path).read_text())["rankings"]}
    now = now or datetime.now(timezone.utc)
    out = {}
    for g in snap["games"]:
        # The snapshot keeps raw CFBD names; canonicalize exactly as pipeline.py does before reporting.
        g = {**g, "home": ALIASES.get(g["home"], g["home"]), "away": ALIASES.get(g["away"], g["away"])}
        if g.get("season", season) != season or not (g["home"] in fbs or g["away"] in fbs):
            continue
        kickoff = aware_utc(g.get("start_date"))
        # No future leakage: only completed games whose kickoff is in the past count.
        completed = bool(g.get("completed")) and kickoff is not None and kickoff < now \
            and g.get("home_score") is not None and g.get("away_score") is not None
        out[str(g["game_id"])] = {"game_id": str(g["game_id"]), "season": season, "season_type": "regular",
                                  "kickoff": g.get("start_date"), "home": g["home"], "away": g["away"],
                                  "home_score": g.get("home_score"), "away_score": g.get("away_score"),
                                  "neutral_site": bool(g.get("neutral_site")), "completed": completed}
    return out


# ---------------------------------------------------------------- normalize and join
def _num(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return "invalid"
    return x if math.isfinite(x) else "invalid"


def normalize(rows):
    """Provider-level records keyed by game ID. Identical duplicates collapse; conflicting ones are flagged."""
    games, conflicts = {}, set()
    for row in rows:
        gid = str(row.get("id"))
        game = games.setdefault(gid, {"game_id": gid, "home": row.get("homeTeam"), "away": row.get("awayTeam"),
                                      "home_score": row.get("homeScore"), "away_score": row.get("awayScore"), "providers": {}})
        for line in row.get("lines") or []:
            provider = line.get("provider")
            rec = {"spread": _num(line.get("spread")), "spread_open": _num(line.get("spreadOpen")),
                   "total": _num(line.get("overUnder")), "total_open": _num(line.get("overUnderOpen")),
                   "formatted_spread": line.get("formattedSpread")}
            prior = game["providers"].get(provider)
            if prior is not None and prior != rec:
                conflicts.add(gid)
            game["providers"][provider] = rec
    return games, conflicts


def orient(game, result):
    """Return +1 if CFBD home equals archive home, -1 if swapped. Raise on identity or score mismatch."""
    home, away = ALIASES.get(game["home"], game["home"]), ALIASES.get(game["away"], game["away"])
    if (home, away) == (result["home"], result["away"]):
        sign, hs, as_ = 1, game["home_score"], game["away_score"]
    elif (home, away) == (result["away"], result["home"]):
        sign, hs, as_ = -1, game["away_score"], game["home_score"]
    else:
        raise ArchiveRejected(f"team identity mismatch for game {result['game_id']}")
    if result["completed"] and hs is not None and as_ is not None and (hs, as_) != (result["home_score"], result["away_score"]):
        raise ArchiveRejected(f"final score mismatch for game {result['game_id']}")
    return sign


def _priority(provider):
    return (PROVIDER_PRIORITY.index(provider), "") if provider in PROVIDER_PRIORITY else (len(PROVIDER_PRIORITY), str(provider))


def _half_point(x):
    return abs(x * 2 - round(x * 2)) < 1e-9


def _favored_name_conflict(formatted, spread, home, away):
    """True when formattedSpread names the opposite favourite. Matches the full team name followed by the number,
    trying the longer name first so 'Texas Tech -3' is never read as 'Texas'."""
    if not formatted or spread == 0:
        return False
    named = None
    for name in sorted((home or "", away or ""), key=len, reverse=True):
        rest = formatted[len(name):] if name and formatted.startswith(name) else None
        if rest is not None and (rest == "" or rest.startswith(" ")) and not rest.strip()[:1].isalpha():
            named = name
            break
    if named is None:
        return False
    return (spread < 0) != (named == home)


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def select_market(game, market, sign):
    """Deterministic selection for 'spread' or 'total' (policy v2). Values are oriented to the archive home team.

    v2 (evidence: 2016 consensus was the sole outlier in 233 of 249 disputed spreads):
      * consensus outlier rule: when consensus is >= DISPUTE_POINTS from the median of >= 2 independent providers
        that agree with each other within DISPUTE_POINTS, select the highest-priority independent provider instead;
      * dispute test: selected value >= DISPUTE_POINTS from the median of the remaining providers (comparison only;
        medians are never selected or published, and no line is ever averaged into a selection).
    """
    providers = sorted(game["providers"].items(), key=lambda kv: _priority(kv[0]))
    values = [(p, r[market]) for p, r in providers if r[market] is not None]
    if not values:
        return {"status": "no_line", "provider": None}
    if any(v == "invalid" for _, v in values):
        return {"status": "suspicious", "provider": values[0][0], "flag": "non_numeric", "single_provider": len(values) == 1}
    first, first_value = values[0]
    rest = values[1:]
    # Sole-outlier rule: the priority choice is replaced only when >= 2 other providers agree with each other within
    # DISPUTE_POINTS and the priority choice is >= DISPUTE_POINTS from their median.
    replaced = (len(rest) >= 2 and max(v for _, v in rest) - min(v for _, v in rest) < DISPUTE_POINTS
                and abs(first_value - _median([v for _, v in rest])) >= DISPUTE_POINTS)
    pool = rest if replaced else values
    provider, value = pool[0]
    if replaced:
        reason = "consensus_outlier_replaced" if first == "consensus" else "priority_outlier_replaced"
    else:
        reason = ("priority" if provider == "consensus" else
                  "fallback_missing_consensus" if "consensus" not in game["providers"] else "fallback_missing_value")
    rec = game["providers"][provider]
    sel = {"provider": provider, "reason": reason, "single_provider": len(values) == 1}
    if market == "spread":
        flag = ("spread_magnitude" if abs(value) > 70 else "spread_increment" if not _half_point(value) else
                "spread_sign_conflict" if _favored_name_conflict(rec["formatted_spread"], value, game["home"], game["away"]) else None)
        if flag:
            return {**sel, "status": "suspicious", "flag": flag}
    elif not 20 <= value <= 110 or not _half_point(value):
        return {**sel, "status": "suspicious", "flag": "total_value"}
    others = [v for p, v in pool if p != provider]
    disagreement = abs(value - _median(others)) if others else 0.0
    opening = rec[market + "_open"]
    if opening == "invalid" or (isinstance(opening, float) and abs(opening - value) > 21):
        opening = None
    oriented = value * sign if market == "spread" else value
    open_oriented = (opening * sign if market == "spread" else opening) if isinstance(opening, float) else None
    status = "disputed" if disagreement >= DISPUTE_POINTS else "ok"
    return {**sel, "status": status, "value": oriented, "open": open_oriented, "disagreement": disagreement}


# ---------------------------------------------------------------- outcomes
def ats_result(margin, home_spread):
    """margin = home - away; home_spread negative = home favourite. Returns home-perspective W/L/P."""
    cover = margin + home_spread
    return ("W" if cover > 0 else "L" if cover < 0 else "P"), cover


def ou_result(total_points, total):
    diff = total_points - total
    return "O" if diff > 0 else "U" if diff < 0 else "P"


FLIP = {"W": "L", "L": "W", "P": "P"}


def game_outcome(result, spread_sel, total_sel):
    """Private per-game outcome. Never published as-is."""
    margin = result["home_score"] - result["away_score"]
    out = {"game_id": result["game_id"], "season": result["season"], "kickoff": result["kickoff"],
           "home": result["home"], "away": result["away"], "neutral": result["neutral_site"],
           "spread_status": spread_sel["status"], "total_status": total_sel["status"],
           "spread_provider": spread_sel.get("provider"), "total_provider": total_sel.get("provider")}
    if spread_sel["status"] in ("ok", "disputed"):
        out["home_ats"], out["home_cover"] = ats_result(margin, spread_sel["value"])
        out["home_spread"] = spread_sel["value"]
    if total_sel["status"] in ("ok", "disputed"):
        out["ou"] = ou_result(result["home_score"] + result["away_score"], total_sel["value"])
    return out


# ---------------------------------------------------------------- derived team statistics
SPLITS = ("home", "away", "neutral", "favorite", "underdog", "pickem")


def _empty_block():
    return {"games": 0, "ats": {"w": 0, "l": 0, "p": 0}, "ou": {"o": 0, "u": 0, "p": 0},
            "spread_excluded": {"no_line": 0, "disputed": 0, "suspicious": 0},
            "total_excluded": {"no_line": 0, "disputed": 0, "suspicious": 0},
            "cover_n": 0, "cover_sum": 0.0,
            "splits": {k: {"ats": {"w": 0, "l": 0, "p": 0}, "ou": {"o": 0, "u": 0, "p": 0}} for k in SPLITS}}


def _add(block, side, o, include_disputed):
    block["games"] += 1
    ok_spread = o["spread_status"] == "ok" or (include_disputed and o["spread_status"] == "disputed")
    ok_total = o["total_status"] == "ok" or (include_disputed and o["total_status"] == "disputed")
    venue = "neutral" if o["neutral"] else side
    letter = None
    if ok_spread:
        letter = o["home_ats"] if side == "home" else FLIP[o["home_ats"]]
        team_spread = o["home_spread"] if side == "home" else -o["home_spread"]
        role = "favorite" if team_spread < 0 else "underdog" if team_spread > 0 else "pickem"
        for bucket in (block["ats"], block["splits"][venue]["ats"], block["splits"][role]["ats"]):
            bucket[letter.lower()] += 1
        block["cover_n"] += 1
        if block["cover_sum"] is not None:
            block["cover_sum"] += o["home_cover"] if side == "home" else -o["home_cover"]
    else:
        block["spread_excluded"][o["spread_status"]] += 1
    if ok_total:
        for bucket in (block["ou"], block["splits"][venue]["ou"]):
            bucket[o["ou"].lower()] += 1
    else:
        block["total_excluded"][o["total_status"]] += 1
    return letter


def _merge(a, b):
    out = json.loads(json.dumps(a))
    def add(x, y):
        for k, v in y.items():
            if isinstance(v, dict):
                add(x[k], v)
            elif k == "cover_sum":
                x[k] = None if x[k] is None or v is None else x[k] + v
            else:
                x[k] += v
    add(out, b)
    return out


def _publish_block(block, include_sum=False):
    """Counts plus a rounded average only when n >= MIN_AVG_GAMES: a one-game average plus the public score would reveal a line."""
    pub = {k: v for k, v in block.items() if k not in ("cover_n", "cover_sum")}
    known = block["cover_sum"] is not None and block["cover_n"] >= MIN_AVG_GAMES
    pub["avg_cover_margin"] = round(block["cover_sum"] / block["cover_n"], 1) if known else None
    pub["avg_cover_margin_games"] = block["cover_n"]
    if include_sum:
        pub["cover_sum"] = block["cover_sum"] if known else None
    return pub


def _private_from_public(pub):
    block = {k: json.loads(json.dumps(v)) for k, v in pub.items()
             if k in ("games", "ats", "ou", "spread_excluded", "total_excluded", "splits")}
    block["cover_n"] = pub["avg_cover_margin_games"]
    block["cover_sum"] = pub.get("cover_sum") if block["cover_n"] else 0.0
    return block


def team_statistics(outcomes, current_season=None, prior_teams=None):
    """Primary (disputed excluded) and sensitivity (disputed included) statistics per team.

    Full mode: all seasons from outcomes. Incremental mode (prior_teams given): outcomes cover only the
    current season; history comes from the prior public payload's exact per-team history aggregates.
    """
    work = {}
    def team(name):
        return work.setdefault(name, {"by_season": {}, "seq": [], "hist": _empty_block(), "hist_sens": _empty_block(),
                                      "cur": _empty_block(), "cur_sens": _empty_block()})
    for name, pt in (prior_teams or {}).items():
        t = team(name)
        t["hist"] = _private_from_public(pt["history"])
        t["hist_sens"] = _private_from_public(pt["history"]["sensitivity"])
        for s, b in pt["by_season"].items():
            if int(s) != current_season:
                t["by_season"][s] = ("public", b)
                t["seq"] += [(int(s), l) for l in b["ats_sequence"]]
    for o in sorted(outcomes, key=lambda x: (x["kickoff"] or "", x["game_id"])):
        for side in ("home", "away"):
            t = team(o[side])
            key = str(o["season"])
            if key not in t["by_season"]:
                t["by_season"][key] = ("private", _empty_block())
            letter = _add(t["by_season"][key][1], side, o, False)
            current = o["season"] == current_season
            _add(t["cur" if current else "hist"], side, o, False)
            _add(t["cur_sens" if current else "hist_sens"], side, o, True)
            if letter:
                t["seq"].append((o["season"], letter))
                t["by_season"][key][1].setdefault("_seq", []).append(letter)
    for t in work.values():
        # Same disclosure rule as the public history block: a withheld small-sample sum is unknown in both modes,
        # so full rebuilds and incremental refreshes produce identical outputs.
        for k in ("hist", "hist_sens"):
            if 0 < t[k]["cover_n"] < MIN_AVG_GAMES:
                t[k]["cover_sum"] = None
    public = {}
    for name, t in sorted(work.items()):
        by_season = {}
        for s, (kind, b) in sorted(t["by_season"].items()):
            if kind == "public":
                by_season[s] = b
            else:
                seq = "".join(b.pop("_seq", []))
                by_season[s] = {**_publish_block(b), "ats_sequence": seq}
        seq = sorted(t["seq"], key=lambda x: x[0])  # seasons ascending; within a season kickoff order is preserved
        recent = list(reversed(seq))
        overall_sens = _merge(t["hist_sens"], t["cur_sens"])
        public[name] = {
            "history": {**_publish_block(t["hist"], include_sum=True), "sensitivity": _publish_block(t["hist_sens"], include_sum=True)},
            "overall": _publish_block(_merge(t["hist"], t["cur"])),
            "by_season": by_season,
            "last_n": {str(n): {k: sum(1 for _, l in recent[:n] if l.lower() == k) for k in ("w", "l", "p")} for n in (5, 10, 20)},
            "recent_results": [{"season": s, "ats": l} for s, l in recent[:20]],
            "sensitivity_including_disputed": {"ats": overall_sens["ats"], "ou": overall_sens["ou"]},
        }
    return public


# ---------------------------------------------------------------- season build and validation
def build_season(season, raw_rows, results):
    """Return (outcomes, coverage). Raises ArchiveRejected on identity/score mismatch."""
    games, conflicts = normalize(raw_rows)
    season_results = {gid: r for gid, r in results.items() if r["season"] == season}
    cov = Counter()
    providers_spread, providers_total = Counter(), Counter()
    outcomes = []
    cov["archive_games"] = len(season_results)
    for gid, result in season_results.items():
        game = games.get(gid)
        if game is None:
            cov["unmatched"] += 1
            continue
        cov["matched"] += 1
        sign = orient(game, result)
        if gid in conflicts:
            spread = total = {"status": "suspicious", "provider": None, "flag": "conflicting_duplicate"}
            cov["conflicting_duplicates"] += 1
        else:
            spread, total = select_market(game, "spread", sign), select_market(game, "total", sign)
        cov["spread_" + spread["status"]] += 1
        cov["total_" + total["status"]] += 1
        cov["spread_open_available"] += spread.get("open") is not None
        cov["total_open_available"] += total.get("open") is not None
        cov["spread_single_provider"] += bool(spread.get("single_provider"))
        cov["spread_consensus_replaced"] += spread.get("reason") == "consensus_outlier_replaced"
        cov["total_consensus_replaced"] += total.get("reason") == "consensus_outlier_replaced"
        cov["spread_priority_replaced"] += spread.get("reason") == "priority_outlier_replaced"
        cov["total_priority_replaced"] += total.get("reason") == "priority_outlier_replaced"
        if spread.get("provider"):
            providers_spread[spread["provider"]] += 1
        if total.get("provider"):
            providers_total[total["provider"]] += 1
        if result["completed"]:
            cov["completed"] += 1
            outcomes.append(game_outcome(result, spread, total))
    coverage = {k: cov.get(k, 0) for k in (
        "archive_games", "matched", "unmatched", "completed", "conflicting_duplicates",
        "spread_ok", "spread_disputed", "spread_no_line", "spread_suspicious",
        "total_ok", "total_disputed", "total_no_line", "total_suspicious",
        "spread_open_available", "total_open_available", "spread_single_provider",
        "spread_consensus_replaced", "total_consensus_replaced", "spread_priority_replaced", "total_priority_replaced")}
    coverage["selected_spread_providers"] = dict(sorted(providers_spread.items()))
    coverage["selected_total_providers"] = dict(sorted(providers_total.items()))
    return outcomes, coverage


def validate_season(season, cov, completed_season=True):
    if cov["matched"] + cov["unmatched"] != cov["archive_games"]:
        raise ArchiveRejected(f"{season}: coverage does not reconcile")
    for market in ("spread", "total"):
        parts = sum(cov[f"{market}_{s}"] for s in ("ok", "disputed", "no_line", "suspicious"))
        if parts != cov["matched"]:
            raise ArchiveRejected(f"{season}: {market} statuses do not reconcile")
    if cov["conflicting_duplicates"]:
        raise ArchiveRejected(f"{season}: {cov['conflicting_duplicates']} conflicting duplicate rows")
    if not completed_season:
        return
    m = cov["matched"] or 1
    checks = {"matched": cov["matched"] / (cov["archive_games"] or 1),
              "spread": (cov["spread_ok"] + cov["spread_disputed"]) / m,
              "total": (cov["total_ok"] + cov["total_disputed"]) / m}
    for k, v in checks.items():
        if v < THRESHOLDS[k]:
            raise ArchiveRejected(f"{season}: {k} coverage {v:.3f} below {THRESHOLDS[k]}")
    for market in ("spread", "total"):
        if cov[f"{market}_disputed"] / m > THRESHOLDS["disputed"]:
            raise ArchiveRejected(f"{season}: {market} disputed share above {THRESHOLDS['disputed']}; review provider policy")
        if cov[f"{market}_suspicious"]:
            raise ArchiveRejected(f"{season}: {cov[market + '_suspicious']} unexplained suspicious {market} values")


def diagnose_season(season, raw_rows, results):
    """Aggregate dispute diagnostics (counts only; safe for CI logs)."""
    games, _ = normalize(raw_rows)
    out = Counter()
    for gid, result in results.items():
        if result["season"] != season or gid not in games:
            continue
        for market in ("spread", "total"):
            vals = {p: r[market] for p, r in games[gid]["providers"].items() if isinstance(r[market], float)}
            if len(vals) < 2:
                continue
            out[f"{market}_multi_provider"] += 1
            spread_of_values = max(vals.values()) - min(vals.values())
            if spread_of_values < DISPUTE_POINTS:
                continue
            out[f"{market}_disputed"] += 1
            bucket = "3-4" if spread_of_values < 4 else "4-6" if spread_of_values < 6 else "6-10" if spread_of_values < 10 else "10+"
            out[f"{market}_range_{bucket}"] += 1
            if "consensus" in vals and len(vals) >= 3:
                others = [v for p, v in vals.items() if p != "consensus"]
                if max(others) - min(others) < DISPUTE_POINTS:
                    out[f"{market}_consensus_sole_outlier"] += 1
            if "consensus" in vals and len(vals) >= 2:
                others = sorted(v for p, v in vals.items() if p != "consensus")
                med = others[len(others) // 2]
                if abs(vals["consensus"] - med) >= DISPUTE_POINTS and (vals["consensus"] < 0) != (med < 0) and market == "spread":
                    out["spread_consensus_opposite_favourite"] += 1
    for gid, result in results.items():
        if result["season"] != season or gid not in games:
            continue
        sign = orient(games[gid], result)
        for market in ("spread", "total"):
            sel = select_market(games[gid], market, sign)
            if sel["status"] == "suspicious":
                out[f"policy_v2_{market}_suspicious_flag_{sel.get('flag')}"] += 1
            if sel["status"] == "disputed":
                out[f"policy_v2_{market}_disputed_selected_{sel['provider']}"] += 1
                vals = {p: r[market] for p, r in games[gid]["providers"].items() if isinstance(r[market], float)}
                rest = [v for p, v in vals.items() if p != sel["provider"]]
                if len(rest) >= 2 and max(rest) - min(rest) < DISPUTE_POINTS:
                    out[f"policy_v2_{market}_disputed_selected_sole_outlier"] += 1
    _, cov = build_season(season, raw_rows, {g: r for g, r in results.items() if r["season"] == season})
    for k in ("spread_disputed", "total_disputed", "spread_consensus_replaced", "total_consensus_replaced",
              "spread_priority_replaced", "total_priority_replaced", "spread_suspicious", "total_suspicious"):
        out["policy_v2_" + k] = cov[k]
    return dict(sorted(out.items()))


# ---------------------------------------------------------------- public output and guard
PUBLIC_GAME_KEYS = {"spread", "total", "spread_open", "total_open", "home_spread", "home_cover", "cover", "line", "moneyline",
                    "cover_margin", "over_under", "value", "open", "disagreement", "provider", "game_id", "home_score", "away_score"}
FLOAT_KEYS = {"avg_cover_margin", "cover_sum", "dispute_threshold_points", "max_team_cover_rate_change_pct_points"}


def assert_public_safe(obj, key="$"):
    """Licensing guard: fail if a restricted per-game field or an unexpected number appears in a public payload."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in PUBLIC_GAME_KEYS:
                raise ArchiveRejected(f"restricted field {k!r} in public output")
            assert_public_safe(v, k)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, dict) and set(v) - {"season", "ats"}:
                raise ArchiveRejected(f"unexpected per-game object under {key!r}")
            assert_public_safe(v, key)
    elif isinstance(obj, float) and key not in FLOAT_KEYS:
        raise ArchiveRejected(f"unexpected non-integer value under {key!r}")


def sensitivity_summary(teams):
    primary = Counter(); sens = Counter(); max_shift = 0.0
    for t in teams.values():
        p, s = t["overall"]["ats"], t["sensitivity_including_disputed"]["ats"]
        for k in "wlp":
            primary[k] += p[k]; sens[k] += s[k]
        pr = p["w"] / max(p["w"] + p["l"], 1); sr = s["w"] / max(s["w"] + s["l"], 1)
        max_shift = max(max_shift, abs(pr - sr))
    return {"primary_method": "disputed games (provider disagreement >= 3.0 points) excluded from ATS/O-U",
            "sensitivity_method": "disputed games included using the deterministically selected provider",
            "ats_games_primary": sum(primary.values()) // 2, "ats_games_including_disputed": sum(sens.values()) // 2,
            "max_team_cover_rate_change_pct_points": round(100 * max_shift, 1)}


def fbs_teams(report_path=CURRENT_REPORT):
    return {t["team"] for t in json.loads(Path(report_path).read_text())["rankings"]}


def build_public(outcomes, coverage, receipts, current_season=None, prior_teams=None, publish_teams=None):
    teams = team_statistics(outcomes, current_season, prior_teams)
    if publish_teams is not None:
        # Records are published for current FBS programs only; their games against FCS opponents still count.
        teams = {name: t for name, t in teams.items() if name in publish_teams}
    generated = max(r["retrieved_at"] for s in receipts["seasons"].values() for t, r in s.items() if t in SEASON_TYPES)
    payload = {"schema_version": SCHEMA_VERSION, "provider_policy_version": POLICY_VERSION, "generated_at": generated,
               "source": SOURCE, "attribution": ATTRIBUTION,
               "methodology": {"closing_line": "selected provider's last captured CFBD value; ATS and O/U use closing values only",
                               "provider_priority": list(PROVIDER_PRIORITY) + ["others alphabetically"],
                               "dispute_threshold_points": DISPUTE_POINTS,
                               "dispute_test": "selected closing value vs median of other providers (comparison only)",
                               "sole_outlier_rule": "the priority provider (consensus or a sportsbook) is replaced by the highest-priority provider of an agreeing group when it is >= 3 points from the median of >= 2 other providers that agree within 3 points",
                               "spread_convention": "home spread, negative = home favourite",
                               "primary_denominator": "games with a non-disputed, non-suspicious closing value for that market",
                               "avg_cover_margin_min_games": MIN_AVG_GAMES,
                               "limitations": ["Opening lines unavailable before 2021",
                                               "Per-game lines are not published (CFBD redistribution terms pending clarification)",
                                               "Current-season records include completed games only",
                                               "Published teams are current FBS programs; seasons before a program joined FBS include only games against FBS opponents",
                                               "Descriptive records are not predictions"]},
               "seasons": sorted(int(s) for s in coverage), "current_season": current_season,
               "coverage": dict(sorted(coverage.items())), "sensitivity": sensitivity_summary(teams), "teams": teams}
    assert_public_safe(payload)
    return payload


def write_atomic(pairs):
    """Write all (path, payload) temps first, then replace; on any error nothing is replaced.
    The public archive is written compactly (browser payload); receipts stay indented for review."""
    temps = []
    try:
        for path, payload in pairs:
            tmp = Path(str(path) + ".tmp")
            tmp.parent.mkdir(parents=True, exist_ok=True)
            compact = "teams" in payload   # the public archive payload; independent of the file name
            text = json.dumps(payload, sort_keys=True, separators=(",", ":")) if compact else json.dumps(payload, indent=1, sort_keys=True)
            tmp.write_text(text + "\n")
            temps.append((tmp, Path(path)))
        for tmp, path in temps:
            tmp.replace(path)
    finally:
        for tmp, _ in temps:
            tmp.unlink(missing_ok=True)


def run(seasons, current_season, key, cache, *, offline=False, accept_upstream=False, incremental=False, fetch=fetch_cfbd_lines,
        receipts_path=RECEIPTS, public_path=PUBLIC, archive=ARCHIVE, games_path=CURRENT_GAMES, report_path=CURRENT_REPORT, now=None):
    """Build, validate and atomically publish. Any ArchiveRejected leaves both outputs untouched."""
    prior = json.loads(Path(receipts_path).read_text()) if Path(receipts_path).exists() else {"seasons": {}}
    receipts = {"schema_version": SCHEMA_VERSION, "provider_policy_version": POLICY_VERSION, "source": SOURCE,
                "attribution": ATTRIBUTION, "seasons": {}}
    prior_teams, coverage = None, {}
    if incremental:
        # Current-season refresh: history is carried forward from the last verified outputs (no historical download).
        if current_season is None or not Path(public_path).exists():
            raise ArchiveRejected("incremental refresh needs a current season and an existing verified public archive")
        prior_public = json.loads(Path(public_path).read_text())
        if prior_public.get("provider_policy_version") != POLICY_VERSION:
            raise ArchiveRejected("provider policy changed; run a full backfill")
        prior_teams = prior_public["teams"]
        for s, entry in prior["seasons"].items():
            if int(s) != current_season:
                receipts["seasons"][s] = entry
                coverage[s] = entry["coverage"]
        seasons = [current_season]
    results = historical_results([s for s in seasons if s != current_season], archive)
    if current_season in seasons:
        results.update(current_results(current_season, games_path, report_path, now))
    outcomes = []
    for season in seasons:
        rows = []
        receipts["seasons"][str(season)] = {}
        for st in SEASON_TYPES:
            prior_r = prior["seasons"].get(str(season), {}).get(st)
            # The current season legitimately changes every week; only completed seasons are change-guarded.
            guard = prior_r if season != current_season else None
            r, receipt = acquire(season, st, key, cache, guard, offline=offline, accept_upstream=accept_upstream, fetch=fetch)
            receipts["seasons"][str(season)][st] = receipt
            rows += r
        season_outcomes, cov = build_season(season, rows, results)
        validate_season(season, cov, completed_season=season != current_season)
        receipts["seasons"][str(season)]["coverage"] = cov
        coverage[str(season)] = cov
        outcomes += season_outcomes
    receipts["seasons"] = dict(sorted(receipts["seasons"].items()))
    payload = build_public(outcomes, coverage, receipts, current_season, prior_teams, fbs_teams(report_path))
    write_atomic([(receipts_path, receipts), (public_path, payload)])
    return receipts, payload


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backfill", help="completed season range, e.g. 2016-2025 (full rebuild)")
    p.add_argument("--season", type=int, help="current season; alone = incremental refresh on top of the verified archive")
    p.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="private, gitignored snapshot directory")
    p.add_argument("--offline", action="store_true")
    p.add_argument("--check", action="store_true", help="offline full rebuild must reproduce committed outputs byte-for-byte")
    p.add_argument("--accept-upstream-change", action="store_true")
    p.add_argument("--diagnose", action="store_true", help="print aggregate dispute diagnostics per season and exit (no outputs written)")
    a = p.parse_args()
    incremental = bool(a.season and not a.backfill and not a.check)
    if a.backfill:
        lo, hi = (int(x) for x in a.backfill.split("-"))
        seasons = list(range(lo, hi + 1))
    else:
        seasons = sorted(int(s) for s in json.loads(RECEIPTS.read_text())["seasons"]) if RECEIPTS.exists() else []
    if a.season:
        seasons = sorted(set(seasons) | {a.season})
    if a.diagnose:
        lo, hi = (int(x) for x in a.backfill.split("-"))
        report = {}
        for season in range(lo, hi + 1):
            rows = []
            for st in SEASON_TYPES:
                r, _ = acquire(season, st, os.environ.get("CFBD_API_KEY", ""), a.cache, None, offline=a.offline)
                rows += r
            res = historical_results([season])
            report[season] = {"matched": sum(1 for g in res if g in normalize(rows)[0]), **diagnose_season(season, rows, res)}
        print(json.dumps(report, indent=1))
        return
    if a.check:
        before = (RECEIPTS.read_bytes(), PUBLIC.read_bytes())
        tmp_r, tmp_p = Path(str(RECEIPTS) + ".check"), Path(str(PUBLIC) + ".check")
        try:
            tmp_r.write_bytes(before[0])
            run(seasons, a.season, "", a.cache, offline=True, receipts_path=tmp_r, public_path=tmp_p)
            if (tmp_r.read_bytes(), tmp_p.read_bytes()) != before:
                raise SystemExit("regeneration differs from committed outputs")
        finally:
            tmp_r.unlink(missing_ok=True)
            tmp_p.unlink(missing_ok=True)
        print("check: byte-identical")
        return
    try:
        receipts, payload = run(seasons, a.season, os.environ.get("CFBD_API_KEY", ""), a.cache, offline=a.offline,
                                accept_upstream=a.accept_upstream_change, incremental=incremental)
    except ArchiveRejected as exc:
        raise SystemExit(f"market archive rejected; last verified outputs kept: {exc}")
    # Aggregates only: never print per-game values in CI logs.
    print(json.dumps({"seasons": payload["seasons"], "teams": len(payload["teams"]), "sensitivity": payload["sensitivity"],
                      "coverage": {s: {k: v for k, v in c.items() if not k.startswith("selected_")}
                                   for s, c in payload["coverage"].items()}}, indent=1))


if __name__ == "__main__":
    main()
