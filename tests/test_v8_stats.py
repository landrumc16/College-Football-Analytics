"""V8 M2 statistics: synthetic leagues with known truth, membership rules, leakage and reproducibility."""
import copy
import itertools
import json

from cfb_analytics import v8_sources as src
from cfb_analytics import v8_stats as st


def counts(plays, succ, yards=None, drives=10, pts=20):
    c = src.empty_counts()
    c.update(plays=plays, succ=succ, yards=yards if yards is not None else plays * 5, ppa=0.0, ppa_n=plays,
             drives=drives, drive_pts=pts, rush=plays // 2, rush_succ=succ // 2, db=plays - plays // 2,
             db_succ=succ - succ // 2, third=10, third_conv=4, rz_trips=3, rz_td=2, rz_pts=17)
    return c


def game(gid, date, home, away, home_off, away_off, confs, fbs=None, neutral=False):
    fbs = fbs if fbs is not None else set(confs)
    rows = []
    for team, opp, side, off in ((home, away, "home", home_off), (away, home, "away", away_off)):
        rows.append({"game_id": str(gid), "season": 2025, "week": 1, "season_type": "regular", "date": date,
                     "team": team, "opp": opp, "site": "neutral" if neutral else side,
                     "team_conf": confs.get(team, "FCS"), "opp_conf": confs.get(opp, "FCS"),
                     "team_fbs": team in fbs, "opp_fbs": opp in fbs, "pf": off["drive_pts"], "pa": 0,
                     "has_plays": True, "has_drives": True, "off": off})
    for r in rows:
        r["pa"] = next(x["pf"] for x in rows if x is not r)
    return rows


def league(strength_off, strength_def, schedule, confs, plays=60):
    """Each game: offense success = 0.42 + off(team) - def(opp) exactly (no noise)."""
    rows = []
    for gid, (date, home, away) in enumerate(schedule, 1):
        h = round(plays * (0.42 + strength_off[home] - strength_def[away]))
        a = round(plays * (0.42 + strength_off[away] - strength_def[home]))
        rows += game(gid, date, home, away, counts(plays, h), counts(plays, a), confs)
    return rows


def test_adjustment_rewards_strong_schedule_and_penalizes_weak_schedule():
    # A and B have identical true offenses; A plays the three best defenses, B the three worst.
    teams = list("ABCDEFGH")
    off = dict.fromkeys(teams, 0.0)
    dfn = {"C": 0.12, "D": 0.10, "E": 0.08, "F": -0.08, "G": -0.10, "H": -0.12, "A": 0.0, "B": 0.0}
    confs = dict.fromkeys(teams, "SEC")
    sched = [(f"2025-09-{d:02d}", "A", o) for d, o in zip((1, 8, 15), "CDE")]
    sched += [(f"2025-09-{d:02d}", "B", o) for d, o in zip((1, 8, 15), "FGH")]
    sched += [(f"2025-10-{i + 1:02d}", x, y) for i, (x, y) in enumerate(itertools.combinations("CDEFGH", 2))]
    stats = st.team_stats(league(off, dfn, sched, confs), 2025)
    a, b = stats["teams"]["A"]["offense"]["sr"], stats["teams"]["B"]["offense"]["sr"]
    assert a["raw"] < b["raw"]                       # raw numbers flatter B
    # Adjustment closes most of the schedule-driven gap; the remainder is intended small-sample shrinkage.
    assert abs(a["adjusted"] - b["adjusted"]) < 0.3 * (b["raw"] - a["raw"])
    assert stats["teams"]["H"]["defense"]["sr"]["adjusted_rank"] > stats["teams"]["C"]["defense"]["sr"]["adjusted_rank"]


def test_power_membership_by_season_notre_dame_and_transitions():
    assert st.is_power("Oregon State", "Pac-12", 2023) and not st.is_power("Oregon State", "Pac-12", 2024)
    assert st.is_power("Notre Dame", "FBS Independents", 2016) and st.is_power("Notre Dame", "FBS Independents", 2026)
    assert st.is_power("BYU", "Big 12", 2023) and not st.is_power("BYU", "FBS Independents", 2022)
    assert not st.is_power("Boise State", "Mountain West", 2025) and not st.is_power("Army", "FBS Independents", 2023)


def test_power_view_counts_only_power_opponents_and_fcs_excluded_from_fit():
    confs = {"A": "SEC", "B": "SEC", "ND": "FBS Independents", "G": "Mountain West"}
    confs["Notre Dame"] = confs.pop("ND")
    fbs = set(confs)
    rows = []
    rows += game(1, "2025-09-01", "A", "Notre Dame", counts(60, 30), counts(60, 24), confs)
    rows += game(2, "2025-09-08", "A", "G", counts(60, 40), counts(60, 20), confs)
    rows += game(3, "2025-09-15", "A", "Tiny FCS", counts(60, 55), counts(60, 10), confs, fbs=fbs)
    rows += game(4, "2025-09-22", "B", "G", counts(60, 33), counts(60, 25), confs)
    rows += game(5, "2025-09-29", "Notre Dame", "B", counts(60, 28), counts(60, 26), confs)
    s = st.team_stats(rows, 2025)
    a = s["teams"]["A"]
    assert a["games"] == 3 and a["fcs_games"] == 1 and a["power_games"] == 1
    assert a["offense"]["sr"]["power"] == 0.5 and a["offense"]["sr"]["power_games"] == 1   # only vs Notre Dame
    assert a["offense"]["sr"]["raw"] == round((30 + 40 + 55) / 180, 4)                       # FCS included in raw
    assert "Tiny FCS" not in s["teams"]                                                      # profiles: FBS only
    assert s["teams"]["G"]["offense"]["sr"]["power"] is None and s["teams"]["G"]["offense"]["sr"]["power_rank"] is None
    fit = st.adjust(st.pair_units(rows), "sr")
    assert "Tiny FCS" not in fit["off"]                                                       # not in the fit


def test_small_samples_shrink_and_carry_larger_uncertainty():
    confs = dict.fromkeys("ABCD", "ACC")
    rows = game(1, "2025-09-01", "A", "B", counts(20, 18), counts(20, 8), confs)       # tiny sample
    rows += game(2, "2025-09-01", "C", "D", counts(300, 165), counts(300, 120), confs)  # large sample
    s = st.team_stats(rows, 2025)
    a, c = s["teams"]["A"]["offense"]["sr"], s["teams"]["C"]["offense"]["sr"]
    assert a["raw"] == 0.9 and a["adjusted"] < 0.7          # heavily shrunk toward the mean
    assert a["se"] > c["se"]


def test_no_future_leakage_and_reproducibility():
    teams = list("ABCD")
    confs = dict.fromkeys(teams, "Big Ten")
    sched = [("2025-09-01", "A", "B"), ("2025-09-01", "C", "D"), ("2025-09-08", "A", "C"), ("2025-09-08", "B", "D")]
    rows = league(dict.fromkeys(teams, 0.0), dict.fromkeys(teams, 0.0), sched, confs)
    asof = st.team_stats(rows, 2025, as_of="2025-09-05")
    future = copy.deepcopy(rows)
    for r in future:
        if r["date"] >= "2025-09-05":
            r["off"]["succ"] = r["off"]["plays"]    # wildly different future games
    assert st.team_stats(future, 2025, as_of="2025-09-05") == asof
    assert asof["teams"]["A"]["games"] == 1
    assert json.dumps(st.team_stats(rows, 2025), sort_keys=True) == json.dumps(st.team_stats(rows, 2025), sort_keys=True)


def test_ties_share_a_rank_and_missing_values_are_unranked():
    assert st.rank({"A": 0.5, "B": 0.5, "C": 0.4, "D": None}, True) == {"A": 1, "B": 1, "C": 3}
    assert st.rank({"A": 0.1, "B": 0.3}, False) == {"A": 1, "B": 2}


def test_trend_labels_only_beyond_uncertainty():
    steady = st.trend([0.0, 0.01, -0.01, 0.0, 0.01, -0.01, 0.0], 3)
    assert steady["label"] == "steady"
    rising = st.trend([-0.2, -0.21, -0.19, -0.2, 0.2, 0.21, 0.19], 3)
    assert rising["label"] == "improving" and rising["change"] > 0
    assert st.trend([0.1, 0.2, 0.3], 3) is None            # too few games


def test_definitions_are_complete():
    d = st.definitions()
    assert {"ppd", "sr", "epa", "expl", "third", "rz_td", "late", "sack", "stuff"} <= set(d)
    assert all({"label", "numerator", "denominator"} <= set(v) for v in d.values())
