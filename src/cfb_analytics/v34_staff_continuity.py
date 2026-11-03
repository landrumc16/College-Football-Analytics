"""Compute documented coaching-staff continuity at a pregame cutoff.

Continuity is descriptive and is not itself a causal coaching grade.
"""
from .coaching import coaching_as_of, ROLES
from .talent import _timestamp


def staff_continuity(records, *, current_cutoff, prior_cutoff):
    current = _timestamp(current_cutoff)
    prior = _timestamp(prior_cutoff)
    if current is None or prior is None or prior >= current:
        raise ValueError("Ordered timezone-aware cutoffs required")
    before = coaching_as_of(records, prior_cutoff)
    after = coaching_as_of(records, current_cutoff)
    teams = sorted({team for team, _ in before} | {team for team, _ in after})
    result = []
    for team in teams:
        known = []
        changed = []
        for role in sorted(ROLES):
            previous, now = before.get((team, role)), after.get((team, role))
            if previous is None or now is None:
                continue
            known.append(role)
            if previous["coach"] != now["coach"]:
                changed.append(role)
        result.append({"team": team, "comparable_roles": len(known),
                       "unchanged_roles": len(known)-len(changed),
                       "changed_roles": changed,
                       "continuity_fraction": (len(known)-len(changed))/len(known) if known else None})
    return {"teams": result, "scope": "dated staff continuity; missing roles not assumed unchanged"}
