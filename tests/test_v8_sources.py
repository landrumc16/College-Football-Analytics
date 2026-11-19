"""V8 M1 derivation: per team-game counts from fixture plays/drives (hand-computed expectations)."""
from cfb_analytics import v8_sources as s


def play(offense, kind, down, distance, gained, period=1, off_score=0, def_score=0, to_goal=50, drive=1, ppa=0.1):
    return {"offense": offense, "defense": "B" if offense == "A" else "A", "playType": kind, "down": down,
            "distance": distance, "yardsGained": gained, "period": period, "offenseScore": off_score,
            "defenseScore": def_score, "yardsToGoal": to_goal, "driveId": drive, "ppa": ppa, "gameId": 1}


def test_success_definition():
    assert s.successful(1, 10, 5, False) and not s.successful(1, 10, 4, False)
    assert s.successful(2, 10, 7, False) and not s.successful(2, 10, 6, False)
    assert s.successful(3, 4, 4, False) and not s.successful(4, 4, 3, False)
    assert s.successful(3, 10, 2, True)  # touchdown


def test_garbage_time_thresholds():
    assert not s.is_garbage(1, 50)
    assert s.is_garbage(2, 39) and not s.is_garbage(2, 38)
    assert s.is_garbage(3, -29) and not s.is_garbage(3, 28)
    assert s.is_garbage(4, 23) and not s.is_garbage(4, 22)


def test_offense_counts_hand_computed():
    plays = [
        play("A", "Rush", 1, 10, 12),                       # explosive rush, success
        play("A", "Rush", 1, 10, -1),                       # stuff, fail
        play("A", "Pass Reception", 2, 11, 25),             # explosive pass, success
        play("A", "Sack", 3, 6, -7),                        # dropback, sack, third down fail
        play("A", "Pass Incompletion", 3, 5, 0, drive=2),   # third down fail
        play("A", "Rushing Touchdown", 3, 2, 2, to_goal=2, drive=3),   # red zone, third-down conversion, TD success
        play("A", "Pass Interception Return", 1, 10, 0, drive=4),      # turnover, fail
        play("A", "Rush", 1, 10, 30, period=4, off_score=40, def_score=10),  # garbage time: excluded from efficiency
        play("A", "Penalty", 1, 10, 5),                     # not scrimmage
        play("B", "Rush", 1, 10, 50),                       # other offense
        play("A", "Kickoff", None, None, 60),               # no down
    ]
    drives = [
        {"offense": "A", "id": 1, "plays": 4, "startOffenseScore": 0, "endOffenseScore": 3, "elapsed": {"minutes": 2, "seconds": 30}, "startYardsToGoal": 75},
        {"offense": "A", "id": 3, "plays": 1, "startOffenseScore": 3, "endOffenseScore": 10, "elapsed": {"minutes": 0, "seconds": 10}, "startYardsToGoal": 2},
        {"offense": "A", "id": 4, "plays": 1, "startOffenseScore": 10, "endOffenseScore": 10, "elapsed": {"minutes": 0, "seconds": 20}, "startYardsToGoal": 60},
        {"offense": "B", "id": 9, "plays": 3, "startOffenseScore": 0, "endOffenseScore": 7, "elapsed": {"minutes": 1, "seconds": 0}},
    ]
    c = s.offense_counts(plays, drives, "A")
    assert c["plays"] == 7                       # non-garbage scrimmage plays
    assert c["yards"] == 12 - 1 + 25 - 7 + 0 + 2 + 0 == 31
    assert c["succ"] == 3                        # 12-yd rush, 25-yd pass, TD
    assert (c["rush"], c["rush_yds"], c["rush_succ"], c["rush_expl"], c["rush_stuff"]) == (3, 13, 2, 1, 1)
    assert (c["db"], c["db_yds"], c["db_succ"], c["db_expl"], c["sacks"]) == (4, 18, 1, 1, 1)
    assert c["expl"] == 2
    assert (c["third"], c["third_conv"]) == (3, 1)
    assert c["turnovers"] == 1
    assert (c["late_plays"], c["late_succ"]) == (0, 0)       # garbage-margin 4th quarter is not close
    assert (c["drives"], c["drive_pts"], c["drive_plays"], c["drive_secs"]) == (3, 10, 6, 180)
    assert (c["rz_trips"], c["rz_td"], c["rz_pts"]) == (1, 1, 7)
    assert c["ppa_n"] == 7 and abs(c["ppa"] - 0.7) < 1e-9


def test_close_late_counts_include_fourth_quarter_one_score_games():
    c = s.offense_counts([play("A", "Rush", 1, 10, 6, period=4, off_score=14, def_score=20)], [], "A")
    assert (c["late_plays"], c["late_succ"]) == (1, 1)


def test_derive_season_rows_both_sides_and_membership():
    teams = [{"school": "A", "conference": "SEC"}, {"school": "B", "conference": "Big 12"}]
    games = [{"id": 1, "week": 1, "seasonType": "regular", "startDate": "2025-08-30T16:00:00.000Z", "completed": True,
              "homeTeam": "A", "awayTeam": "C", "homePoints": 35, "awayPoints": 3, "neutralSite": False, "awayConference": "SWAC"},
             {"id": 2, "week": 2, "seasonType": "regular", "startDate": "2025-09-06T16:00:00.000Z", "completed": False,
              "homeTeam": "A", "awayTeam": "B", "homePoints": None, "awayPoints": None},
             {"id": 3, "week": 1, "seasonType": "regular", "startDate": "2025-08-30T16:00:00.000Z", "completed": True,
              "homeTeam": "D", "awayTeam": "E", "homePoints": 10, "awayPoints": 7}]
    membership, rows = s.derive_season(2025, teams, games, [], [play("A", "Rush", 1, 10, 5)])
    assert membership == {"A": "SEC", "B": "Big 12"}
    assert [(r["team"], r["opp"], r["site"], r["pf"], r["pa"]) for r in rows] == [("A", "C", "home", 35, 3), ("C", "A", "away", 3, 35)]
    assert rows[0]["team_fbs"] and not rows[0]["opp_fbs"] and rows[1]["team_conf"] == "SWAC"
    assert rows[0]["has_plays"] and rows[0]["off"]["plays"] == 1 and rows[0]["off"]["succ"] == 1
    assert rows[1]["off"]["plays"] == 0                                    # C ran no plays in the fixture
