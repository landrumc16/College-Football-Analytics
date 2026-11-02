from cfb_analytics.historical import HistoricalGame
from cfb_analytics.v3_evaluation import evaluate_matched


def game(season=2025, away_division="FBS"):
    return HistoricalGame(season=season, game_id=1, home="A", away="B",
        home_division="FBS", away_division=away_division,
        kickoff=f"{season}-09-01T18:00:00Z",
        source_retrieved_at=f"{season}-09-02T00:00:00Z",
        source="fixture", home_score=21, away_score=7)


def forecast(p=.8, season=2025):
    return (p, f"{season}-09-01T17:00:00Z", f"{season}-09-01T16:00:00Z")


def test_matched_holdout_and_calibration():
    result = evaluate_matched([game()], {(2025, 1): forecast(.6)},
                              {(2025, 1): forecast(.8)})
    metrics = result["groups"]["holdout/fbs_vs_fbs"]["candidate"]
    assert metrics["games"] == 1
    assert round(metrics["brier"], 4) == .04
    assert metrics["calibration"][0]["observed"] == 1


def test_invalid_pregame_provenance_excluded():
    late = (.9, "2025-09-01T19:00:00Z", "2025-09-01T16:00:00Z")
    result = evaluate_matched([game()], {(2025, 1): forecast()},
                              {(2025, 1): late})
    assert result["groups"] == {}
    assert result["exclusions"]["invalid_pregame_provenance"] == 1


def test_fcs_scored_separately():
    result = evaluate_matched([game(away_division="FCS")],
                              {(2025, 1): forecast()},
                              {(2025, 1): forecast()})
    assert result["groups"]["holdout/fbs_vs_fcs"]["candidate"]["games"] == 1
