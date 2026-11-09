"""Historical identity integrity: duplicate source rows must not inflate coverage."""
import pytest

from cfb_analytics.v4_program_provenance import validate_program_sources


def strength(season):
    return {"team": "Example", "season": season, "strength": 1.0,
            "source": "https://example.org/strength"}


def poll(season, name="AP"):
    return {"team": "Example", "season": season, "poll": name,
            "preseason_rank": 12, "final_rank": 10,
            "source": "https://example.org/poll"}


def test_full_window_with_both_polls_is_counted():
    coverage = validate_program_sources(
        [strength(y) for y in range(2016, 2026)],
        [poll(y, name) for y in range(2016, 2026) for name in ("AP", "Coaches")],
        2025,
    )
    assert coverage["strength_programs_full_window"] == 1
    assert coverage["poll_programs_full_window"] == 2


@pytest.mark.parametrize("duplicate_kind", ["strength", "poll"])
def test_duplicate_team_season_rejected(duplicate_kind):
    strengths = [strength(2025)]
    polls = [poll(2025)]
    if duplicate_kind == "strength":
        strengths.append(strength(2025))
    else:
        polls.append(poll(2025))
    with pytest.raises(ValueError, match="duplicate team-season"):
        validate_program_sources(strengths, polls, 2025)


def test_separate_poll_sources_are_not_duplicates():
    coverage = validate_program_sources([strength(2025)], [poll(2025, "AP"), poll(2025, "Coaches")], 2025)
    assert coverage["poll_programs_full_window"] == 0


def test_future_season_rejected():
    with pytest.raises(ValueError, match="outside completed window"):
        validate_program_sources([strength(2026)], [], 2025)
