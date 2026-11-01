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
