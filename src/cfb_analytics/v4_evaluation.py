"""Paired, provenance-aware V4 evaluation. No model promotion or synthetic archives."""
from __future__ import annotations

from collections import defaultdict
from math import isfinite, log
from statistics import mean


def evaluate_pairs(rows: list[dict]) -> dict:
    """Compare predictions on identical games, rejecting duplicates and missing provenance.

    Required: game_id, season, week, outcome, incumbent_probability,
    challenger_probability, prediction_kind ('retrospective' or 'prospective').
    Prospective rows additionally require a pregame timestamp and data-as-of ID.
    """
    if not rows:
        return {"status": "insufficient_data", "games": 0, "promotion_eligible": False}
    seen = set()
    buckets = defaultdict(list)
    for row in rows:
        key = (row["season"], row["game_id"])
        if key in seen:
            raise ValueError("Duplicate season/game_id")
        seen.add(key)
        if not isinstance(row["week"], int) or row["week"] < 1:
            raise ValueError("Week must be positive integer")
        if row["outcome"] not in (0, 1):
            raise ValueError("Outcome must be binary")
        for name in ("incumbent_probability", "challenger_probability"):
            p = row[name]
            if not isinstance(p, (float, int)) or not isfinite(p) or not 0 <= p <= 1:
                raise ValueError("Invalid probability: " + name)
        kind = row["prediction_kind"]
        if kind not in ("prospective", "retrospective"):
            raise ValueError("Prediction kind must be explicit")
        if kind == "prospective" and not (row.get("predicted_at") and row.get("data_as_of")):
            raise ValueError("Prospective predictions require archive provenance")
        buckets[kind].append(row)

    def summarize(items):
        def metrics(field):
            ps = [r[field] for r in items]
            ys = [r["outcome"] for r in items]
            eps = 1e-15
            return {
                "brier_score": mean((p-y)**2 for p, y in zip(ps, ys)),
                "log_loss": mean(-(y*log(max(eps, p))+(1-y)*log(max(eps, 1-p))) for p, y in zip(ps, ys)),
                "winner_accuracy": mean((p >= .5) == bool(y) for p, y in zip(ps, ys)),
            }
        incumbent = metrics("incumbent_probability")
        challenger = metrics("challenger_probability")
        before = incumbent["brier_score"]
        return {
            "games": len(items),
            "incumbent": incumbent,
            "challenger": challenger,
            "relative_brier_reduction": (before-challenger["brier_score"])/before if before > 0 else None,
        }

    return {
        "status": "evaluation_only",
        "games": len(rows),
        "promotion_eligible": False,
        "reason": "Requires four independent held-out seasons, clustered uncertainty, and all V4 release gates",
        "retrospective": summarize(buckets["retrospective"]) if buckets["retrospective"] else None,
        "prospective": summarize(buckets["prospective"]) if buckets["prospective"] else None,
        "retrospective_by_season": {str(season): summarize([r for r in buckets["retrospective"] if r["season"] == season])
                                   for season in sorted({r["season"] for r in buckets["retrospective"]})},
    }


def clustered_brier_interval(rows: list[dict], *, draws: int = 2000,
                             seed: int = 2026) -> dict:
    """Paired game-week cluster bootstrap of challenger-minus-incumbent Brier.

    Use only held-out retrospective rows from a single predeclared evaluation
    cohort. Resample entire (season, week) clusters, not individual games.
    The returned interval is descriptive until fold independence and cutoff
    provenance are established elsewhere.
    """
    import random
    if not rows:
        raise ValueError("At least one paired game is required")
    if draws < 100:
        raise ValueError("At least 100 bootstrap draws required")
    clusters = defaultdict(list)
    for row in rows:
        if row["prediction_kind"] != "retrospective":
            raise ValueError("Bootstrap requires retrospective rows only")
        if not isinstance(row["week"], int) or row["week"] < 1:
            raise ValueError("Invalid week")
        for key in ("incumbent_probability", "challenger_probability"):
            p = row[key]
            if not isinstance(p, (int, float)) or not isfinite(p) or not 0 <= p <= 1:
                raise ValueError("Invalid probability")
        if row["outcome"] not in (0, 1):
            raise ValueError("Invalid outcome")
        y = row["outcome"]
        clusters[(row["season"], row["week"])].append(
            (row["challenger_probability"] - y) ** 2
            - (row["incumbent_probability"] - y) ** 2)
    if len(clusters) < 2:
        raise ValueError("At least two independent game-week clusters required")
    blocks = list(clusters.values())
    point = mean(d for block in blocks for d in block)
    rng = random.Random(seed)
    sampled = []
    for _ in range(draws):
        selected = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        sampled.append(mean(d for block in selected for d in block))
    sampled.sort()
    return {
        "paired_brier_difference": point,
        "ci95_lower": sampled[int(draws * .025)],
        "ci95_upper": sampled[min(draws - 1, int(draws * .975))],
        "clusters": len(blocks),
        "games": len(rows),
        "draws": draws,
        "seed": seed,
        "ci_method": "paired game-week cluster bootstrap percentile",
        "supports_improvement": sampled[min(draws - 1, int(draws * .975))] < 0,
    }
