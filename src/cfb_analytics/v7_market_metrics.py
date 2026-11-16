"""V7 Milestone 3: market comparison and metrics engine.

Reads only already-published, licensed inputs:
  * web/public/v7-team-lines/<team>.json  (M2: one named provider's closing spread/total per game)
  * data/pregame-2026-history.json        (forecast ledger; only authentic pre-kickoff entries are used)
  * research/archive/verified/verified-pregame-rows.json (independently verified publication cohort)

Writes:
  * web/public/v7-market-metrics.json          team aggregates, national calibration, comparison summary
  * web/public/v7-model-market/<team>.json     per-game model-vs-market rows (team/game page context only)

No network, no private snapshots, no new model. The model produces win probabilities and projected
margins; it does not produce game totals, so no model-vs-market totals comparison exists.
"""
import argparse
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from .model import market_home_win_probability
from .v7_market_archive import ATTRIBUTION, LINES_LICENSE, POLICY_VERSION, team_slug

SCHEMA_VERSION = 1
LINES_DIR = Path("web/public/v7-team-lines")
LEDGER = Path("data/pregame-2026-history.json")
VERIFIED = Path("research/archive/verified/verified-pregame-rows.json")
TEAM_HISTORY = Path("web/public/v7-team-market-history.json")
PUBLIC = Path("web/public/v7-market-metrics.json")
COMPARISON_DIR = Path("web/public/v7-model-market")

MARKET_SCALE = 19.5          # existing validated spread->probability scale (V7-DATA-FEASIBILITY §M1)
Z95 = 1.959963984540054
MIN_RATE_GAMES = 10          # below this a rate is not published (insufficient sample)
ADEQUATE_GAMES = 30
MIN_DISTRIBUTION_GAMES = 5   # same small-sample rule as the M2 archive
LAST_N = (5, 10, 20)
VENUES = ("home", "away", "neutral")
ROLES = ("favorite", "underdog", "pickem")
COVER_BUCKETS = (("lt_-14", None, -14), ("-14_to_-7", -14, -7), ("-7_to_-3", -7, -3), ("-3_to_0", -3, 0),
                 ("push", 0, 0), ("0_to_3", 0, 3), ("3_to_7", 3, 7), ("7_to_14", 7, 14), ("gt_14", 14, None))
DIFF_BUCKETS = ((0, 5), (5, 10), (10, 20), (20, None))   # absolute probability-point difference

IMPLIED_PROBABILITY_NOTE = (
    "Approximate win probability derived from the closing point spread with the existing logistic conversion "
    f"(scale {MARKET_SCALE} points, fitted on 7,560 FBS games 2016-2025). Spreads are quoted at roughly equal "
    "prices on both sides; no moneyline prices or bookmaker margin (vig/fees) are used, so this is not a traded "
    "price, an executable quote or a share of bets or money.")
MODEL_TOTAL = {"status": "not_available",
               "reason": "The incumbent model does not produce game totals, so no model-vs-market totals comparison is made."}
RETROSPECTIVE = {"used": False,
                 "reason": ("No model forecasts were archived before kickoff for 2016-2025. Retrospective replays "
                            "(for example the V6 research challenger) are calculations made after the games and are "
                            "neither used here nor presented as pregame predictions."),
                 "historical_model_comparison": "not_available"}


class MetricsRejected(RuntimeError):
    pass


# ---------------------------------------------------------------- small statistics helpers
def wilson(successes, n):
    if n == 0:
        return None
    p = successes / n
    denom = 1 + Z95 ** 2 / n
    centre = (p + Z95 ** 2 / (2 * n)) / denom
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / denom
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def sample_label(n):
    return "insufficient" if n < MIN_RATE_GAMES else "limited" if n < ADEQUATE_GAMES else "adequate"


def rate_block(wins, losses, pushes, win_key, loss_key):
    """Record plus a rate that excludes pushes, a Wilson 95% interval and a sample-size label."""
    n = wins + losses
    block = {win_key: wins, loss_key: losses, "p": pushes, "decided": n, "sample": sample_label(n)}
    if n < MIN_RATE_GAMES:
        block.update(rate=None, ci95=None, ci_excludes_50=None,
                     na_reason=f"fewer than {MIN_RATE_GAMES} decided games")
    else:
        ci = wilson(wins, n)
        block.update(rate=round(wins / n, 3), ci95=ci, ci_excludes_50=ci[0] > 0.5 or ci[1] < 0.5)
    return block


def distribution(values):
    n = len(values)
    if n < MIN_DISTRIBUTION_GAMES:
        return {"n": n, "mean": None, "median": None, "sd": None, "p25": None, "p75": None, "buckets": None,
                "na_reason": f"fewer than {MIN_DISTRIBUTION_GAMES} games"}
    q = statistics.quantiles(values, n=4, method="inclusive")
    buckets = {}
    for name, lo, hi in COVER_BUCKETS:
        if name == "push":
            buckets[name] = sum(1 for v in values if v == 0)
        elif hi is not None and hi <= 0:
            buckets[name] = sum(1 for v in values if (lo is None or v >= lo) and v < hi)
        else:
            buckets[name] = sum(1 for v in values if v > lo and (hi is None or v <= hi))
    return {"n": n, "mean": round(statistics.fmean(values), 1), "median": round(statistics.median(values), 1),
            "sd": round(statistics.stdev(values), 1), "p25": round(q[0], 1), "p75": round(q[2], 1), "buckets": buckets}


def implied_probability(team_spread):
    """Team-perspective spread (negative = favoured) -> approximate win probability."""
    return market_home_win_probability(team_spread, MARKET_SCALE)


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.astimezone(timezone.utc) if t.tzinfo else None


# ---------------------------------------------------------------- per-game classification
def classify(game):
    """Derive one team-perspective game record from an M2 per-game line entry. Pure and independently testable."""
    spread, total = game["spread"], game["total"]
    played = game["team_score"] is not None and game["opponent_score"] is not None
    margin = game["team_score"] - game["opponent_score"] if played else None
    out = {"season": game["season"], "venue": game["venue"], "played": played, "spread_status": game["spread_status"],
           "total_status": game["total_status"], "kickoff": game["kickoff"], "game_id": game["game_id"]}
    if spread is not None:
        out["role"] = "favorite" if spread < 0 else "underdog" if spread > 0 else "pickem"
        out["implied"] = implied_probability(spread)
        if played:
            cover = margin + spread
            letter = "W" if cover > 0 else "L" if cover < 0 else "P"
            if game["ats"] is not None and game["ats"] != letter:
                raise MetricsRejected(f"ATS letter disagrees with score and spread for game {game['game_id']}")
            out.update(cover=cover, ats=letter)
    if total is not None and played:
        diff = game["team_score"] + game["opponent_score"] - total
        letter = "O" if diff > 0 else "U" if diff < 0 else "P"
        if game["ou"] is not None and game["ou"] != letter:
            raise MetricsRejected(f"O/U letter disagrees with score and total for game {game['game_id']}")
        out.update(total_margin=diff, ou=letter)
    if played:
        out["result"] = "W" if margin > 0 else "L" if margin < 0 else "T"
    return out


def _usable(g, market, include_disputed=False):
    """A game counts for a market when its closing value is non-disputed (or disputed, for the sensitivity) and it has a result."""
    allowed = ("ok", "disputed") if include_disputed else ("ok",)
    return g[market + "_status"] in allowed and ("ats" if market == "spread" else "ou") in g


def _exclusions(rows, market):
    out = {"no_line": 0, "disputed": 0, "suspicious": 0, "no_result": 0}
    for g in rows:
        status = g[market + "_status"]
        if status != "ok":
            out[status] = out.get(status, 0) + 1
        elif not g["played"]:
            out["no_result"] += 1
    return out


def team_block(rows):
    """Aggregate metrics for one team's classified games (primary: disputed excluded)."""
    ats_rows = [g for g in rows if _usable(g, "spread")]
    ou_rows = [g for g in rows if _usable(g, "total")]
    def ats(sub):
        return rate_block(*(sum(1 for g in sub if g["ats"] == k) for k in "WLP"), "w", "l")
    def ou(sub):
        return rate_block(*(sum(1 for g in sub if g["ou"] == k) for k in "OUP"), "o", "u")
    expect = [g for g in ats_rows if g["result"] != "T"]
    implied_sum = sum(g["implied"] for g in expect)
    wins = sum(1 for g in expect if g["result"] == "W")
    market = {"games": len(expect), "actual_wins": wins,
              "market_expected_wins": round(implied_sum, 1) if expect else None,
              "wins_vs_market": round(wins - implied_sum, 1) if expect else None,
              "mean_implied_win_probability": round(implied_sum / len(expect), 3) if expect else None,
              "tied_finals_excluded": sum(1 for g in ats_rows if g["result"] == "T")}
    if len(expect) < MIN_RATE_GAMES:
        market.update(market_expected_wins=None, wins_vs_market=None, mean_implied_win_probability=None,
                      na_reason=f"fewer than {MIN_RATE_GAMES} games with a closing spread and a result")
    recent = sorted(ats_rows, key=lambda g: (g["kickoff"] or "", g["game_id"]), reverse=True)
    recent_ou = sorted(ou_rows, key=lambda g: (g["kickoff"] or "", g["game_id"]), reverse=True)
    return {
        "games": len(rows),
        "ats": ats(ats_rows), "ou": ou(ou_rows),
        "ats_excluded": _exclusions(rows, "spread"), "ou_excluded": _exclusions(rows, "total"),
        "ats_including_disputed": ats([g for g in rows if _usable(g, "spread", include_disputed=True)]),
        "splits": {
            "venue": {v: {"ats": ats([g for g in ats_rows if g["venue"] == v]),
                          "ou": ou([g for g in ou_rows if g["venue"] == v])} for v in VENUES},
            "role": {r: {"ats": ats([g for g in ats_rows if g["role"] == r]),
                         "ou": ou([g for g in ou_rows if g.get("role") == r]),
                         "cover_margin_mean": distribution([g["cover"] for g in ats_rows if g["role"] == r])["mean"]}
                     for r in ROLES},
        },
        "cover_margin": distribution([g["cover"] for g in ats_rows]),
        "total_margin": distribution([g["total_margin"] for g in ou_rows]),
        "market_expectation": market,
        "last_n": {str(n): {"ats": {k: sum(1 for g in recent[:n] if g["ats"] == K) for k, K in zip("wlp", "WLP")},
                            "ou": {k: sum(1 for g in recent_ou[:n] if g["ou"] == K) for k, K in zip("oup", "OUP")}}
                   for n in LAST_N},
    }


# ---------------------------------------------------------------- national calibration of the spread conversion
def calibration(lines):
    """Each game once (home side, else alphabetically first team for neutral sites); 10-point bins."""
    chosen = {}
    for team, games in sorted(lines.items()):
        for g in games:
            if g["spread_status"] != "ok" or g["team_score"] is None or g["team_score"] == g["opponent_score"]:
                continue
            if g["game_id"] not in chosen or g["venue"] == "home":   # teams iterate alphabetically
                chosen[g["game_id"]] = g
    seasons = {}
    rows = []
    for g in chosen.values():
        p = implied_probability(g["spread"])
        won = g["team_score"] > g["opponent_score"]
        rows.append((p, won, g["season"]))
    bins = []
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10
        sub = [(p, w) for p, w, _ in rows if lo <= p < hi or (i == 9 and p == 1.0)]
        n = len(sub)
        wins = sum(1 for _, w in sub if w)
        bins.append({"lower": lo, "upper": hi, "games": n,
                     "mean_implied": round(statistics.fmean(p for p, _ in sub), 3) if n else None,
                     "observed_win_rate": round(wins / n, 3) if n else None, "ci95": wilson(wins, n)})
    for p, w, s in rows:
        seasons.setdefault(s, []).append((p, w))
    brier = lambda xs: round(statistics.fmean((p - w) ** 2 for p, w in xs), 4)
    return {"games": len(rows), "brier": brier([(p, w) for p, w, _ in rows]) if rows else None,
            "by_season_brier": {str(s): brier(xs) for s, xs in sorted(seasons.items())},
            "bins": bins,
            "method": "home-team perspective (neutral sites: alphabetically first team; FBS-at-FCS: the FBS team); non-disputed closing spreads; "
                      "completed, non-tied games; each game counted once"}


# ---------------------------------------------------------------- authentic model-vs-market comparison
def authentic_forecast(entry, kickoff_from_lines=None):
    """(True, None) only for a forecast generated and recorded before kickoff by an identified model."""
    if entry.get("source") != "generated_before_kickoff":
        return False, "not_generated_before_kickoff"
    if not entry.get("model_id"):
        return False, "no_model_id"
    recorded, scheduled = parse_time(entry.get("forecast_recorded_at")), parse_time(entry.get("scheduled_kickoff_at"))
    if recorded is None or scheduled is None:
        return False, "missing_timestamp"
    actual = parse_time(kickoff_from_lines) or scheduled
    if not (recorded < scheduled and recorded < actual):
        return False, "recorded_at_or_after_kickoff"
    p = entry.get("home_win_probability")
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        return False, "invalid_probability"
    m = entry.get("home_margin")
    if isinstance(m, bool) or not isinstance(m, (int, float)) or not math.isfinite(m):
        return False, "invalid_margin"
    return True, None


def _find_line(lines_by_team, home, away, game_id):
    """Home-perspective line entry; falls back to the away team's file (non-FBS home) and inverts it."""
    for team, other, invert in ((home, away, False), (away, home, True)):
        for g in lines_by_team.get(team, ()):
            if g["game_id"] == game_id:
                if g["opponent"] != other:
                    return None, "team_mismatch"
                return (g, invert), None
    return None, "no_line_record"


def comparison_rows(ledger, lines_by_team, verified):
    """Per-game authentic comparisons plus an exclusion tally with reasons."""
    excluded = {}
    rows = []
    def skip(reason):
        excluded[reason] = excluded.get(reason, 0) + 1
    for key, entry in sorted(ledger.items()):
        ok, reason = authentic_forecast(entry)
        if not ok:
            skip(reason)
            continue
        found, reason = _find_line(lines_by_team, entry.get("home"), entry.get("away"), key)
        if found is None:
            if reason == "no_line_record":
                fbs = entry.get("home") in lines_by_team or entry.get("away") in lines_by_team
                reason = "game_not_in_archive" if fbs else "non_fbs_matchup"
            skip(reason)
            continue
        g, invert = found
        ok, reason = authentic_forecast(entry, g["kickoff"])   # re-check against the archived kickoff (reschedules)
        if not ok:
            skip(reason)
            continue
        if g["spread_status"] != "ok":
            skip(f"spread_{g['spread_status']}")
            continue
        v = verified.get(key)
        if v is not None and (v["home_win_probability"] != entry["home_win_probability"]
                              or v["prediction_time"] != entry["forecast_recorded_at"]):
            raise MetricsRejected(f"verified publication record disagrees with the ledger for game {key}")
        home_spread = -g["spread"] if invert else g["spread"]
        market_p = implied_probability(home_spread)
        model_p, model_m = entry["home_win_probability"], entry["home_margin"]
        market_m = -home_spread
        recorded, kickoff = parse_time(entry["forecast_recorded_at"]), parse_time(g["kickoff"])
        played = g["team_score"] is not None
        home_score, away_score = ((g["opponent_score"], g["team_score"]) if invert else (g["team_score"], g["opponent_score"]))
        rows.append({
            "game_id": key, "season": g["season"], "week": g["week"], "kickoff": g["kickoff"],
            "home": entry["home"], "away": entry["away"], "neutral": g["venue"] == "neutral",
            "forecast_kind": "authentic_pregame",
            "publication_evidence": "independently_verified" if v is not None else "ledger_recorded_before_kickoff",
            "model_id": entry["model_id"], "forecast_recorded_at": entry["forecast_recorded_at"],
            "hours_before_kickoff": round((kickoff - recorded).total_seconds() / 3600, 1),
            "model_home_win_probability": round(model_p, 4), "market_home_win_probability": round(market_p, 4),
            "probability_difference_points": round(100 * (model_p - market_p), 1),
            "model_home_margin": round(model_m, 1), "home_spread": home_spread, "spread_provider": g["spread_provider"],
            "margin_difference_points": round(model_m - market_m, 1),
            "favorite_agreement": ("market_pickem" if market_m == 0 else "model_pickem" if model_m == 0 else
                                   "agree" if (model_m > 0) == (market_m > 0) else "disagree"),
            "home_score": home_score if played else None, "away_score": away_score if played else None,
        })
    return rows, dict(sorted(excluded.items()))


def comparison_summary(rows, excluded):
    def describe(sub):
        if not sub:
            return {"games": 0, "na_reason": "no authentic pregame forecasts with a non-disputed closing spread"}
        diffs = [abs(r["probability_difference_points"]) for r in sub]
        margins = [abs(r["margin_difference_points"]) for r in sub]
        buckets = {f"{lo}_to_{hi}" if hi else f"gte_{lo}": sum(1 for d in diffs if d >= lo and (hi is None or d < hi))
                   for lo, hi in DIFF_BUCKETS}
        agreement = {k: sum(1 for r in sub if r["favorite_agreement"] == k)
                     for k in ("agree", "disagree", "market_pickem", "model_pickem")}
        return {"games": len(sub), "sample": sample_label(len(sub)),
                "mean_abs_probability_difference_points": round(statistics.fmean(diffs), 1),
                "median_abs_probability_difference_points": round(statistics.median(diffs), 1),
                "mean_signed_probability_difference_points": round(statistics.fmean(r["probability_difference_points"] for r in sub), 1),
                "abs_probability_difference_buckets": buckets,
                "mean_abs_margin_difference_points": round(statistics.fmean(margins), 1),
                "median_abs_margin_difference_points": round(statistics.median(margins), 1),
                "favorite_agreement": agreement,
                "median_hours_before_kickoff": round(statistics.median(r["hours_before_kickoff"] for r in sub), 1)}
    return {
        "population": "authentic pregame forecasts (generated and recorded before kickoff by an identified model) "
                      "joined by game ID to the selected provider's non-disputed closing spread",
        "all_authentic": describe(rows),
        "independently_verified_subset": describe([r for r in rows if r["publication_evidence"] == "independently_verified"]),
        "excluded": excluded,
        "excluded_reasons": {
            "not_generated_before_kickoff": "carried-forward entry without a pre-kickoff generation record",
            "non_fbs_matchup": "neither team is a current FBS program, so no licensed closing line exists",
            "game_not_in_archive": "the game has not been played yet or had no closing line in the archive",
            "spread_disputed": "providers disagreed by 3 or more points; excluded from the primary comparison",
        },
        "model_total": MODEL_TOTAL,
        "retrospective_replays": RETROSPECTIVE,
        "caveats": [
            "The closing line is observed at kickoff, after the forecast was recorded; the two are not simultaneous.",
            "Differences describe disagreement only. They are not edges, picks or evidence that either source is better; "
            "accuracy comparison on identical games is reserved for the Milestone 6 validation.",
            IMPLIED_PROBABILITY_NOTE,
        ],
    }


# ---------------------------------------------------------------- inputs, build, guard, write
def load_lines(lines_dir=LINES_DIR):
    out = {}
    for f in sorted(Path(lines_dir).glob("*.json")):
        payload = json.loads(f.read_text())
        out[payload["team"]] = payload["games"]
    if not out:
        raise MetricsRejected(f"no team line files in {lines_dir}")
    return out


def load_verified(path=VERIFIED):
    return {r["game_id"]: r for r in json.loads(Path(path).read_text())}


def build(lines_by_team, ledger, verified, generated_at):
    teams = {}
    for team, games in sorted(lines_by_team.items()):
        rows = [classify(g) for g in games]
        seasons = sorted({g["season"] for g in rows})
        current = seasons[-1] if seasons else None
        teams[team] = {"overall": team_block(rows),
                       "current_season": {"season": current, **team_block([g for g in rows if g["season"] == current])}}
    adequate = [t for t in teams.values() if t["overall"]["ats"]["sample"] == "adequate"]
    rows, excluded = comparison_rows(ledger, lines_by_team, verified)
    metrics = {
        "schema_version": SCHEMA_VERSION, "provider_policy_version": POLICY_VERSION, "generated_at": generated_at,
        "attribution": ATTRIBUTION,
        "methodology": {
            "primary_population": "games with the selected provider's non-disputed closing value and a final score",
            "rates": "pushes excluded from the denominator; Wilson 95% interval",
            "minimum_games_for_rate": MIN_RATE_GAMES, "adequate_sample_games": ADEQUATE_GAMES,
            "minimum_games_for_distribution": MIN_DISTRIBUTION_GAMES,
            "cover_margin": "team score minus opponent score plus team closing spread (positive = covered)",
            "total_margin": "combined points minus closing total (positive = over)",
            "implied_probability": IMPLIED_PROBABILITY_NOTE,
            "market_expectation": "sum of spread-implied win probabilities compared with actual wins; descriptive only",
            "limitations": ["Descriptive records are not predictions or future-win probabilities",
                            "Opening-line movement is not published: CFBD permission covers closing lines only",
                            "Disputed games are excluded from primary figures; ATS including disputed games is shown separately",
                            "Published teams are current FBS programs; games against FCS opponents count for the FBS team"],
        },
        "multiple_comparisons": {
            "teams_with_adequate_ats_sample": len(adequate),
            "teams_whose_ats_interval_excludes_50pct": sum(1 for t in adequate if t["overall"]["ats"]["ci_excludes_50"]),
            "expected_by_chance_at_5pct": round(0.05 * len(adequate), 1),
            "note": "With many teams, about 5% of 95% intervals exclude 50% by chance alone; an excluded interval is not proof of a lasting trend.",
        },
        "implied_probability_calibration": calibration(lines_by_team),
        "model_vs_market": comparison_summary(rows, excluded),
        "teams": teams,
    }
    files = {}
    for team in sorted(lines_by_team):
        team_rows = [r for r in rows if team in (r["home"], r["away"])]
        if team_rows:
            files[team_slug(team)] = {"schema_version": SCHEMA_VERSION, "team": team, "generated_at": generated_at,
                                      "attribution": ATTRIBUTION, "license": LINES_LICENSE,
                                      "forecast_kind": "authentic_pregame", "model_total": MODEL_TOTAL,
                                      "implied_probability_note": IMPLIED_PROBABILITY_NOTE, "games": team_rows}
    assert_metrics_safe(metrics)
    for payload in files.values():
        assert_comparison_safe(payload)
    return metrics, files


RESTRICTED_KEYS = {"spread", "total", "home_spread", "spread_open", "total_open", "moneyline", "provider",
                   "spread_provider", "total_provider", "game_id", "line", "lines"}
COMPARISON_GAME_KEYS = {"game_id", "season", "week", "kickoff", "home", "away", "neutral", "forecast_kind",
                        "publication_evidence", "model_id", "forecast_recorded_at", "hours_before_kickoff",
                        "model_home_win_probability", "market_home_win_probability", "probability_difference_points",
                        "model_home_margin", "home_spread", "spread_provider", "margin_difference_points",
                        "favorite_agreement", "home_score", "away_score"}


def assert_metrics_safe(obj, path="$"):
    """The aggregate file carries no per-game lines, game IDs, providers or model totals."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in RESTRICTED_KEYS:
                raise MetricsRejected(f"restricted key {k!r} at {path}")
            if "model_total" in k and k != "model_total":
                raise MetricsRejected(f"unsupported model-total output {k!r} at {path}")
            if k == "model_total" and v != MODEL_TOTAL:
                raise MetricsRejected("model totals are not produced by the incumbent model")
            assert_metrics_safe(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_metrics_safe(v, f"{path}[{i}]")


def assert_comparison_safe(payload):
    """Per-team comparison files: authentic forecasts only, one named provider, no model totals."""
    expected = {"schema_version", "team", "generated_at", "attribution", "license", "forecast_kind", "model_total",
                "implied_probability_note", "games"}
    if set(payload) != expected or payload["forecast_kind"] != "authentic_pregame" or payload["model_total"] != MODEL_TOTAL:
        raise MetricsRejected("unexpected comparison file structure")
    seen = set()
    for g in payload["games"]:
        if set(g) != COMPARISON_GAME_KEYS:
            raise MetricsRejected(f"unexpected comparison fields: {sorted(set(g) ^ COMPARISON_GAME_KEYS)}")
        if g["forecast_kind"] != "authentic_pregame":
            raise MetricsRejected("non-authentic forecast in comparison file")
        if not isinstance(g["spread_provider"], str) or not g["spread_provider"]:
            raise MetricsRejected("closing spread must carry exactly one named provider")
        if parse_time(g["forecast_recorded_at"]) >= parse_time(g["kickoff"]):
            raise MetricsRejected("forecast recorded at or after kickoff")
        if g["game_id"] in seen:
            raise MetricsRejected("duplicate game in comparison file")
        seen.add(g["game_id"])


def cross_check(metrics, team_history):
    """Independent recount must equal the M2 archive's team statistics exactly."""
    mismatches = []
    for team, t in team_history["teams"].items():
        mine = metrics["teams"].get(team)
        if mine is None:
            mismatches.append(f"{team}: missing")
            continue
        theirs, ours = t["overall"], mine["overall"]
        pairs = [("ats", theirs["ats"], {k: ours["ats"][k] for k in "wlp"}),
                 ("ou", theirs["ou"], {"o": ours["ou"]["o"], "u": ours["ou"]["u"], "p": ours["ou"]["p"]})]
        for v in VENUES:
            pairs.append((f"{v}.ats", theirs["splits"][v]["ats"], {k: ours["splits"]["venue"][v]["ats"][k] for k in "wlp"}))
            pairs.append((f"{v}.ou", theirs["splits"][v]["ou"], {k: ours["splits"]["venue"][v]["ou"][k] for k in "oup"}))
        for r in ROLES:
            pairs.append((f"{r}.ats", theirs["splits"][r]["ats"], {k: ours["splits"]["role"][r]["ats"][k] for k in "wlp"}))
        for name, a, b in pairs:
            if a != b:
                mismatches.append(f"{team} {name}: archive {a} vs metrics {b}")
    if set(metrics["teams"]) != set(team_history["teams"]):
        mismatches.append("team sets differ")
    return mismatches


def serialize(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def generate(lines_dir=LINES_DIR, ledger_path=LEDGER, verified_path=VERIFIED, history_path=TEAM_HISTORY):
    lines = load_lines(lines_dir)
    history = json.loads(Path(history_path).read_text())
    generated_at = history["generated_at"]
    metrics, files = build(lines, json.loads(Path(ledger_path).read_text()), load_verified(verified_path), generated_at)
    problems = cross_check(metrics, history)
    if problems:
        raise MetricsRejected("metrics disagree with the M2 archive: " + "; ".join(problems[:5]))
    return metrics, files


def write(metrics, files, public=PUBLIC, comparison_dir=COMPARISON_DIR):
    """Atomic: stage everything, then swap the directory and the file."""
    comparison_dir = Path(comparison_dir)
    staged = comparison_dir.with_name(comparison_dir.name + ".tmp")
    if staged.exists():
        for f in staged.iterdir():
            f.unlink()
        staged.rmdir()
    staged.mkdir(parents=True)
    for slug, payload in files.items():
        (staged / f"{slug}.json").write_text(serialize(payload))
    tmp = Path(str(public) + ".tmp")
    tmp.write_text(serialize(metrics))
    old = comparison_dir.with_name(comparison_dir.name + ".old")
    if comparison_dir.exists():
        comparison_dir.rename(old)
    staged.rename(comparison_dir)
    tmp.replace(public)
    if old.exists():
        for f in old.iterdir():
            f.unlink()
        old.rmdir()


def check(metrics, files, public=PUBLIC, comparison_dir=COMPARISON_DIR):
    differences = []
    if Path(public).read_text() != serialize(metrics):
        differences.append(str(public))
    existing = {f.stem for f in Path(comparison_dir).glob("*.json")}
    if existing != set(files):
        differences.append(f"{comparison_dir}: file set differs")
    for slug, payload in files.items():
        f = Path(comparison_dir) / f"{slug}.json"
        if f.exists() and f.read_text() != serialize(payload):
            differences.append(str(f))
    return differences


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="regenerate in memory and require byte-identical outputs")
    args = parser.parse_args(argv)
    metrics, files = generate()
    if args.check:
        differences = check(metrics, files)
        if differences:
            print("metrics outputs differ: " + ", ".join(differences), file=sys.stderr)
            return 1
        print("check: byte-identical")
        return 0
    write(metrics, files)
    s = metrics["model_vs_market"]
    print(f"teams: {len(metrics['teams'])}; calibration games: {metrics['implied_probability_calibration']['games']}; "
          f"authentic comparisons: {s['all_authentic']['games']} (verified {s['independently_verified_subset']['games']}); "
          f"comparison files: {len(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
