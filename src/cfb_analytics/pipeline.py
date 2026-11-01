"""End-to-end season model from a validated CFBD snapshot.

The frozen 2026 workbook roster supplies priors and conferences until a
season-specific preseason-prior feed is implemented. Unknown teams are treated
as FCS opponents, not silently added to the ranked FBS universe.
"""
import json
from pathlib import Path

from .ingestion import IngestedGame
from .model import ModelSettings
from .predictions import predict
from .projections import ScheduledGame, project_season
from .rankings import rank_scores
from .ratings import Game, Team, calculate_ratings


def build_season_report(snapshot: dict, roster: list[dict], settings=ModelSettings()) -> dict:
    season = snapshot["season"]
    games = [IngestedGame(**g) for g in snapshot["games"]]
    if any(g.season != season for g in games):
        raise ValueError("Snapshot contains games from a different season")
    if len({g.game_id for g in games}) != len(games):
        raise ValueError("Snapshot contains duplicate game ids")
    if any(g.completed and (g.home_score is None or g.away_score is None) for g in games):
        raise ValueError("Completed game missing score")
    teams = [Team(t["name"], t["conference"], t["prior"]) for t in roster]
    known = {t.name for t in teams}
    conferences = {t.name: t.conference for t in teams}
    completed = [
        Game(g.home, g.away, g.home_score, g.away_score, g.week)
        for g in games if g.completed
    ]
    ratings = calculate_ratings(teams, completed, settings)
    conference_wins = {name: 0 for name in known}
    for g in games:
        if not g.completed or g.home not in known or g.away not in known:
            continue
        if (conferences[g.home] == conferences[g.away] and
                conferences[g.home] != "Independent"):
            winner = g.home if g.home_score > g.away_score else g.away
            conference_wins[winner] += 1
    projections = project_season(
        {t.name: (t.conference, ratings[t.name].adaptive_rating,
                  ratings[t.name].wins, conference_wins[t.name]) for t in teams},
        [ScheduledGame(g.home, g.away, g.completed) for g in games],
        home_field_advantage=settings.home_field_advantage,
        win_probability_scale=settings.win_probability_scale,
        fcs_rating=settings.fcs_opponent_rating,
    )
    order = rank_scores([
        (t.name, projections[t.name].projected_wins,
         ratings[t.name].adaptive_rating, index + 4)
        for index, t in enumerate(teams)
    ])
    ranking = [
        {"rank": index + 1, "team": name, "rank_score": score,
         "rating": ratings[name].adaptive_rating,
         "wins": ratings[name].wins,
         "losses": ratings[name].losses,
         "projected_wins": projections[name].projected_wins,
         "projected_conference_wins": projections[name].projected_conference_wins}
        for index, (name, score) in enumerate(order)
    ]
    predictions = []
    for g in games:
        if g.completed:
            continue
        home_rating = ratings[g.home].adaptive_rating if g.home in known else settings.fcs_opponent_rating
        away_rating = ratings[g.away].adaptive_rating if g.away in known else settings.fcs_opponent_rating
        result = predict(g.home, g.away, home_rating, away_rating,
                         neutral=g.neutral_site,
                         home_field_advantage=settings.home_field_advantage,
                         model_scale=settings.win_probability_scale)
        predictions.append({
            "game_id": g.game_id, "week": g.week, "home": g.home, "away": g.away,
            "neutral_site": g.neutral_site, "predicted_winner": result.winner,
            "home_margin": result.home_margin,
            "home_win_probability": result.model_home_probability,
            "confidence": result.confidence,
        })
    return {
        "season": season, "source": snapshot.get("source"),
        "summary": {"teams": len(teams), "completed_games": len(completed),
                    "upcoming_games": len(predictions)},
        "rankings": ranking, "predictions": predictions,
    }


def run_snapshot(snapshot_path: Path, roster_path: Path, output_path: Path):
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    report = build_season_report(snapshot, roster)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temp.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        temp.replace(output_path)
    finally:
        temp.unlink(missing_ok=True)
    return report
