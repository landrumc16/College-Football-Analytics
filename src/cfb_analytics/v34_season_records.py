"""Convert canonical completed games to team-season win totals.

FBS-FCS results count toward actual season records; division classification is
kept separate from FBS-vs-FBS forecast accuracy scoring.
"""
from collections import defaultdict


def season_records(games, *, eligible_teams):
    """Return team-season actual wins and completed-game counts.

    Requires complete canonical games with unique (season, game_id).
    Unplayed games and ties do not count toward a win/loss record.
    """
    eligible = set(eligible_teams)
    seen = set()
    totals = defaultdict(lambda: {"actual_wins": 0, "games_played": 0,
                                  "fcs_or_other_opponent_games": 0})
    for game in games:
        key = (game.season, game.game_id)
        if key in seen:
            raise ValueError("Duplicate game in season record")
        seen.add(key)
        if not game.completed or game.home_score is None or game.away_score is None:
            continue
        if game.home_score == game.away_score:
            raise ValueError("Unexpected tied completed football game")
        for team, opponent, won in ((game.home, game.away, game.home_score > game.away_score),
                                    (game.away, game.home, game.away_score > game.home_score)):
            if team not in eligible:
                continue
            record = totals[(game.season, team)]
            record["games_played"] += 1
            record["actual_wins"] += int(won)
            record["fcs_or_other_opponent_games"] += int(opponent not in eligible)
    return [{"season": season, "team": team, **totals[(season, team)]}
            for season, team in sorted(totals)]
