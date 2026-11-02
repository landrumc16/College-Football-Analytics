"""Retrospective baseline: chronological integrity and FCS accounting."""
import json
from scripts.walkforward_baseline import run


def game(id, kickoff, home, away, hd="FBS", ad="FBS", hs=21, ass=14):
    return {"season": 2025, "game_id": id, "kickoff": kickoff,
            "home": home, "away": away, "home_division": hd,
            "away_division": ad, "home_score": hs, "away_score": ass,
            "neutral_site": True}


def test_same_kickoff_predictions_are_independent(tmp_path):
    t = "2025-09-01T12:00:00Z"
    games = [game(1, t, "A", "B"), game(2, t, "A", "C")]
    source = tmp_path / "games.json"
    source.write_text(json.dumps(games))
    result = run([source], tmp_path / "out")
    predictions = json.loads((tmp_path / "out" / "walkforward_predictions.json").read_text())
    assert result["overall"]["games"] == 2
    assert [x["home_probability"] for x in predictions] == [0.5, 0.5]


def test_fcs_updates_rating_but_not_fbs_accuracy(tmp_path):
    games = [game(1, "2025-09-01T12:00:00Z", "A", "FCS1", ad="FCS"),
             game(2, "2025-09-02T12:00:00Z", "A", "B")]
    source = tmp_path / "games.json"
    source.write_text(json.dumps(games))
    report = run([source], tmp_path / "out")
    preds = json.loads((tmp_path / "out" / "walkforward_predictions.json").read_text())
    assert report["overall"]["games"] == 1
    assert preds[0]["home_probability"] > 0.5


def test_duplicate_game_rejected(tmp_path):
    import pytest
    g = game(1, "2025-09-01T12:00:00Z", "A", "B")
    source = tmp_path / "games.json"
    source.write_text(json.dumps([g, g]))
    with pytest.raises(ValueError, match="Duplicate game"):
        run([source], tmp_path / "out")
