"""V8 M3: publish the compact Offense & Defense data file for the web app.

  python -m cfb_analytics.v8_publish --season 2026   # writes web/public/v8-team-stats.json

Per metric and side the row is [raw, raw_rank, power, power_rank, power_games, adjusted, se, adjusted_rank, n]
(n = denominator: plays, drives, attempts or trips). Every value comes from v8_stats; nothing is estimated here.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import v8_stats as st

OUT = Path("web/public/v8-team-stats.json")
FIELDS = ["raw", "raw_rank", "power", "power_rank", "power_games", "adjusted", "se", "adjusted_rank", "n"]


def compact(stats, receipt):
    teams = {}
    for name, t in sorted(stats["teams"].items()):
        side = lambda s: {m: [t[s][m].get(f) for f in FIELDS] for m in st.METRICS}
        trend = {k: (v["last4"] or v["last3"]) for k, v in t["trend"].items()}
        teams[name] = {"conference": t["conference"], "power": t["power"], "games": t["games"],
                       "fcs_games": t["fcs_games"], "power_games": t["power_games"],
                       "games_with_play_data": t["games_with_play_data"],
                       "ppg": t["points_per_game"], "papg": t["points_allowed_per_game"],
                       "offense": side("offense"), "defense": side("defense"),
                       "trend": trend, "volatility": t["volatility"]}
    season_cov = next((c for c in receipt.get("coverage", []) if c["season"] == stats["season"]), None)
    return {"schema_version": 1, "season": stats["season"], "as_of": stats["as_of"],
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "CollegeFootballData play-by-play and drives (derived counts); research/v8",
            "fields": FIELDS, "definitions": st.definitions(), "league": stats["league"],
            "power_conferences": stats["power_conferences"], "fbs_teams": stats["fbs_teams"],
            "power_teams": stats["power_teams"], "coverage": season_cov,
            "method": {"adjusted": "weighted ridge: game value = mean + offense + defense + home field; schedule counted once; shrinkage by sample size; FCS games excluded",
                       "power": "games against ACC, Big Ten, Big 12, SEC and Notre Dame (Pac-12 through 2023)",
                       "garbage_time": "efficiency excludes plays when the margin exceeds 38 (Q2), 28 (Q3) or 22 (Q4)",
                       "trend": "last 4 games versus earlier games, opponent-adjusted; labelled only beyond 1.645 standard errors",
                       "volatility": "standard deviation of opponent-adjusted game values (5+ games)"},
            "teams": teams}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    stats = st.team_stats(st.load_rows(args.season), args.season)
    receipt = json.loads((st.ROOT / "sources-receipt.json").read_text())
    payload = compact(stats, receipt)
    args.out.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"{args.out}: {len(payload['teams'])} teams, {args.out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
