"""Review builds must contain the real report and observations, with no API acquisition."""
import json
from pathlib import Path
import subprocess
import tempfile
import os
import pytest

# These tests build with the frontend toolchain. Workflows that install it (tests.yml, the V9 foundation workflow) set
# REQUIRE_WEB_BUILD=1 so a missing toolchain fails there; elsewhere (for example the production data refresh, which
# validates data before committing it) they are skipped rather than blocking publication.
requires_web_build = pytest.mark.skipif(not Path('web/node_modules/.bin/esbuild').exists() and not os.environ.get('REQUIRE_WEB_BUILD'),
                                        reason='needs npm install --prefix web (run by tests.yml and the V9 foundation workflow)')
pytestmark = requires_web_build



def test_review_observations_and_real_team_values():
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(['node', 'scripts/v9_intelligence.mjs', directory], check=True, capture_output=True)
        packet = json.loads((Path(directory) / 'team-intelligence.json').read_text())
    report = json.loads(Path('data/season-2026-report.json').read_text())
    assert len(packet['teams']) == len(report['rankings']) == 138
    for name in ['Texas Tech', 'Georgia', 'Baylor', 'Notre Dame', 'Boise State']:
        team = next(t for t in packet['teams'] if t['team'] == name)
        actual = next(t for t in report['rankings'] if t['team'] == name)
        assert team['strength']['value'] == actual['rating']
        assert team['accomplishment']['wins'] == actual['wins']
        assert team['accomplishment']['national_metric'] is None
    assert packet['observations']
    assert len({o['source_sha256'] for o in packet['observations']}) == len(packet['observations'])
    for observation in packet['observations']:
        retained = Path('docs/evidence/v9/strength-history') / (observation['source_sha256'] + '.json')
        if retained.exists():
            assert observation == json.loads(retained.read_text())
        assert observation['kind'] == 'retained_report_observation'
        assert observation['report_generated_at']
