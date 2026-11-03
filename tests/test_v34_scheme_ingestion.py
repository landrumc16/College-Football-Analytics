import pytest
from cfb_analytics.v34_scheme_ingestion import normalize_scheme_statistics


def row(value=.6, published="2025-09-01T00:00:00Z"):
    return {"team": "Georgia", "feature": "pass_rate", "value": value,
            "source": "official team stats", "observed_at": published,
            "published_at": published}


def test_valid_rate_and_provenance():
    result = normalize_scheme_statistics([row()], cutoff="2025-09-02T00:00:00Z")
    assert result[0]["value"] == .6
    assert result[0]["source"] == "official team stats"


def test_future_data_and_out_of_range_rate_rejected():
    with pytest.raises(ValueError):
        normalize_scheme_statistics([row(published="2025-09-03T00:00:00Z")],
                                    cutoff="2025-09-02T00:00:00Z")
    with pytest.raises(ValueError, match="fraction"):
        normalize_scheme_statistics([row(value=62)], cutoff="2025-09-02T00:00:00Z")
