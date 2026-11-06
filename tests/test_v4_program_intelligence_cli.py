import json
import subprocess
import sys


def test_cli_refuses_unreviewed_and_incomplete_publication(tmp_path):
    strength = tmp_path / "strength.json"
    polls = tmp_path / "polls.json"
    output = tmp_path / "published.json"
    source = "sha256:" + "a" * 64
    strength.write_text(json.dumps([
        dict(team="A", season=y, strength=10.0, source=source)
        for y in range(2016, 2026)
    ]))
    polls.write_text(json.dumps([
        dict(team="A", season=y, poll="AP", preseason_rank=5,
             final_rank=8, source=source)
        for y in range(2016, 2026)
    ]))
    args = [sys.executable, "-m", "cfb_analytics.v4_program_intelligence_cli",
            "--strength-input", str(strength), "--poll-input", str(polls),
            "--latest-completed-season", "2025", "--output", str(output)]
    blocked = subprocess.run(args, capture_output=True, text=True)
    assert blocked.returncode != 0
    assert "independent review" in blocked.stderr
    assert not output.exists()
    allowed = subprocess.run(args + ["--reviewed-sources"], capture_output=True, text=True)
    assert allowed.returncode == 0, allowed.stderr
    report = json.loads(output.read_text())
    assert report["source_review_attested"] is True
    assert report["provenance_diagnostics"]["source_authenticity_verified"] is False


def test_cli_refuses_empty_sources_even_with_attestation(tmp_path):
    a, b, out = [tmp_path / n for n in ("a.json", "b.json", "out.json")]
    a.write_text("[]")
    b.write_text("[]")
    result = subprocess.run([sys.executable, "-m", "cfb_analytics.v4_program_intelligence_cli",
        "--strength-input", str(a), "--poll-input", str(b),
        "--latest-completed-season", "2025", "--output", str(out),
        "--reviewed-sources"], capture_output=True, text=True)
    assert result.returncode != 0
    assert not out.exists()
