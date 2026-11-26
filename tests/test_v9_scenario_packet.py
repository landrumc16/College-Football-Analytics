"""Review packaging pairs exact reports/scenarios without relaxing client integrity checks."""
import hashlib
import json
import subprocess
from pathlib import Path
import pytest
from scripts.v9_scenario_packet import build_packet
from cfb_analytics.v6_scenarios import scenario_input
import os
import pytest

# These tests build with the frontend toolchain. Workflows that install it (tests.yml, the V9 foundation workflow) set
# REQUIRE_WEB_BUILD=1 so a missing toolchain fails there; elsewhere (for example the production data refresh, which
# validates data before committing it) they are skipped rather than blocking publication.
requires_web_build = pytest.mark.skipif(not Path('web/node_modules/.bin/esbuild').exists() and not os.environ.get('REQUIRE_WEB_BUILD'),
                                        reason='needs npm install --prefix web (run by tests.yml and the V9 foundation workflow)')


REPORT = Path('data/season-2026-report.json')
GAMES = Path('data/cfbd-2026-games.json')


def test_packet_is_exact_existing_adapter_plus_report_digest():
    raw = REPORT.read_bytes()
    packet = build_packet(raw, GAMES.read_bytes())
    digest = packet.pop('report_sha256')
    assert digest == hashlib.sha256(raw).hexdigest()
    assert packet == scenario_input(json.loads(raw), json.loads(GAMES.read_bytes()))
    assert packet['retrieved_at'] == json.loads(raw)['retrieved_at']
    assert packet['draws'] == 2000


def test_report_byte_corrections_change_digest_not_model_inputs():
    raw = REPORT.read_bytes()
    a = build_packet(raw, GAMES.read_bytes())
    b = build_packet(raw + b'\n', GAMES.read_bytes())
    assert a.pop('report_sha256') != b.pop('report_sha256')
    assert a == b


def test_source_identity_mismatch_is_rejected():
    games = json.loads(GAMES.read_bytes())
    report = json.loads(REPORT.read_bytes())
    upcoming = next(g for g in report['schedule'] if not g['completed'])
    original = next(g for g in games['games'] if g['game_id'] == upcoming['game_id'])
    original['home'] = 'Not the scheduled team'
    with pytest.raises(ValueError, match='Schedule identity differs'):
        build_packet(REPORT.read_bytes(), json.dumps(games).encode())


@requires_web_build
def test_complete_review_build_has_matching_report_and_scenario():
    protected = [REPORT, Path('web/public/v6-scenario-input.json'), Path('web/public/dual-projections.json')]
    before = [p.read_bytes() for p in protected]
    subprocess.run(['node', 'scripts/v9_preview.mjs'], check=True, capture_output=True)
    report_bytes = Path('web/dist/season-report.json').read_bytes()
    packet = json.loads(Path('web/dist/v6-scenario-input.json').read_bytes())
    assert report_bytes == REPORT.read_bytes()
    assert packet['report_sha256'] == hashlib.sha256(report_bytes).hexdigest()
    assert packet['retrieved_at'] == json.loads(report_bytes)['retrieved_at']
    assert [p.read_bytes() for p in protected] == before
