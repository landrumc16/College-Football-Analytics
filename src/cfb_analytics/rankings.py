from math import sqrt


def rank_scores(rows, weight=0.5):
    if not 0 <= weight <= 1:
        raise ValueError('weight must be between 0 and 1')
    if not rows:
        return []
    def zscores(values):
        mean = sum(values) / len(values)
        std = sqrt(sum((x - mean) ** 2 for x in values) / len(values))
        return [(x - mean) / std if std else 0 for x in values]
    wins = zscores([x[1] for x in rows])
    ratings = zscores([x[2] for x in rows])
    scores = [(x[0], weight * wins[i] + (1 - weight) * ratings[i] - x[3] * 1e-7) for i, x in enumerate(rows)]
    return sorted(scores, key=lambda x: -x[1])


def explain_rank_scores(rows, weight=0.5):
    """Expose exact model contributions, not inferred schedule or causal effects.

    The row-order tie-break is retained so the explanation reconciles to
    rank_scores exactly. The rating input is not a separate SOS measure.
    """
    if not 0 <= weight <= 1:
        raise ValueError("weight must be between 0 and 1")
    if not rows:
        return []
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("Duplicate team in ranking explanation")

    def normalized(values):
        mean = sum(values) / len(values)
        deviation = sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        return [(v - mean) / deviation if deviation else 0.0 for v in values]

    win_z = normalized([row[1] for row in rows])
    rating_z = normalized([row[2] for row in rows])
    explained = []
    for i, (team, projected_wins, rating, sheet_row) in enumerate(rows):
        wins_contribution = weight * win_z[i]
        rating_contribution = (1 - weight) * rating_z[i]
        tie_break = -sheet_row * 1e-7
        explained.append({
            "team": team,
            "projected_wins": projected_wins,
            "rating": rating,
            "wins_contribution": wins_contribution,
            "rating_contribution": rating_contribution,
            "tie_break_contribution": tie_break,
            "score": wins_contribution + rating_contribution + tie_break,
            "scope": "standardized projected wins and rating; no separate SOS attribution",
        })
    return sorted(explained, key=lambda item: -item["score"])
