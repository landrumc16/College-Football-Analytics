"""Historical preseason poll expectation diagnostics, not a predictive model.

Each record represents one program in one completed season for one poll,
with a preseason and final rank (1..25 or None for unranked). The caller
must supply dated, verified AP/Coaches snapshots and team normalization.
"""
from __future__ import annotations

from collections import defaultdict


def historical_hype(rows: list[dict], latest_season: int, window: int = 10,
                    recent_weight: float = 2.0) -> dict:
    """Compute separately sourced poll retention, entry and within-poll drift.

    A rank change is measured only when ranked at both endpoints; treating
    unranked as rank 26 would fabricate rank precision. Weighted mean drift
    is positive when a ranked program falls and negative when it rises.
    """
    if not isinstance(latest_season, int) or isinstance(latest_season, bool):
        raise ValueError("Invalid latest completed season")
    if not isinstance(window, int) or isinstance(window, bool) or window < 2:
        raise ValueError("Invalid window")
    if not isinstance(recent_weight, (int, float)) or not 1 <= recent_weight <= 10:
        raise ValueError("Invalid recent weighting")
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        required = ("team", "season", "poll", "preseason_rank", "final_rank", "source")
        if any(k not in row for k in required):
            raise ValueError("Missing required poll-history fields")
        team, season, poll = row["team"], row["season"], row["poll"]
        if not isinstance(team, str) or not team.strip() or not isinstance(row["source"], str) or not row["source"].strip():
            raise ValueError("Missing team or source")
        if poll not in ("AP", "Coaches"):
            raise ValueError("Poll must be AP or Coaches")
        if not isinstance(season, int) or isinstance(season, bool) or season > latest_season:
            raise ValueError("Season must be completed")
        for key in ("preseason_rank", "final_rank"):
            rank = row[key]
            if rank is not None and (not isinstance(rank, int) or isinstance(rank, bool) or not 1 <= rank <= 25):
                raise ValueError("Rank must be 1..25 or None for unranked")
        key = (team, season, poll)
        if key in seen:
            raise ValueError("Duplicate team-season-poll")
        seen.add(key)
        if season >= latest_season - window + 1:
            groups[(team, poll)].append(row)

    results = []
    for (team, poll), records in sorted(groups.items()):
        preseason = [r for r in records if r["preseason_rank"] is not None]
        final = [r for r in records if r["final_rank"] is not None]
        retained = [r for r in preseason if r["final_rank"] is not None]
        entered = [r for r in records if r["preseason_rank"] is None and r["final_rank"] is not None]
        eligible_entries = [r for r in records if r["preseason_rank"] is None]
        drift = [(r, r["final_rank"] - r["preseason_rank"]) for r in retained]
        weighted = [(recent_weight if r["season"] > latest_season - window / 2 else 1.0, change)
                    for r, change in drift]
        mean_drift = (sum(w * d for w, d in weighted) / sum(w for w, _ in weighted)) if weighted else None
        classification = "insufficient_data"
        # Never label a ten-season tendency from a partial set of seasons.
        if len(records) == window and len(drift) >= 3:
            if mean_drift > 2:
                classification = "historically_overhyped"
            elif mean_drift < -2:
                classification = "historically_underhyped"
            else:
                classification = "broadly_justified"
        results.append({
            "team": team, "poll": poll, "seasons_observed": len(records),
            "seasons_required": window, "full_window_coverage": len(records) == window,
            "preseason_top25": len(preseason), "retained_top25": len(retained),
            "dropped_out": len(preseason) - len(retained),
            "unranked_preseason": len(eligible_entries), "entered_top25": len(entered),
            "final_top25": len(final),
            "retention_rate": len(retained) / len(preseason) if preseason else None,
            "entry_rate": len(entered) / len(eligible_entries) if eligible_entries else None,
            "within_poll_mean_rank_drop": mean_drift,
            "within_poll_comparisons": len(drift),
            "historical_tendency": classification,
        })
    return {
        "status": "descriptive_only", "latest_completed_season": latest_season,
        "window": window, "recent_weight": recent_weight,
        "predictive_validation": False, "program_polls": results,
    }
