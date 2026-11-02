"""End-to-end V3 archived forecast CLI contract."""
import json

import pytest

from cfb_analytics.v3_cli import run


def test_cli_matched_archived_forecasts(tmp_path):
    games = [{
        "season": 2025, "game_id": 9, "home": "A", "away": "B",
        "home_division": "FBS", "away_division": "FBS",
        "kickoff": "2025-09-01T18:00:00Z",
        "source_retrieved_at": "2025-09-02T02:00:00Z",
        "source": "fixture", "home_score": 24, "away_score": 10,
    }]
    def forecast(p):
        return [{"season": 2025, "game_id": 9,
                 "home_win_probability": p,
                 "generated_at": "2025-09-01T17:00:00Z",
                 "input_retrieved_at": "2025-09-01T16:00:00Z"}]
    paths = [tmp_path / name for name in ("games.json", "baseline.json", "candidate.json")]
    for path, rows in zip(paths, (games, forecast(.6), forecast(.8))):
        path.write_text(json.dumps(rows))
    result = run(*paths)
    assert result["groups"]["holdout/all"]["baseline"]["games"] == 1
    assert result["groups"]["holdout/all"]["candidate"]["brier"] == pytest.approx(.04)


def test_cli_duplicate_forecast_fails(tmp_path):
    games = tmp_path / "games.json"
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    games.write_text("[]")
    duplicate = {"season": 2025, "game_id": 9, "home_win_probability": .6,
                 "generated_at": "2025-09-01T17:00:00Z",
                 "input_retrieved_at": "2025-09-01T16:00:00Z"}
    baseline.write_text(json.dumps([duplicate, duplicate]))
    candidate.write_text("[]")
    with pytest.raises(ValueError, match="Duplicate forecast"):
        run(games, baseline, candidate)
