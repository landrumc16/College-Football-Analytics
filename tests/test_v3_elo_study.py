"""V3 study regression: chronology, holdout, FCS and no leakage."""
import json

import pytest

from scripts.v3_elo_study import evaluate, study


def game(year, gid, day, home="A", away="B", hd="FBS", ad="FBS",
         hs=21, ass=14):
    return {"season": year, "game_id": gid,
            "kickoff": f"{year}-09-{day:02d}T12:00:00Z",
            "home": home, "away": away, "home_division": hd,
            "away_division": ad, "home_score": hs, "away_score": ass,
            "neutral_site": True}


def test_same_day_result_not_leaked():
    games = [game(2024, 1, 1, away="FCS1", ad="FCS"),
             {**game(2024, 2, 1, away="B"), "kickoff": "2024-09-01T14:00:00Z"}]
    r = evaluate(games, holdout=2025)
    # FCS contributes to subsequent ratings, but not same-day early kickoff.
    assert r["development"]["games"] == 1
    assert r["development"]["brier"] == pytest.approx(.25)


def test_fcs_changes_later_rating():
    games = [game(2024, 1, 1, away="FCS1", ad="FCS"),
             game(2024, 2, 2, away="B")]
    r = evaluate(games, holdout=2025)
    assert r["development"]["games"] == 1
    assert r["fbs_fcs"]["development"]["games"] == 1
    assert r["development"]["brier"] < .25


def test_holdout_is_separate_and_selection_is_development_only(tmp_path):
    games = [game(2024, 1, 1), game(2025, 2, 1)]
    p = tmp_path / "games.json"
    p.write_text(json.dumps(games))
    r = study([p])
    assert len(r["candidates"]) == 5
    assert r["selected"]["development"]["games"] == 1
    assert r["selected"]["holdout"]["games"] == 1
    assert r["promotion_authorized"] is False
    assert r["holdout_is_not_used_for_selection"] is True


def test_duplicate_rejected():
    g = game(2024, 1, 1)
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate([g, g])
