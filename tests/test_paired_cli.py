"""End-to-end JSON benchmark execution using explicitly archived pregame snapshots."""
import json

from cfb_analytics.paired_cli import main, run


def test_matched_benchmark_cli(tmp_path, capsys):
    game = {
        "season": 2025, "game_id": 1, "home": "A", "away": "B",
        "home_division": "FBS", "away_division": "FBS",
        "kickoff": "2025-09-01T20:00:00Z",
        "source_retrieved_at": "2025-09-02T12:00:00Z",
        "source": "fixture", "home_score": 28, "away_score": 21,
    }
    forecast = {
        "season": 2025, "game_id": 1,
        "generated_at": "2025-09-01T18:00:00Z",
        "input_retrieved_at": "2025-09-01T17:00:00Z",
    }
    paths = [tmp_path / name for name in ("games.json", "workbook.json", "candidate.json")]
    for path, data in zip(paths, [[game], [{**forecast, "home_win_probability": 0.6}],
                                  [{**forecast, "home_win_probability": 0.8}]]):
        path.write_text(json.dumps(data))
    output = tmp_path / "scorecard.json"
    assert main(["--games", str(paths[0]), "--workbook", str(paths[1]),
                 "--candidate", str(paths[2]), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["paired_games"] == 1
    assert result["eligible_completed_games"] == 1
    assert result["excluded"] == {"ineligible_game": 0, "missing_workbook": 0,
                                  "missing_candidate": 0, "not_verified_pregame": 0}
    assert round(result["workbook"]["brier_score"], 8) == 0.16
    assert round(result["candidate"]["brier_score"], 8) == 0.04
    assert run(*paths) == result
