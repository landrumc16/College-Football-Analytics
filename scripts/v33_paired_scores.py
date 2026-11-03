"""Paired retrospective forecast scoring with strict game alignment.

Research-only: the observations must come from predictions reconstructed before
each game's result; these utilities do not create prospective forecast evidence.
"""
from math import isfinite, log, sqrt


def _index(rows):
    indexed = {}
    for row in rows:
        key = (row["season"], str(row["game_id"]))
        if key in indexed:
            raise ValueError(f"Duplicate prediction game: {key}")
        p = row["home_probability"]
        y = row["home_won"]
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not isfinite(p) or not 0 <= p <= 1:
            raise ValueError(f"Invalid home probability: {key}")
        if y not in (0, 1):
            raise ValueError(f"Invalid outcome: {key}")
        indexed[key] = (p, y)
    return indexed


def paired_score(incumbent_rows, candidate_rows):
    """Return mean candidate-minus-incumbent losses on identical games."""
    base = _index(incumbent_rows)
    trial = _index(candidate_rows)
    if base.keys() != trial.keys():
        raise ValueError("Incumbent and candidate must score identical games")
    if not base:
        return {"games": 0, "brier_delta": None, "logloss_delta": None,
                "brier_delta_standard_error": None}
    brier_deltas, log_deltas = [], []
    for key, (p, y) in base.items():
        q, candidate_y = trial[key]
        if y != candidate_y:
            raise ValueError(f"Conflicting outcomes for game: {key}")
        brier_deltas.append((q - y) ** 2 - (p - y) ** 2)
        def loss(prob):
            clipped = min(1 - 1e-12, max(1e-12, prob))
            return -(y * log(clipped) + (1 - y) * log(1 - clipped))
        log_deltas.append(loss(q) - loss(p))
    n = len(brier_deltas)
    mean = sum(brier_deltas) / n
    se = sqrt(sum((x - mean) ** 2 for x in brier_deltas) / (n * (n - 1))) if n > 1 else None
    return {"games": n, "brier_delta": mean,
            "logloss_delta": sum(log_deltas) / n,
            "brier_delta_standard_error": se}


def calibration_bins(rows, *, bins=10):
    """Equal-width reliability bins; observed rates are descriptive, not calibrated forecasts."""
    if not isinstance(bins, int) or not 2 <= bins <= 100:
        raise ValueError("bins must be an integer from 2 to 100")
    observations = _index(rows)
    groups = [[] for _ in range(bins)]
    for probability, outcome in observations.values():
        index = min(bins - 1, int(probability * bins))
        groups[index].append((probability, outcome))
    return [
        {"lower": i / bins, "upper": (i + 1) / bins,
         "games": len(group),
         "mean_probability": sum(p for p, _ in group) / len(group) if group else None,
         "observed_rate": sum(y for _, y in group) / len(group) if group else None}
        for i, group in enumerate(groups)
    ]
