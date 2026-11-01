"""Deterministic 10,000-season Monte Carlo CFP forecast.

Model approximation: conference champions are regular-season conference-win leaders
(ties use seeded random choice). Conference title games and committee judgment
are not yet modeled. The five highest-ranked champions receive automatic bids,
then seven at-large teams. All twelve seeds follow simulated projected-win/rating
scores. Four highest seeds receive byes. Playoff games use neutral-site ratings.
"""
from collections import Counter, defaultdict
from math import sqrt
from random import Random
from .model import win_probability_from_rating_gap


def simulate_cfp(teams, games, *, simulations=10000, seed=2026,
                 scale=18.0, home_edge=3.0, fcs_rating=-26.0):
    """teams: name -> {conference,rating,wins,conference_wins}.
    games: remaining {home,away,neutral_site} records.
    """
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    rng = Random(seed)
    names = sorted(teams)
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
    for game in games:
        home, away = game["home"], game["away"]
        gap = (teams[home]["rating"] if home in teams else fcs_rating) - (teams[away]["rating"] if away in teams else fcs_rating)
        if not game.get("neutral_site", False):
            gap += home_edge
        same_conf = home in teams and away in teams and teams[home]["conference"] == teams[away]["conference"] and teams[home]["conference"] != "Independent"
        prepared.append((home, away, win_probability_from_rating_gap(gap, scale), same_conf))
    totals = defaultdict(Counter)
    sum_wins = Counter()
    title_counts = Counter()
    for _ in range(simulations):
        wins = {n: teams[n]["wins"] for n in names}
        conf_wins = {n: teams[n]["conference_wins"] for n in names}
        for home, away, p, same_conf in prepared:
            winner = home if rng.random() < p else away
            if winner in wins:
                wins[winner] += 1
                if same_conf:
                    conf_wins[winner] += 1
        for n in names:
            sum_wins[n] += wins[n]
        mean = sum(wins.values()) / len(names)
        std = sqrt(sum((wins[n]-mean)**2 for n in names)/len(names)) or 1
        scores = {n: 0.5*(wins[n]-mean)/std + 0.5*rating_z[n] for n in names}
        champions = []
        for members in conferences.values():
            best = max(conf_wins[n] for n in members)
            tied = [n for n in members if conf_wins[n] == best]
            champion = rng.choice(tied)
            champions.append(champion)
            totals[champion]["conference_title"] += 1
        automatic = sorted(champions, key=lambda n: (-scores[n], n))[:5]
        others = sorted((n for n in names if n not in automatic), key=lambda n: (-scores[n], n))
        field = sorted(automatic + others[:7], key=lambda n: (-scores[n], n))
        for i, n in enumerate(field):
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
        for n in round_one:
            totals[n]["quarterfinal"] += 1
        quarter = [game(field[a-1],n) for a,n in zip((4,3,2,1),round_one)]
        for n in quarter:
            totals[n]["semifinal"] += 1
        semis = [game(quarter[0],quarter[3]), game(quarter[1],quarter[2])]
        for n in semis:
            totals[n]["final"] += 1
        title_counts[game(*semis)] += 1
    return {
        "simulations": simulations, "seed": seed,
        "scenario": "current_model_probabilities",
        "methodology": "Regular-season conference leaders; five highest-ranked champions plus seven at-large; seeded neutral-site playoff. Conference championship games and CFP committee decisions not modeled.",
        "teams": [
            {"team": n, "conference": teams[n]["conference"],
             "average_wins": round(sum_wins[n]/simulations, 3),
             **{k: round(totals[n][k]/simulations, 4) for k in ("conference_title","cfp_field","first_round_bye","quarterfinal","semifinal","final")},
             "national_title": round(title_counts[n]/simulations, 4)}
            for n in sorted(names, key=lambda n:(-title_counts[n],n))
        ],
    }
