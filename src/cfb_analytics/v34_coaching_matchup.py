"""Time-bounded coaching continuity and scheme diagnostics for a matchup.

Features are descriptive; they do not alter production forecasts.
"""
from .v34_staff_continuity import staff_continuity
from .v34_matchups import matchup_scheme_diagnostics
from .talent import _timestamp


def coaching_matchup_report(games, staff, schemes, *, cutoff_by_game, prior_cutoff_by_game):
    matchups = matchup_scheme_diagnostics(games, schemes, cutoff_by_game=cutoff_by_game)["matchups"]
    output = []
    for match in matchups:
        game_id = match["game_id"]
        prior = prior_cutoff_by_game.get(game_id)
        if _timestamp(prior) is None or _timestamp(prior) >= _timestamp(match["cutoff"]):
            raise ValueError("Earlier coaching comparison cutoff required")
        continuity = staff_continuity(staff, current_cutoff=match["cutoff"], prior_cutoff=prior)
        teams = {row["team"]: row for row in continuity["teams"]}
        output.append({**match, "home_staff": teams.get(match["home"]),
                       "away_staff": teams.get(match["away"])})
    return {"matchups": output,
            "scope": "research-only pregame scheme and staff continuity; no validated win-probability adjustment"}
