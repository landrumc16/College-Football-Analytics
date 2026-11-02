"""Decision contract: never promote retrospective Elo automatically."""
import copy

import pytest

from scripts.v3_research_decision import summarize


def fixture(dev_candidate=0.19, holdout_candidate=0.19):
    incumbent = {"k": 24, "home_advantage": 55,
                 "development": {"games": 100, "brier": 0.21},
                 "holdout": {"games": 40, "brier": 0.22}}
    candidate = {"k": 16, "home_advantage": 55,
                 "development": {"games": 100, "brier": dev_candidate},
                 "holdout": {"games": 40, "brier": holdout_candidate}}
    others = [dict(copy.deepcopy(incumbent), k=k, home_advantage=h)
              for k, h in ((32, 55), (24, 0), (24, 75))]
    return {"type": "v3_retrospective_elo_sensitivity",
            "holdout_season": 2025, "holdout_is_not_used_for_selection": True,
            "incumbent": incumbent, "selected": candidate,
            "candidates": [incumbent, candidate, *others]}


def test_meaningful_gain_requires_holdout_confirmation():
    result = summarize(fixture())
    assert result["recommendation"] == "candidate_warrants_further_validation"
    assert result["promotion_authorized"] is False
    assert result["production_model"] == "workbook_2026_baseline"


def test_holdout_regression_retains_incumbent():
    assert summarize(fixture(holdout_candidate=0.23))["recommendation"] == "retain_incumbent"


def test_tiny_gain_retains_incumbent():
    assert summarize(fixture(dev_candidate=0.2095, holdout_candidate=0.2195))["recommendation"] == "retain_incumbent"


def test_missing_holdout_is_rejected():
    study = fixture()
    study["selected"]["holdout"]["games"] = 0
    with pytest.raises(ValueError, match="Development and holdout"):
        summarize(study)


def test_invalid_selection_is_rejected():
    study = fixture()
    study["selected"] = study["incumbent"]
    with pytest.raises(ValueError, match="minimize development Brier"):
        summarize(study)
