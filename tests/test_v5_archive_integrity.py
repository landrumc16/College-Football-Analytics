"""Offline V5 archive retention checks."""
import hashlib
import json
from zipfile import ZipFile

from cfb_analytics.v5_archive_integrity import verify_archive


def archive(tmp_path, tamper=False):
    path = tmp_path / "research.zip"
    source = b"retained source bytes"
    games = b"[]"
    manifest = {"seasons": {"2025": {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "extracted_sha256": hashlib.sha256(games).hexdigest(),
        "extracted_games": 0,
        "source_bytes": len(source),
        "completed_fbs_vs_fbs": 0,
        "completed_fbs_vs_other": 0,
    }}}
    with ZipFile(path, "w") as z:
        z.writestr("coverage.json", json.dumps(manifest))
        z.writestr("cfb_schedules_2025.parquet", source if not tamper else b"modified")
        z.writestr("games_2025.json", games)
    return path


def test_retained_bytes_replay_without_network(tmp_path):
    result = verify_archive(archive(tmp_path))
    assert result["status"] == "pass"
    assert result["seasons_checked"] == 1
    assert result["scope"] == "integrity_only_not_independent_source_verification"


def test_source_tampering_fails_closed(tmp_path):
    result = verify_archive(archive(tmp_path, tamper=True))
    assert result["status"] == "fail"
    assert any("checksum mismatch" in failure for failure in result["failures"])


def test_malformed_game_row_reports_failure_not_exception(tmp_path):
    path = tmp_path / "malformed.zip"
    source = b"retained source bytes"
    games = json.dumps([None]).encode()
    manifest = {"seasons": {"2025": {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "extracted_sha256": hashlib.sha256(games).hexdigest(),
        "extracted_games": 1,
        "source_bytes": len(source),
        "completed_fbs_vs_fbs": 0,
        "completed_fbs_vs_other": 1,
    }}}
    with ZipFile(path, "w") as z:
        z.writestr("coverage.json", json.dumps(manifest))
        z.writestr("cfb_schedules_2025.parquet", source)
        z.writestr("games_2025.json", games)
    result = verify_archive(path)
    assert result["status"] == "fail"
    assert any("identifiers" in failure or "season labels" in failure
               for failure in result["failures"])
