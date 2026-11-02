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
    exclusions = {"ineligible_game": 0, "missing_workbook": 0,
                  "missing_candidate": 0, "not_verified_pregame": 0}
    for game in sorted(games, key=lambda g: (g.season, g.game_id)):
        key = (game.season, game.game_id)
        if not game.eligible_fbs_accuracy:
            exclusions["ineligible_game"] += 1
            continue
        if key not in left:
            exclusions["missing_workbook"] += 1
        if key not in right:
            exclusions["missing_candidate"] += 1
        if key not in left or key not in right:
            continue
        a, b = left[key], right[key]
        if not all(game.verified_pregame(f.generated_at, f.input_retrieved_at)
                   for f in (a, b)):
            exclusions["not_verified_pregame"] += 1
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
    seasons = sorted({row[0] for row in scored})
    by_season = {}
    for season in seasons:
        rows = [row for row in scored if row[0] == season]
        def season_metrics(column):
            n = len(rows)
            values = [(row[column], row[1]) for row in rows]
            return {
                "games": n,
                "winner_accuracy": sum((p >= 0.5) == bool(y) for p, y in values) / n,
                "brier_score": sum((p - y) ** 2 for p, y in values) / n,
                "log_loss": -sum(y * log(max(1e-15, p)) +
                                 (1-y) * log(max(1e-15, 1-p)) for p, y in values) / n,
            }
        by_season[str(season)] = {"workbook": season_metrics(2),
                                  "candidate": season_metrics(3)}
    return {
        "paired_games": len(scored),
        "eligible_completed_games": sum(g.eligible_fbs_accuracy for g in games),
        "excluded": exclusions,
        "workbook": baseline,
        "candidate": challenger,
        "candidate_minus_workbook": None if not scored else {
            metric: challenger[metric] - baseline[metric]
            for metric in ("winner_accuracy", "brier_score", "log_loss")},
        "by_season": by_season,
        "by_season_counts": {
            str(season): sum(row[0] == season for row in scored)
            for season in sorted({row[0] for row in scored})},
        "scope": "matched verified pregame FBS-vs-FBS probability forecasts",
    }
