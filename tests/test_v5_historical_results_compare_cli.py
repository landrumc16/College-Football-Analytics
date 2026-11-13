import json
import subprocess
import sys

def test_comparison_cli_produces_review_only_artifact(tmp_path):
    a = tmp_path / "first.json"
    b = tmp_path / "second.json"
    output = tmp_path / "comparison.json"
    rows = {"seasons": [{"season": 2024, "teams": [
        {"team": "Alpha", "fbs_wins": 9, "fbs_losses": 3}
    ]}]}
    a.write_text(json.dumps(rows))
    b.write_text(json.dumps(rows))
    command = [sys.executable, "-m", "cfb_analytics.v5_historical_results_compare_cli",
               "--primary", str(a), "--primary-source", "https://example.org/first",
               "--independent", str(b), "--independent-source", "https://example.org/second",
               "--output", str(output)]
    completed = subprocess.run(command, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(output.read_text())
    assert result["matching_count"] == 1
    assert result["exception_count"] == 0
    assert result["source_independence_attested"] is False
    assert result["status"] == "comparison_only_requires_independence_review"


def test_comparison_cli_rejects_same_input_file(tmp_path):
    archive = tmp_path / "archive.json"
    archive.write_text('{"seasons":[]}')
    completed = subprocess.run(
        [sys.executable, "-m", "cfb_analytics.v5_historical_results_compare_cli",
         "--primary", str(archive), "--independent", str(archive),
         "--independent-source", "https://example.org/second"],
        capture_output=True, text=True)
    assert completed.returncode != 0
    assert "different file" in completed.stderr
