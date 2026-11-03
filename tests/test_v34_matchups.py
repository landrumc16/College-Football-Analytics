import pytest
from cfb_analytics.v34_matchups import matchup_scheme_diagnostics


def game():
    return {"game_id": 1, "home": "Georgia", "away": "Alabama",
            "kickoff": "2025-10-04T20:00:00Z"}


def scheme(team, value, published):
    return {"team": team, "feature": "pass_rate", "value": value,
            "source": "official play-by-play", "observed_at": published,
            "published_at": published}


def test_matchup_excludes_future_observations():
    rows = [scheme("Georgia", .60, "2025-10-03T12:00:00Z"),
            scheme("Alabama", .45, "2025-10-03T12:00:00Z"),
            scheme("Georgia", .99, "2025-10-05T12:00:00Z")]
    result = matchup_scheme_diagnostics([game()], rows,
                   cutoff_by_game={1: "2025-10-04T19:00:00Z"})
    item = result["matchups"][0]
    assert item["covered_metrics"] == 1
    assert item["comparisons"][0]["home_minus_away"] == pytest.approx(.15)
    assert item["missing_metrics"] == 5


def test_cutoff_after_kickoff_rejected():
    with pytest.raises(ValueError, match="pre-kickoff"):
        matchup_scheme_diagnostics([game()], [],
                       cutoff_by_game={1: "2025-10-04T20:00:00Z"})
