"""V7 M6 historical validation: hand-computed fixtures and committed-output checks."""
import json
import math
import re
from pathlib import Path

import pytest

from cfb_analytics import v7_validation as v

ROOT = Path(__file__).resolve().parents[1]


def row(gid, opp, ts, os_, venue="home", spread=-3.0, total=50.0, ats=None, ou=None, season=2024):
    margin = ts - os_
    if ats is None and spread is not None:
        c = margin + spread
        ats = "W" if c > 0 else "L" if c < 0 else "P"
    if ou is None and total is not None:
        d = ts + os_ - total
        ou = "O" if d > 0 else "U" if d < 0 else "P"
    return {"game_id": gid, "season": season, "opponent": opp, "venue": venue, "team_score": ts, "opponent_score": os_,
            "spread": spread, "spread_status": "ok" if spread is not None else "no_line", "total": total,
            "total_status": "ok" if total is not None else "no_line", "ats": ats, "ou": ou}


INDEX = {"1": ("Alpha", "Beta", 30, 20, False), "2": ("Gamma", "Alpha", 17, 24, True)}


def test_integrity_passes_consistent_rows_from_both_sides():
    lines = {"Alpha": [row("1", "Beta", 30, 20), row("2", "Gamma", 24, 17, venue="neutral")],
             "Beta": [row("1", "Alpha", 20, 30, venue="away", spread=3.0)]}
    report, problems = v.integrity(lines, INDEX)
    assert problems == [] and report["team_game_rows_checked"] == 3 and report["status"] == "passed"


@pytest.mark.parametrize("bad,kind", [
    (row("1", "Beta", 31, 20), "identity/score"),          # score differs from verified source
    (row("1", "Beta", 30, 20, venue="away"), "identity/score"),
    (row("1", "Beta", 30, 20, ats="L"), "ATS"),             # 30-20-3 is a cover
    (row("1", "Beta", 30, 20, ou="U"), "O/U"),              # 50 points on 50 is a push
    (row("9", "Beta", 30, 20), "not in verified"),
])
def test_integrity_detects_tampering(bad, kind):
    _, problems = v.integrity({"Alpha": [bad]}, INDEX)
    assert problems and kind in problems[0]


def test_national_favorite_home_and_over_rates():
    lines = {"A": [row("1", "B", 30, 20, spread=-7),        # fav covers (3)
                   row("2", "C", 21, 20, spread=-7),        # fav fails
                   row("3", "D", 20, 13, spread=-7, total=33),  # push, total push
                   row("4", "E", 10, 20, spread=3.5)]}      # dog (A) loses by 10: favourite (E) covers
    n = v.national(lines)
    assert n["favorite_cover"]["n"] == 3 and n["favorite_cover"]["rate"] == round(2 / 3, 4) and n["favorite_cover"]["pushes"] == 1
    assert n["home_cover_non_neutral"]["n"] == 3 and n["home_cover_non_neutral"]["pushes"] == 1
    assert n["over"]["pushes"] == 2            # 30+20 on 50 and 20+13 on 33


def test_scoring_rules_hand_values():
    assert v.brier(0.8, 1) == pytest.approx(0.04)
    assert v.logloss(0.8, 1) == pytest.approx(-math.log(0.8))
    assert v.logloss(0.0, 1) == pytest.approx(-math.log(v.EPS))           # clipped, finite
    s = v.scores([{"y": 1, "p": 0.8}, {"y": 0, "p": 0.6}, {"y": 1, "p": 0.5}], "p")
    assert s["brier"] == round((0.04 + 0.36 + 0.25) / 3, 4)
    assert s["winner_accuracy"] == round((1 + 0 + 0.5) / 3, 4)


def test_bootstrap_is_deterministic_and_brackets_the_mean():
    xs = [0.1, -0.2, 0.05, 0.3, -0.1, 0.0, 0.2, -0.05, 0.15, 0.1]
    a, b = v.paired_bootstrap(xs), v.paired_bootstrap(xs)
    assert a == b and a[0] <= sum(xs) / len(xs) <= a[1]
    assert v.paired_bootstrap([0.5] * 10) == [0.5, 0.5]


def synthetic(n, model_shift):
    rows = []
    for i in range(n):
        market = 0.3 + 0.4 * (i % 5) / 4
        rows.append({"y": int(i % 3 != 0), "model": min(max(market + model_shift, 0.01), 0.99), "market": market,
                     "model_margin": 3.0, "market_margin": 2.0, "actual_margin": 5.0 if i % 3 else -5.0})
    return rows


def test_evaluate_reports_na_below_ten_games_and_conclusion_branches():
    assert v.evaluate(synthetic(9, 0), "x")["na_reason"]
    same = v.evaluate(synthetic(30, 0.0), "x")
    assert same["paired_differences_model_minus_market"]["brier"] == {"mean": 0.0, "ci95": [0.0, 0.0]}
    assert same["conclusion"].startswith("Inconclusive") and same["conclusion"].endswith("No model-market disagreement to evaluate.")
    worse = v.evaluate(synthetic(60, -0.25), "x")       # model pushed away from outcomes that are mostly wins
    assert worse["paired_differences_model_minus_market"]["brier"]["ci95"][0] > 0
    assert worse["conclusion"].startswith("The closing-spread market was more accurate")


def test_comparison_population_rejects_non_authentic(tmp_path):
    game = {"game_id": "1", "home_score": 21, "away_score": 14, "forecast_kind": "retrospective_replay",
            "model_home_win_probability": 0.6, "home_spread": -3, "model_home_margin": 4.0, "publication_evidence": "x",
            "week": 10, "kickoff": "k", "forecast_recorded_at": "r", "hours_before_kickoff": 50}
    (tmp_path / "a.json").write_text(json.dumps({"games": [game]}))
    with pytest.raises(v.ValidationFailed):
        v.comparison_population(tmp_path)


def test_committed_validation_reproduces(monkeypatch):
    monkeypatch.chdir(ROOT)
    assert v.OUTPUT.read_text() == v.serialize(v.build())


def test_committed_findings_match_independent_v5_evaluation(monkeypatch):
    monkeypatch.chdir(ROOT)
    r = json.loads(v.OUTPUT.read_text())
    assert r["archive_integrity"]["status"] == "passed" and r["archive_integrity"]["team_game_rows_checked"] > 17000
    verified = r["model_vs_market"]["independently_verified"]
    v5 = json.loads((ROOT / "web/public/v5-forecast-evaluation.json").read_text())["models"]["workbook_2026_baseline"]
    assert verified["games"] == v5["games"] == 65
    assert verified["model"]["brier"] == round(v5["brier"], 4)
    assert verified["model"]["winner_accuracy"] == round(v5["accuracy"], 4)
    assert r["model_vs_market"]["model_total"]["status"] == "not_available"
    for key in ("favorite_cover", "home_cover_non_neutral", "over"):
        lo, hi = r["national_market_checks"][key]["ci95"]
        assert lo < 0.5 + 0.02 and hi > 0.5 - 0.02
    text = json.dumps(r).lower()
    assert "profitable betting strategy" in text and not re.search(r"\bedges?\b|\bpicks?\b|\block\b", text)
