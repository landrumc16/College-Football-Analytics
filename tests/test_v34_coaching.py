import pytest
from cfb_analytics.coaching import coaching_as_of, scheme_as_of

CUTOFF = "2026-09-01T12:00:00Z"


def test_coaching_assignments_use_published_as_of():
    base = {"team": "Georgia", "role": "head_coach", "coach": "Coach A",
            "source": "school announcement", "effective_at": "2026-01-01T00:00:00Z",
            "published_at": "2026-01-01T00:00:00Z"}
    future = {**base, "coach": "Coach B", "published_at": "2026-09-02T00:00:00Z"}
    result = coaching_as_of([base, future], CUTOFF)
    assert result[("Georgia", "head_coach")]["coach"] == "Coach A"


def test_coaching_conflicts_are_rejected():
    base = {"team": "Georgia", "role": "offensive_coordinator", "coach": "A",
            "source": "school", "effective_at": "2026-01-01T00:00:00Z",
            "published_at": "2026-01-01T00:00:00Z"}
    with pytest.raises(ValueError):
        coaching_as_of([base, {**base, "coach": "B"}], CUTOFF)


def test_scheme_metrics_are_distinct_and_cutoff_safe():
    base = {"team": "Georgia", "feature": "pace", "value": 70,
            "source": "dated play-by-play summary",
            "observed_at": "2026-08-01T00:00:00Z",
            "published_at": "2026-08-02T00:00:00Z"}
    passing = {**base, "feature": "pass_rate", "value": 0.55}
    future = {**base, "value": 90, "published_at": "2026-09-02T00:00:00Z"}
    selected = scheme_as_of([base, passing, future], CUTOFF)
    assert selected[("Georgia", "pace")]["value"] == 70
    assert selected[("Georgia", "pass_rate")]["value"] == 0.55
    assert len(selected) == 2
