import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('snapshot', Path(__file__).parents[1] / 'scripts/v9_strength_snapshot.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_snapshot_retry_preserves_original_retention_and_payload(tmp_path):
    report = Path(__file__).parents[1] / 'data/season-2026-report.json'
    target = module.archive(report, tmp_path, 'a' * 40)
    original = target.read_bytes()
    assert module.archive(report, tmp_path, 'a' * 40) == target
    assert target.read_bytes() == original
    assert len(json.loads(original)['teams']) == 138
    assert len(list(tmp_path.iterdir())) == 1


def test_invalid_commit_creates_no_archive(tmp_path):
    with pytest.raises(ValueError):
        module.archive('missing.json', tmp_path / 'archive', 'main')
    assert not (tmp_path / 'archive').exists()


def test_tampered_existing_snapshot_is_rejected(tmp_path):
    report = Path(__file__).parents[1] / 'data/season-2026-report.json'
    target = module.archive(report, tmp_path, 'a' * 40)
    value = json.loads(target.read_text())
    value['teams'][0]['rating'] += 1
    target.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='identity conflict'):
        module.archive(report, tmp_path, 'a' * 40)
    assert json.loads(target.read_text()) == value
