from datetime import datetime, timezone
from scripts.optional_source_budget import allowed

NOW = datetime(2026, 11, 27, 14, tzinfo=timezone.utc)


def test_optional_calls_cannot_consume_essential_reserve():
    info = {'resetAt': '2026-12-01T00:00:00Z', 'remainingCalls': 14}
    assert not allowed(info, NOW)
    info['remainingCalls'] = 33
    assert not allowed(info, NOW)
    info['remainingCalls'] = 34
    assert allowed(info, NOW)


def test_unknown_or_invalid_quota_never_funds_optional_calls():
    for value in [None, -1, '1000', True]:
        assert not allowed({'remainingCalls': value}, NOW)
