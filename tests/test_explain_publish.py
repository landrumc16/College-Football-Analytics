"""'Why this prediction?' data: exact decompositions of the published forecasts, never a new model."""
import json
from pathlib import Path

import pytest

from cfb_analytics import dual_publish as pub
from cfb_analytics import explain_publish as ex


@pytest.fixture(scope="module")
def inputs():
    report = json.loads(Path("data/season-2026-report.json").read_text())
    snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
    evaluation = json.loads(pub.EVAL.read_text())
    membership = json.loads(Path("research/v8/fbs-membership.json").read_text())
    return report, snapshot, evaluation, membership


@pytest.fixture(scope="module")
def built(inputs):
    return ex.build(*inputs)


def test_official_parts_rebuild_every_published_margin(inputs, built):
    report = inputs[0]
    published = {p["game_id"]: p for p in report["predictions"]}
    assert len(built["games"]) >= 100
    for g in built["games"]:
        o = g["official"]
        assert abs(o["home_margin"] - published[g["game_id"]]["home_margin"]) < 1e-3
        assert abs(o["season_games"] + o["preseason_prior"] + o["home_field"] - o["home_margin"]) < 2e-3
        assert o["home_field"] == (0.0 if g["neutral_site"] else 3.0)


def test_standard_and_momentum_parts_equal_the_published_dual_projections(inputs, built):
    """Built from the same inputs, every explained Standard/Momentum margin equals dual_publish.build exactly."""
    report, snapshot, evaluation, membership = inputs
    dual = pub.build(report, snapshot, evaluation, membership)
    to_report = pub.report_names(set(membership[str(snapshot["season"])]))
    by_pair = {(to_report.get(g["home"], g["home"]), to_report.get(g["away"], g["away"])): g for g in dual["games"]}
    for g in built["games"]:
        d = by_pair[(g["home"], g["away"])]
        for k in ("standard", "momentum"):
            part = g[k]
            assert abs(part["home_margin"] - d[k]["home_margin"]) < 0.01
            assert abs(part["home_win_probability"] - d[k]["home_win_probability"]) < 1e-3
            assert abs(part["season_games"] + part["preseason_prior"] + part["home_field"] - part["home_margin"]) < 2e-3
            assert abs(part["home_points"] - part["away_points"] - part["home_margin"]) < 2e-3


# The matchup audit was a point-in-time analysis of this exact pregame snapshot. Any later refresh (other teams'
# results move opponent ratings) legitimately changes these values, so the pinned numbers apply only to it; the
# decomposition tests above hold for every snapshot. Pinning them to live data blocked the game-day refresh.
AUDIT_SNAPSHOT = "2026-11-20T06:48:33.393964+00:00"


def test_texas_tech_at_baylor_matches_the_matchup_audit(inputs, built):
    if inputs[1].get("retrieved_at") != AUDIT_SNAPSHOT:
        pytest.skip("audit values apply only to the audited pregame snapshot; decomposition is checked for every snapshot")
    g = next(x for x in built["games"] if x["home"] == "Baylor" and x["away"] == "Texas Tech")
    # Points of home (Baylor) margin: the audit found TT +4.46 from carry-over, Baylor +0.38 from this season, +3.0 home.
    assert abs(g["official"]["preseason_prior"] + 4.455) < 0.01
    assert abs(g["official"]["season_games"] - 0.381) < 0.01
    assert abs(g["official"]["home_margin"] + 1.075) < 0.01
    assert abs(g["standard"]["home_margin"] + 0.92) < 0.02 and abs(g["momentum"]["home_margin"] + 2.27) < 0.02
    tt = built["teams"]["Texas Tech"]
    assert tt["weakest_game"]["opponent"] == "Abilene Christian" and tt["weakest_game"]["opponent_fbs"] is False
    assert tt["official_games_average"] == pytest.approx(15.22, abs=0.01)
    assert built["teams"]["Baylor"]["official_games_average"] == pytest.approx(15.79, abs=0.01)


def test_unavailable_inputs_are_listed_not_inferred(built):
    assert any("Quarterback" in u for u in built["unavailable"])
    assert all("quarterback" not in json.dumps(t).lower() for t in built["teams"].values())


def test_mismatched_official_rating_stops_publishing(inputs):
    report, snapshot, evaluation, membership = inputs
    tampered = json.loads(json.dumps(report))
    tampered["rankings"][0]["rating"] += 0.5
    with pytest.raises(ValueError, match="does not reproduce"):
        ex.build(tampered, snapshot, evaluation, membership)


def test_published_file_matches_the_committed_report():
    data = json.loads(Path("web/public/prediction-explanations.json").read_text())
    report = json.loads(Path("data/season-2026-report.json").read_text())
    if data["report_retrieved_at"] != report["retrieved_at"]:
        pytest.skip("routine data refresh since the explanations were generated; the deploy regenerates both")
    published = {p["game_id"]: p for p in report["predictions"]}
    assert all(abs(g["official"]["home_margin"] - published[g["game_id"]]["home_margin"]) < 1e-3 for g in data["games"])
