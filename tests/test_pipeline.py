import pytest
from cfb_analytics.pipeline import build_season_report


ROSTER = [
    {"name": "A", "conference": "ACC", "prior": 10},
    {"name": "B", "conference": "ACC", "prior": -10},
    {"name": "C", "conference": "Independent", "prior": 0},
]


def game(game_id, home, away, *, completed=False, hs=None, ass=None, neutral=False):
    return {"game_id": game_id, "season": 2026, "week": game_id,
            "home": home, "away": away, "completed": completed,
            "home_score": hs, "away_score": ass, "neutral_site": neutral}


def test_complete_season_pipeline():
    snapshot = {"season": 2026, "source": "test", "games": [
        game(1, "A", "B", completed=True, hs=28, ass=14),
        game(2, "B", "A"),
        game(3, "C", "FCS", neutral=True),
    ]}
    report = build_season_report(snapshot, ROSTER)
    assert report["summary"] == {"teams": 3, "completed_games": 1, "upcoming_games": 2}
    assert len(report["rankings"]) == 3
    assert {r["rank"] for r in report["rankings"]} == {1, 2, 3}
    a = next(r for r in report["rankings"] if r["team"] == "A")
    assert a["wins"] == 1
    assert a["projected_conference_wins"] > 1
    assert len(report["predictions"]) == 2
    assert all(0 <= p["home_win_probability"] <= 1 for p in report["predictions"])


def test_reject_mixed_seasons():
    with pytest.raises(ValueError):
        build_season_report({"season": 2026, "games": [
            {**game(1, "A", "B"), "season": 2025}
        ]}, ROSTER)


def test_reject_duplicate_game_ids():
    g = game(1, "A", "B")
    with pytest.raises(ValueError):
        build_season_report({"season": 2026, "games": [g, g]}, ROSTER)
