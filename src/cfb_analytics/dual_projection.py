"""Dual projections: a Standard (equal-weight) and a Momentum (stair-step recency) model.

Both models share one opponent-strength fit and differ only in how a team's own games are averaged:

  Stage 1 (shared, once): ridge fit of points scored, pts(team, game) = mean + O(team) + D(opp) + h*site, over all
          completed games before the cutoff, shrunk toward preseason priors. FCS opponents form one pooled team.
          This is the only place opponent strength enters, so it is never counted twice.
  Stage 2 (per model): each team's opponent-adjusted game values
          offense a = points scored - (mean + D(opp) + h*site);  defense b = points allowed - (mean + O(opp) - h*site)
          are clipped at +/-CLIP points (one outlier cannot dominate) and averaged with model weights, shrunk toward the
          team's preseason prior with PRIOR_GAMES of weight:
            Standard  every game weight 1
            Momentum  stair-step weights, newest game highest (linear, or geometric with ratio r), rescaled to mean 1
                      so both models carry the same effective sample size against the prior.
Projection: home points = mean + O(home) + D(away) + h, away points = mean + O(away) + D(home) - h (no h when neutral);
win probability = 1 / (1 + exp(-margin / s)) with s fitted on earlier seasons only. Season records use the exact
(Poisson-binomial) win distribution of each model's own game probabilities.

Research and preview only: published production forecasts are untouched.
"""
import math
from collections import defaultdict

FCS = "FCS (pooled)"
CLIP = 24.0          # points; caps a single game's adjusted value
PRIOR_GAMES = 3.0    # stage-2 prior weight, in games
STAGE1_PRIOR = 2.0   # stage-1 ridge weight toward priors, in games
REGRESS = 0.6        # preseason prior = REGRESS x previous season's final rating
NEW_TEAM = (-6.0, 6.0)          # offense, defense prior for programs new to FBS (margin -12, as the incumbent)
FCS_PRIOR = (-10.0, 10.0)

WEIGHTINGS = {
    "standard": ("Standard", None),
    "momentum": ("Momentum (linear stair-step)", "linear"),
    "momentum_geo90": ("Momentum, geometric 0.90", 0.90),
    "momentum_geo80": ("Momentum, geometric 0.80", 0.80),
    "momentum_geo70": ("Momentum, geometric 0.70", 0.70),
}


def weights(n, kind):
    """Stair-step weights for n games ordered oldest -> newest, rescaled to mean 1 (newest highest)."""
    if n == 0:
        return []
    if kind is None:
        raw = [1.0] * n
    elif kind == "linear":
        raw = [float(i + 1) for i in range(n)]
    else:
        raw = [kind ** (n - 1 - i) for i in range(n)]
    total = sum(raw)
    return [w * n / total for w in raw]


def node(row, team_field):
    return row[team_field] if row["team_fbs" if team_field == "team" else "opp_fbs"] else FCS


def stage1(rows, priors, iterations=60):
    """Shared opponent-strength fit. rows: team-game rows strictly before the cutoff (both sides of each game)."""
    obs = [(node(r, "team"), node(r, "opp"), 1 if r["site"] == "home" else -1 if r["site"] == "away" else 0, float(r["pf"]))
           for r in rows if r.get("pf") is not None]
    teams = sorted({o[0] for o in obs} | {o[1] for o in obs} | set(priors))
    prior = {t: priors.get(t, FCS_PRIOR if t == FCS else NEW_TEAM) for t in teams}
    off = {t: prior[t][0] for t in teams}
    dfn = {t: prior[t][1] for t in teams}
    mean = sum(o[3] for o in obs) / len(obs) if obs else 28.0
    home = 1.5
    by_off, by_def = defaultdict(list), defaultdict(list)
    for o in obs:
        by_off[o[0]].append(o); by_def[o[1]].append(o)
    for _ in range(iterations if obs else 0):
        for t in teams:
            items = by_off.get(t, [])
            off[t] = (sum(v - mean - dfn[d] - home * s for _, d, s, v in items) + STAGE1_PRIOR * prior[t][0]) / (len(items) + STAGE1_PRIOR)
        for t in teams:
            items = by_def.get(t, [])
            dfn[t] = (sum(v - mean - off[o] - home * s for o, _, s, v in items) + STAGE1_PRIOR * prior[t][1]) / (len(items) + STAGE1_PRIOR)
        hs = [o for o in obs if o[2]]
        home = sum(s * (v - mean - off[o] - dfn[d]) for o, d, s, v in hs) / len(hs) if hs else home
        mean = sum(v - off[o] - dfn[d] - home * s for o, d, s, v in obs) / len(obs)
    return {"mean": mean, "home": home, "off": off, "def": dfn, "prior": prior}


def game_values(rows, fit):
    """Per FBS team, chronological [(date, game_id, offense value, defense value)] (clipped)."""
    out = defaultdict(list)
    for r in rows:
        if not r["team_fbs"] or r.get("pf") is None:
            continue
        opp = node(r, "opp")
        s = 1 if r["site"] == "home" else -1 if r["site"] == "away" else 0
        a = r["pf"] - (fit["mean"] + fit["def"].get(opp, 0.0) + fit["home"] * s)
        b = r["pa"] - (fit["mean"] + fit["off"].get(opp, 0.0) - fit["home"] * s)
        clip = lambda v: max(-CLIP, min(CLIP, v))
        out[r["team"]].append((r["date"] or "", r["game_id"], clip(a), clip(b)))
    for t in out:
        out[t].sort()
    return out


def model_ratings(values, fit, kind):
    """{team: (offense, defense)} for one weighting, shrunk toward each team's preseason prior."""
    ratings = {}
    for t, prior in fit["prior"].items():
        games = values.get(t, [])
        w = weights(len(games), kind)
        o = (sum(wi * g[2] for wi, g in zip(w, games)) + PRIOR_GAMES * prior[0]) / (sum(w) + PRIOR_GAMES)
        d = (sum(wi * g[3] for wi, g in zip(w, games)) + PRIOR_GAMES * prior[1]) / (sum(w) + PRIOR_GAMES)
        ratings[t] = (o, d)
    ratings[FCS] = (fit["off"].get(FCS, FCS_PRIOR[0]), fit["def"].get(FCS, FCS_PRIOR[1]))
    return ratings


def project(home, away, neutral, ratings, fit):
    """(home points, away points, home margin) for one game."""
    h = 0.0 if neutral else fit["home"]
    ho, hd = ratings.get(home, ratings[FCS])
    ao, ad = ratings.get(away, ratings[FCS])
    hp = fit["mean"] + ho + ad + h
    ap = fit["mean"] + ao + hd - h
    return hp, ap, hp - ap


def probability(margin, scale):
    return 1 / (1 + math.exp(-margin / scale))


def fit_scale(margins, outcomes):
    """Logistic scale s minimising log loss of p = 1/(1+exp(-margin/s)) (golden-section search)."""
    def loss(s):
        total = 0.0
        for m, y in zip(margins, outcomes):
            p = min(max(probability(m, s), 1e-6), 1 - 1e-6)
            total -= y * math.log(p) + (1 - y) * math.log(1 - p)
        return total
    lo, hi = 3.0, 40.0
    for _ in range(60):
        a, b = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
        if loss(a) < loss(b):
            hi = b
        else:
            lo = a
    return (lo + hi) / 2


def win_distribution(probabilities):
    """Exact distribution of the number of wins (Poisson-binomial)."""
    dist = [1.0]
    for p in probabilities:
        nxt = [0.0] * (len(dist) + 1)
        for k, q in enumerate(dist):
            nxt[k] += q * (1 - p)
            nxt[k + 1] += q * p
        dist = nxt
    return dist


def next_priors(final_ratings):
    """Preseason priors for the following season: regress each FBS team's final rating toward average."""
    return {t: (REGRESS * o, REGRESS * d) for t, (o, d) in final_ratings.items() if t != FCS}
