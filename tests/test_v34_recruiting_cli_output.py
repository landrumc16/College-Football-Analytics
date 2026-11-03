import json
from cfb_analytics.v34_recruiting_evaluation_cli import main


def test_cli_writes_parseable_json(tmp_path):
    input_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "report.json"
    input_path.write_text(json.dumps({"classes": [], "games_by_season": {},
                         "fbs_teams_by_season": {}, "completed_seasons": []}), encoding="utf-8")
    main(["--input", str(input_path), "--output", str(output_path)])
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["joined_team_seasons"] == 0
    assert result["historical_asof_verified"] is False
