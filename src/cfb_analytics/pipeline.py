"""End-to-end season model from a validated CFBD snapshot.

The frozen 2026 workbook roster supplies priors and conferences until a
season-specific preseason-prior feed is implemented. Unknown teams are treated
as FCS opponents, not silently added to the ranked FBS universe.
"""
import json
from pathlib import Path

from .cfp import simulate_cfp
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
    # CFBD uses "Miami" for Miami (FL), while the baseline roster uses
    # "Miami (FL)". Resolve this verified alias before model calculations.
    aliases = {"Miami": "Miami (FL)", "App State": "Appalachian State",
               "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}
    games = [IngestedGame(**{**g.__dict__,
                           "home": aliases.get(g.home, g.home),
                           "away": aliases.get(g.away, g.away)}) for g in games]
    teams = [Team(t["name"], t["conference"], t["prior"]) for t in roster]
    if not teams:
        raise ValueError("Roster must contain teams")
    if any(g.home == g.away for g in games):
        raise ValueError("Snapshot contains a self-matchup")
    known = {t.name for t in teams}
    if snapshot.get("source") == "collegefootballdata.com/games":
        observed = {name for g in games for name in (g.home, g.away)}
        missing = sorted(known - observed)
        if missing:
            raise ValueError(f"FBS roster schools absent from CFBD games: {missing}")
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
    cfp = simulate_cfp(
        {t.name: {"conference": t.conference,
                  "rating": ratings[t.name].adaptive_rating,
                  "wins": ratings[t.name].wins,
                  "conference_wins": conference_wins[t.name]} for t in teams},
        [{"home": g.home, "away": g.away, "neutral_site": g.neutral_site}
         for g in games if not g.completed],
        scale=settings.win_probability_scale,
        home_edge=settings.home_field_advantage,
        fcs_rating=settings.fcs_opponent_rating,
    )
    # Deterministic projected field, distinct from Monte Carlo field odds.
    by_conference = {}
    for t in teams:
        if t.conference == "Independent":
            continue
        by_conference.setdefault(t.conference, []).append(t.name)
    ranking_index = {name: i for i, (name, _) in enumerate(order)}
    championship_matchups = []
    projected_champions = []
    for conference, members in sorted(by_conference.items()):
        finalists = sorted(members, key=lambda name: (
            -projections[name].projected_conference_wins, ranking_index[name], name))[:2]
        if len(finalists) == 2:
            first, second = finalists
            # Most likely winner of the neutral-site title game.
            champion = min(finalists, key=lambda name: (-ratings[name].adaptive_rating, name))
            championship_matchups.append({
                "conference": conference, "first": first, "second": second,
                "projected_champion": champion,
            })
        else:
            champion = finalists[0]
        projected_champions.append(champion)
    projected_champions.sort(key=lambda name: ranking_index[name])
    if len(projected_champions) < 5:
        raise ValueError("Projected CFP field requires at least five eligible conference champions")
    if len(known) < 12:
        raise ValueError("Projected CFP field requires at least twelve eligible teams")
    auto_bids = projected_champions[:5]
    at_large = [name for name, _ in order if name not in auto_bids][:7]
    field = sorted(auto_bids + at_large, key=lambda name: ranking_index[name])
    projected_bracket = {
        "methodology": "Projected top-two conference finishers play a neutral-site title game, with the higher-rated finalist favored. Five highest-ranked champions and seven at-large; conference-specific rules and committee selections not modeled.",
        "conference_championships": championship_matchups,
        "seeds": [
            {"seed": i + 1, "team": name, "conference": conferences[name],
             "bid": "automatic" if name in auto_bids else "at_large",
             "bye": i < 4}
            for i, name in enumerate(field)
        ],
        "first_round": [{"home_seed": a, "away_seed": b,
                         "home": field[a-1], "away": field[b-1]}
                        for a, b in ((5, 12), (6, 11), (7, 10), (8, 9))],
    }
    conference_records = {t.name: {"wins": 0, "losses": 0} for t in teams}
    for g in games:
        if not g.completed or g.home not in known or g.away not in known:
            continue
        if conferences[g.home] == conferences[g.away] and conferences[g.home] != "Independent":
            winner = g.home if g.home_score > g.away_score else g.away
            loser = g.away if winner == g.home else g.home
            conference_records[winner]["wins"] += 1
            conference_records[loser]["losses"] += 1
    odds = {row["team"]: row for row in cfp["teams"]}
    conference_standings = {}
    for t in teams:
        conference_standings.setdefault(t.conference, []).append({
            "team": t.name, "conference": t.conference,
            "conference_wins": conference_records[t.name]["wins"],
            "conference_losses": conference_records[t.name]["losses"],
            "wins": ratings[t.name].wins, "losses": ratings[t.name].losses,
            "rating": ratings[t.name].adaptive_rating,
            "projected_wins": projections[t.name].projected_wins,
            "projected_conference_wins": projections[t.name].projected_conference_wins,
            "conference_title_odds": odds[t.name]["conference_title"],
            "cfp_odds": odds[t.name]["cfp_field"],
        })
    for rows in conference_standings.values():
        rows.sort(key=lambda r: (-r["conference_wins"], r["conference_losses"], -r["rating"], r["team"]))
    conference_strength = sorted(
        [{"conference": conf, "teams": len(rows),
          "average_rating": round(sum(r["rating"] for r in rows) / len(rows), 3),
          "best_team": max(rows, key=lambda r: r["rating"])["team"]}
         for conf, rows in conference_standings.items()],
        key=lambda r: -r["average_rating"],
    )
    return {
        "model_metadata": {
            "model_id": "workbook_2026_baseline",
            "model_status": "incumbent_not_v3_promoted",
            "prediction_scale": settings.win_probability_scale,
            "home_field_advantage": settings.home_field_advantage,
            "historical_study": "retrospective_research_only",
        },
        "conference_standings": conference_standings,
        "conference_strength": conference_strength,
        "cfp": cfp,
        "projected_bracket": projected_bracket,
        "season": season, "source": snapshot.get("source"),
        "retrieved_at": snapshot.get("retrieved_at"),
        "data_changed_at": snapshot.get("data_changed_at", snapshot.get("retrieved_at")),
        "summary": {"teams": len(teams), "completed_games": len(completed),
                    "upcoming_games": len(predictions)},
        "schedule": [
            {"game_id": g.game_id, "week": g.week, "home": g.home,
             "away": g.away, "neutral_site": g.neutral_site,
             "completed": g.completed, "home_score": g.home_score,
             "away_score": g.away_score}
            for g in games if g.home in known or g.away in known
        ],
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


def _has_verified_pregame_provenance(game: dict, forecast: dict) -> bool:
    """Exclude historical forecasts unless publication demonstrably preceded kickoff."""
    from datetime import datetime, timezone
    def aware(value):
        if not isinstance(value, str):
            return None
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return timestamp.astimezone(timezone.utc) if timestamp.tzinfo else None
        except ValueError:
            return None
    published = aware(forecast.get("forecast_recorded_at"))
    kickoff = aware(game.get("start_date"))
    return published is not None and kickoff is not None and published < kickoff


def build_performance_against_expectations(snapshot: dict, roster: list[dict],
                                           history: dict) -> dict:
    """Only score completed games with an archived, previously published forecast."""
    aliases = {"Miami": "Miami (FL)", "App State": "Appalachian State",
               "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}
    known = {t["name"] for t in roster}
    performance = {name: {"actual_wins": 0, "expected_wins": 0.0,
                          "games_with_forecasts": 0, "wins_above_expected": None}
                   for name in known}
    for g in snapshot["games"]:
        if not g["completed"] or g["home_score"] is None or g["away_score"] is None:
            continue
        forecast = history.get(str(g["game_id"]))
        if not forecast or not _has_verified_pregame_provenance(g, forecast):
            continue
        home = aliases.get(g["home"], g["home"])
        away = aliases.get(g["away"], g["away"])
        if (forecast.get("home") != home or forecast.get("away") != away):
            continue
        probability = forecast.get("home_win_probability")
        if isinstance(probability, bool) or not isinstance(probability, (float, int)) or not 0 <= probability <= 1:
            continue
        for team, expected, won in (
            (home, probability, g["home_score"] > g["away_score"]),
            (away, 1 - probability, g["away_score"] > g["home_score"]),
        ):
            if team in performance:
                row = performance[team]
                row["games_with_forecasts"] += 1
                row["expected_wins"] += expected
                row["actual_wins"] += int(won)
    for row in performance.values():
        if row["games_with_forecasts"]:
            row["expected_wins"] = round(row["expected_wins"], 3)
            row["wins_above_expected"] = round(
                row["actual_wins"] - row["expected_wins"], 3)
    return performance


def build_prediction_accuracy(snapshot: dict, history: dict, eligible_teams: set[str] | None = None) -> dict:
    """Score only completed games with genuine archived pregame probabilities."""
    games = 0
    correct = 0
    brier_total = 0.0
    aliases = {"Miami": "Miami (FL)", "App State": "Appalachian State",
               "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}
    for game in snapshot["games"]:
        if not game["completed"] or game["home_score"] is None or game["away_score"] is None:
            continue
        if game["home_score"] == game["away_score"]:
            continue
        forecast = history.get(str(game["game_id"]))
        if not forecast or not _has_verified_pregame_provenance(game, forecast):
            continue
        home = aliases.get(game["home"], game["home"])
        away = aliases.get(game["away"], game["away"])
        if eligible_teams is not None and (home not in eligible_teams or away not in eligible_teams):
            continue
        probability = forecast.get("home_win_probability")
        if (forecast.get("home") != home or forecast.get("away") != away
                or isinstance(probability, bool)
                or not isinstance(probability, (float, int))
                or not 0 <= probability <= 1):
            continue
        outcome = int(game["home_score"] > game["away_score"])
        games += 1
        correct += int((probability >= 0.5) == bool(outcome))
        brier_total += (probability - outcome) ** 2
    return {"games_evaluated": games, "correct_winners": correct,
            "winner_accuracy": round(correct / games, 4) if games else None,
            "brier_score": round(brier_total / games, 4) if games else None}
