import pytest
from cfb_analytics.pipeline import build_season_report


ROSTER = [
    {"name": "A", "conference": "ACC", "prior": 10},
    {"name": "B", "conference": "ACC", "prior": -10},
    {"name": "C", "conference": "Independent", "prior": 0},
] + [
    {"name": f"Fixture {i}", "conference": f"Fixture League {i // 2}", "prior": -20}
    for i in range(9)
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
    assert report["summary"] == {"teams": 12, "completed_games": 1, "upcoming_games": 2}
    assert len(report["rankings"]) == 12
    assert {r["rank"] for r in report["rankings"]} == set(range(1, 13))
    a = next(r for r in report["rankings"] if r["team"] == "A")
    assert a["wins"] == 1
    assert a["projected_conference_wins"] > 1
    assert len(report["projected_bracket"]["seeds"]) == 12
    assert len(report["projected_bracket"]["first_round"]) == 4
    assert sum(seed["bid"] == "automatic" for seed in report["projected_bracket"]["seeds"]) == 5
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


def test_reject_completed_game_with_missing_score():
    with pytest.raises(ValueError, match="missing score"):
        build_season_report({"season": 2026, "games": [
            game(1, "A", "B", completed=True, hs=None, ass=7)
        ]}, ROSTER)


def test_report_preserves_data_provenance():
    report = build_season_report({"season": 2026, "source": "test-source",
                                  "retrieved_at": "2026-10-31T00:00:00+00:00",
                                  "data_changed_at": "2026-10-30T00:00:00+00:00",
                                  "games": []}, ROSTER)
    assert report["source"] == "test-source"
    assert report["retrieved_at"] == "2026-10-31T00:00:00+00:00"
    assert report["data_changed_at"] == "2026-10-30T00:00:00+00:00"


def test_reject_empty_roster():
    with pytest.raises(ValueError, match="Roster"):
        build_season_report({"season": 2026, "games": []}, [])


def test_reject_self_matchup():
    with pytest.raises(ValueError, match="self-matchup"):
        build_season_report({"season": 2026, "games": [game(1, "A", "A")]}, ROSTER)
