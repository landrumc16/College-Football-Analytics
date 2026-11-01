"""Paired prediction comparison on the *same* verified historical games.

Input values are pregame probabilities, never reconstructed from final scores.
"""
from math import log
from .historical import HistoricalGame
from .historical_evaluation import ArchivedForecast


def paired_scorecard(games: list[HistoricalGame],
                     workbook: list[ArchivedForecast],
                     candidate: list[ArchivedForecast]) -> dict:
    def index(rows):
        result = {}
        for row in rows:
            key = (row.season, row.game_id)
            if key in result:
                raise ValueError(f"Duplicate forecast {key}")
            result[key] = row
        return result

    left, right = index(workbook), index(candidate)
    if len({(g.season, g.game_id) for g in games}) != len(games):
        raise ValueError("Duplicate historical games")
    scored = []
    for game in sorted(games, key=lambda g: (g.season, g.game_id)):
        key = (game.season, game.game_id)
        if not game.eligible_fbs_accuracy or key not in left or key not in right:
            continue
        a, b = left[key], right[key]
        if not game.verified_pregame(a.generated_at) or not game.verified_pregame(b.generated_at):
            continue
        scored.append((game.season, int(game.home_score > game.away_score),
                       a.home_win_probability, b.home_win_probability))

    def metrics(index):
        n = len(scored)
        if not n:
            return None
        values = [(row[index], row[1]) for row in scored]
        return {
            "winner_accuracy": sum((p >= 0.5) == bool(y) for p, y in values) / n,
            "brier_score": sum((p-y)**2 for p, y in values) / n,
            "log_loss": -sum(y*log(max(1e-15, p)) +
                             (1-y)*log(max(1e-15, 1-p)) for p, y in values) / n,
        }

    baseline, challenger = metrics(2), metrics(3)
    return {
        "paired_games": len(scored),
        "workbook": baseline,
        "candidate": challenger,
        "candidate_minus_workbook": None if not scored else {
            metric: challenger[metric] - baseline[metric]
            for metric in ("winner_accuracy", "brier_score", "log_loss")},
        "by_season_counts": {
            str(season): sum(row[0] == season for row in scored)
            for season in sorted({row[0] for row in scored})},
        "scope": "matched verified pregame FBS-vs-FBS probability forecasts",
    }
