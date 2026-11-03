import pytest
from cfb_analytics.talent import features_as_of, validate_talent_observation

CUTOFF = "2026-09-01T12:00:00Z"


def row(**overrides):
    value = {"team": "Georgia", "feature": "high_school_recruiting",
             "value": 91.2, "source": "dated recruiting release",
             "observed_at": "2026-07-01T00:00:00Z",
             "published_at": "2026-07-02T00:00:00Z"}
    return {**value, **overrides}


def test_latest_known_feature_and_no_future_leakage():
    early = row()
    later = row(value=93, published_at="2026-08-01T00:00:00Z")
    future = row(value=99, published_at="2026-09-02T00:00:00Z")
    result = features_as_of([early, later, future], CUTOFF)
    assert result[("Georgia", "high_school_recruiting")]["value"] == 93
    assert len(result) == 1


def test_reject_missing_provenance_bad_dates_and_nonfinite():
    for invalid in (row(source=""), row(observed_at="2026-07-01"),
                    row(published_at="2026-06-01T00:00:00Z"),
                    row(value=float("nan")), row(value=True),
                    row(feature="unobserved_scheme")):
        with pytest.raises(ValueError):
            validate_talent_observation(invalid, CUTOFF)


def test_cutoff_strict_and_fraction_validation():
    with pytest.raises(ValueError):
        validate_talent_observation(row(published_at=CUTOFF), CUTOFF)
    with pytest.raises(ValueError):
        validate_talent_observation(row(feature="returning_production", value=1.2), CUTOFF)
    assert validate_talent_observation(row(feature="transfer_departures", value=3), CUTOFF)["value"] == 3


def test_conflicting_same_time_values_rejected():
    with pytest.raises(ValueError):
        features_as_of([row(), row(value=95)], CUTOFF)
