"""Real-data offline publication and model-preservation checks."""
import hashlib
import json
import subprocess
from pathlib import Path
import os
import pytest

# These tests build with the frontend toolchain. Workflows that install it (tests.yml, the V9 foundation workflow) set
# REQUIRE_WEB_BUILD=1 so a missing toolchain fails there; elsewhere (for example the production data refresh, which
# validates data before committing it) they are skipped rather than blocking publication.
requires_web_build = pytest.mark.skipif(not Path('web/node_modules/.bin/esbuild').exists() and not os.environ.get('REQUIRE_WEB_BUILD'),
                                        reason='needs npm install --prefix web (run by tests.yml and the V9 foundation workflow)')
pytestmark = requires_web_build



def test_real_publication_preserves_models_and_retains_snapshot(tmp_path):
    protected = [Path('data/season-2026-report.json'), Path('web/public/dual-projections.json')]
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in protected]
    subprocess.run(['node', 'scripts/v9_intelligence.mjs', str(tmp_path)], check=True)
    payload = json.loads((tmp_path / 'team-intelligence.json').read_text())
    report = json.loads(protected[0].read_text())
    assert len(payload['teams']) == len(report['rankings']) == 138
    for team, row in zip(payload['teams'], report['rankings']):
        assert team['strength']['value'] == row['rating']
        assert team['accomplishment']['national_metric'] is None
        assert team['current_level']['window'] == 3
        for trend in team['trends'].values():
            assert trend['requested_window'] == 4
            assert trend['actual_window'] in (None, 3, 4)
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in protected] == before
    snapshots = list((tmp_path / 'strength-history').glob('*.json'))
    retained_hashes = {p.name for p in Path('docs/evidence/v9/strength-history').glob('*.json')}
    assert {p.name for p in snapshots} == retained_hashes | {hashlib.sha256(protected[0].read_bytes()).hexdigest() + '.json'}
    first = snapshots[0].read_bytes()
    subprocess.run(['node', 'scripts/v9_intelligence.mjs', str(tmp_path)], check=True)
    assert snapshots[0].read_bytes() == first
