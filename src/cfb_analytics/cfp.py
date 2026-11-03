"""Deterministic 10,000-season Monte Carlo CFP forecast.

Model approximation: top-two conference-win finishers play neutral-site title games.
Conference-specific tiebreakers and committee judgment are not modeled. The five highest-ranked champions receive automatic bids,
then seven at-large teams. All twelve seeds follow simulated projected-win/rating
scores. Four highest seeds receive byes. Playoff games use neutral-site ratings.
"""
from collections import Counter, defaultdict
from math import isfinite, sqrt
from random import Random
from .model import win_probability_from_rating_gap


def simulate_cfp(teams, games, *, simulations=10000, seed=2026,
                 scale=18.0, home_edge=3.0, fcs_rating=-26.0):
    """teams: name -> {conference,rating,wins,conference_wins}.
    games: remaining {home,away,neutral_site} records.
    """
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    if not teams:
        raise ValueError("at least one team is required")
    if scale <= 0:
        raise ValueError("probability scale must be positive")
    if len(teams) < 12:
        raise ValueError("CFP simulation requires at least 12 eligible teams")
    for name, team in teams.items():
        if not isinstance(team["rating"], (int, float)) or not isfinite(team["rating"]):
            raise ValueError(f"Invalid rating for {name}")
        for key in ("wins", "conference_wins"):
            value = team[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"Invalid {key} for {name}")
        if team["conference"] != "Independent" and not team["conference"]:
            raise ValueError(f"Missing conference for {name}")
    rng = Random(seed)
    names = sorted(teams)
    if len(names) != len(set(names)):
        raise ValueError("duplicate team names")
    conferences = defaultdict(list)
    for name in names:
        conf = teams[name]["conference"]
        if conf != "Independent":
            conferences[conf].append(name)
    # Static rating standardization; each season recomputes win standardization.
    rating_mean = sum(teams[n]["rating"] for n in names) / len(names)
    rating_std = sqrt(sum((teams[n]["rating"] - rating_mean)**2 for n in names) / len(names)) or 1
    rating_z = {n:(teams[n]["rating"]-rating_mean)/rating_std for n in names}
    prepared = []
    seen_games = set()
    for game in games:
        home, away = game["home"], game["away"]
        matchup = tuple(sorted((home, away)))
        if matchup in seen_games:
            raise ValueError(f"Duplicate remaining matchup: {matchup}")
        seen_games.add(matchup)
        if home not in teams and away not in teams:
            # FCS-vs-FCS games cannot change any modeled FBS win total.
            # Retain FBS-vs-FCS games below using the FCS rating assumption.
            continue
        if home == away:
            raise ValueError("self-matchup in remaining schedule")
        gap = (teams[home]["rating"] if home in teams else fcs_rating) - (teams[away]["rating"] if away in teams else fcs_rating)
        if not game.get("neutral_site", False):
            gap += home_edge
        same_conf = home in teams and away in teams and teams[home]["conference"] == teams[away]["conference"] and teams[home]["conference"] != "Independent"
        prepared.append((home, away, win_probability_from_rating_gap(gap, scale), same_conf))
    totals = defaultdict(Counter)
    conference_matchups = defaultdict(Counter)
    sum_wins = Counter()
    win_histograms = defaultdict(Counter)
    title_counts = Counter()
    seed_counts = defaultdict(Counter)
    for _ in range(simulations):
        wins = {n: teams[n]["wins"] for n in names}
        conf_wins = {n: teams[n]["conference_wins"] for n in names}
        for home, away, p, same_conf in prepared:
            winner = home if rng.random() < p else away
            if winner in wins:
                wins[winner] += 1
                if same_conf:
                    conf_wins[winner] += 1
        champions = []
        for conference, members in conferences.items():
            # Model the two highest conference-win finishers in a neutral-site
            # championship. Ties for finalists are resolved by model rating,
            # then team name. Conference-specific tiebreakers are not modeled.
            finalists = sorted(members, key=lambda n: (-conf_wins[n], -teams[n]["rating"], n))[:2]
            if len(finalists) == 2:
                a, b = finalists
                conference_matchups[conference][tuple(sorted((a, b)))] += 1
                probability = win_probability_from_rating_gap(
                    teams[a]["rating"] - teams[b]["rating"], scale)
                champion = a if rng.random() < probability else b
            else:
                champion = finalists[0]
            champions.append(champion)
            totals[champion]["conference_title"] += 1
            # Conference title games count toward final wins and selection scores.
            if len(finalists) == 2:
                wins[champion] += 1
        for n in names:
            sum_wins[n] += wins[n]
            win_histograms[n][wins[n]] += 1
        mean = sum(wins.values()) / len(names)
        std = sqrt(sum((wins[n]-mean)**2 for n in names)/len(names)) or 1
        scores = {n: 0.5*(wins[n]-mean)/std + 0.5*rating_z[n] for n in names}
        automatic = sorted(champions, key=lambda n: (-scores[n], n))[:5]
        others = sorted((n for n in names if n not in automatic), key=lambda n: (-scores[n], n))
        field = sorted(automatic + others[:7], key=lambda n: (-scores[n], n))
        for i, n in enumerate(field):
            seed_counts[n][i + 1] += 1
            totals[n]["cfp_field"] += 1
            if i < 4:
                totals[n]["first_round_bye"] += 1
        if len(field) != 12:
            continue
        def game(a, b):
            p = win_probability_from_rating_gap(teams[a]["rating"]-teams[b]["rating"], scale)
            return a if rng.random() < p else b
        # Seeds 5-12, 6-11, 7-10, 8-9; winners play 4,3,2,1.
        round_one = [game(field[a-1],field[b-1]) for a,b in ((5,12),(6,11),(7,10),(8,9))]
        for n in field[:4] + round_one:
            totals[n]["quarterfinal"] += 1
        quarter = [game(field[a-1],n) for a,n in zip((4,3,2,1),round_one)]
        for n in quarter:
            totals[n]["semifinal"] += 1
        semis = [game(quarter[0],quarter[3]), game(quarter[1],quarter[2])]
        for n in semis:
            totals[n]["final"] += 1
        title_counts[game(*semis)] += 1
    def percentile_win(histogram, percentile):
        target = simulations * percentile
        count = 0
        for wins, occurrences in sorted(histogram.items()):
            count += occurrences
            if count >= target:
                return wins
        return max(histogram)

    return {
        "simulations": simulations, "seed": seed,
        "scenario": "current_model_probabilities",
        "methodology": "Neutral-site championship games between each conference's two leading conference-win teams; ties resolved by model rating. Five highest-ranked champions plus seven at-large. Conference-specific qualification and tiebreak rules and CFP committee decisions not modeled.",
        "conference_championships": [
            {"conference": conference,
             "most_common_matchup": list(max(matchups, key=matchups.get)) if matchups else [],
             "matchup_probability": round(max(matchups.values()) / simulations, 4) if matchups else 0}
            for conference, matchups in sorted(conference_matchups.items())
        ],
        "teams": [
            {"team": n, "conference": teams[n]["conference"],
             "average_wins": round(sum_wins[n]/simulations, 3),
             "wins_p10": percentile_win(win_histograms[n], 0.10),
             "wins_p90": percentile_win(win_histograms[n], 0.90),
             "most_likely_seed": (max(seed_counts[n], key=lambda seed: (seed_counts[n][seed], -seed)) if seed_counts[n] else None),
             "average_seed_when_selected": (round(sum(seed * count for seed, count in seed_counts[n].items()) / sum(seed_counts[n].values()), 2) if seed_counts[n] else None),
             "bowl_eligible": round(sum(count for wins, count in win_histograms[n].items() if wins >= 6) / simulations, 4),
             **{k: round(totals[n][k]/simulations, 4) for k in ("conference_title","cfp_field","first_round_bye","quarterfinal","semifinal","final")},
             "national_title": round(title_counts[n]/simulations, 4)}
            for n in sorted(names, key=lambda n:(-title_counts[n],n))
        ],
    }
