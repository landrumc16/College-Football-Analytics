from datetime import datetime, timezone
from scripts.optional_source_budget import allowed

NOW = datetime(2026, 11, 27, 14, tzinfo=timezone.utc)


def test_optional_calls_cannot_consume_essential_reserve():
    info = {'resetAt': '2026-12-01T00:00:00Z', 'remainingCalls': 14}
    assert not allowed(info, NOW)
    info['remainingCalls'] = 33
    assert not allowed(info, NOW)
    info['remainingCalls'] = 41
    assert allowed(info, NOW)


def test_unknown_or_invalid_quota_never_funds_optional_calls():
    for value in [None, -1, '1000', True]:
        assert not allowed({'remainingCalls': value}, NOW)


def test_core_analytics_precedes_supplemental_acquisition():
    info = {'resetAt': '2026-12-01T00:00:00Z', 'remainingCalls': 39}
    assert allowed(info, NOW, 'core', 7)
    assert not allowed(info, NOW, 'supplemental', 2)
    info['remainingCalls'] = 38
    assert not allowed(info, NOW, 'core', 7)


def test_invalid_priority_or_cost_is_never_spent():
    info = {'resetAt': '2026-12-01T00:00:00Z', 'remainingCalls': 1000}
    assert not allowed(info, NOW, 'essential', 2)
    assert not allowed(info, NOW, 'core', -1)
