"""CLI integration checks for versioned multi-season historical evaluation."""
import json

from cfb_analytics.historical_cli import main, run


def test_cli_deterministic_multiseason(tmp_path, capsys):
    games = []
    forecasts = []
    for season, game_id in [(2024, 1), (2025, 2)]:
        games.append({
            "season": season, "game_id": game_id, "home": "A", "away": "B",
            "home_division": "FBS", "away_division": "FBS",
            "kickoff": f"{season}-09-01T20:00:00Z",
            "source_retrieved_at": f"{season}-09-01T17:00:00Z",
            "source": "fixture", "home_score": 21, "away_score": 14})
        forecasts.append({
            "season": season, "game_id": game_id,
            "home_win_probability": 0.75,
            "generated_at": f"{season}-09-01T18:00:00Z"})
    game_file = tmp_path / "games.json"
    forecast_file = tmp_path / "forecasts.json"
    output = tmp_path / "results.json"
    game_file.write_text(json.dumps(games))
    forecast_file.write_text(json.dumps(forecasts))
    assert main(["--games", str(game_file), "--forecasts", str(forecast_file),
                 "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["games"] == 2
    assert sorted(result["by_season"]) == ["2024", "2025"]
    assert result["metrics"]["brier_score"] == 0.0625
    assert run(game_file, forecast_file) == result
