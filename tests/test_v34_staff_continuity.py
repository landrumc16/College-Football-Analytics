from cfb_analytics.v34_staff_continuity import staff_continuity


def staff(coach, role, date):
    return {"team": "Georgia", "role": role, "coach": coach,
            "source": "official staff directory", "published_at": date,
            "effective_at": date}


def test_staff_continuity_counts_only_comparable_roles():
    rows = [staff("Coach A", "head_coach", "2024-08-01T00:00:00Z"),
            staff("Coach B", "offensive_coordinator", "2024-08-01T00:00:00Z"),
            staff("Coach C", "offensive_coordinator", "2025-08-01T00:00:00Z"),
            staff("Coach D", "defensive_coordinator", "2025-08-01T00:00:00Z")]
    result = staff_continuity(rows, prior_cutoff="2024-09-01T00:00:00Z",
                             current_cutoff="2025-09-01T00:00:00Z")
    ga = result["teams"][0]
    assert ga["comparable_roles"] == 2
    assert ga["unchanged_roles"] == 1
    assert ga["changed_roles"] == ["offensive_coordinator"]
    assert ga["continuity_fraction"] == .5
