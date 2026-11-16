"""V7 Milestone 2 historical market archive: correctness, provider policy, licensing and fail-safe tests.

Fixtures are synthetic except the four documented 2016 Texas Tech games from the
Milestone 1 hand-check (factual scores from the verified archive; three lines each).
"""
import gzip
import json
import random
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cfb_analytics import v7_market_archive as m
from cfb_analytics.v7_market_archive import ArchiveRejected


def line(provider, spread=None, total=None, spread_open=None, total_open=None, formatted=None):
    return {"provider": provider, "spread": spread, "overUnder": total, "spreadOpen": spread_open,
            "overUnderOpen": total_open, "formattedSpread": formatted}


def cfbd(gid, home, away, hs, as_, lines):
    return {"id": int(gid), "homeTeam": home, "awayTeam": away, "homeScore": hs, "awayScore": as_, "lines": lines}


def archive_game(gid, season, home, away, hs, as_, kickoff, neutral=False):
    return {"game_id": str(gid), "season": season, "season_type": "regular", "kickoff": kickoff, "home": home, "away": away,
            "home_score": hs, "away_score": as_, "neutral_site": neutral, "fbs_participant": True, "fbs_game": True}


# Documented Milestone 1 hand-check games (2016).
TTU_WVU = cfbd(400869627, "Texas Tech", "West Virginia", 17, 48,
               [line("teamrankings", 3, 82), line("numberfire", 3, 82), line("consensus", -1)])
ASU_TTU = cfbd(400869100, "Arizona State", "Texas Tech", 68, 55,
               [line("teamrankings", 1.5, 80), line("numberfire", 1, 79), line("consensus", -5)])
TTU_LATECH = cfbd(400869359, "Texas Tech", "Louisiana Tech", 59, 45,
                  [line("teamrankings", -11, 82.5), line("numberfire", -10.5, 80.5), line("consensus", -12)])
TTU_SFA = cfbd(400869625, "Texas Tech", "Stephen F. Austin", 69, 17, [line("consensus", -42)])
TTU_KU = cfbd(400869598, "Texas Tech", "Kansas", 55, 19,
              [line("consensus", -27.5, 78.5, formatted="Texas Tech -27.5")])
DOCUMENTED = [TTU_WVU, ASU_TTU, TTU_LATECH, TTU_SFA, TTU_KU]
KICKOFFS = {"400869627": "2016-10-15T16:00:00.000Z", "400869100": "2016-09-11T02:00:00.000Z",
            "400869359": "2016-09-17T23:00:00.000Z", "400869625": "2016-09-04T00:00:00.000Z",
            "400869598": "2016-09-30T00:30:00.000Z"}


def results_for(rows, season=2016):
    return {str(r["id"]): {"game_id": str(r["id"]), "season": season, "season_type": "regular",
                           "kickoff": KICKOFFS.get(str(r["id"]), f"{season}-10-01T00:00:00Z"),
                           "home": r["homeTeam"], "away": r["awayTeam"], "home_score": r["homeScore"],
                           "away_score": r["awayScore"], "neutral_site": False, "completed": True} for r in rows}


def statuses(rows):
    outcomes, cov = m.build_season(2016, rows, results_for(rows))
    return {o["game_id"]: o for o in outcomes}, cov


# ---------------------------------------------------------------- provider policy and documented disputes
def test_documented_2016_texas_tech_provider_disagreements():
    """Policy v2: in both documented 2016 disputes consensus is the sole outlier against two agreeing books."""
    by_id, cov = statuses(DOCUMENTED)
    wvu = m.select_market(m.normalize([TTU_WVU])[0]["400869627"], "spread", 1)
    assert wvu["reason"] == "consensus_outlier_replaced" and wvu["provider"] == "teamrankings"
    assert wvu["value"] == 3 and wvu["status"] == "ok" and wvu["disagreement"] == 0
    assert by_id["400869627"]["home_ats"] == "L"            # Texas Tech lost by 31 as a 3-point underdog
    asu = m.select_market(m.normalize([ASU_TTU])[0]["400869100"], "spread", 1)
    assert asu["reason"] == "consensus_outlier_replaced" and asu["provider"] == "teamrankings" and asu["disagreement"] == 0.5
    assert by_id["400869100"]["home_ats"] == "W"            # Arizona State +1.5, won by 13
    latech = m.select_market(m.normalize([TTU_LATECH])[0]["400869359"], "spread", 1)
    assert latech["status"] == "ok" and latech["provider"] == "consensus" and latech["disagreement"] == 1.25  # vs median(-11,-10.5)
    sfa_spread = m.select_market(m.normalize([TTU_SFA])[0]["400869625"], "spread", 1)
    assert sfa_spread["status"] == "ok" and sfa_spread["single_provider"]
    assert by_id["400869625"]["total_status"] == "no_line"
    assert cov["spread_consensus_replaced"] == 2 and cov["spread_disputed"] == 0


def test_dispute_flagged_when_no_independent_majority_exists():
    row = cfbd(30, "A", "B", 24, 20, [line("consensus", -3, 50), line("DraftKings", -7, 50)])
    sel = m.select_market(m.normalize([row])[0]["30"], "spread", 1)
    assert sel["provider"] == "consensus" and sel["status"] == "disputed" and sel["disagreement"] == 4
    row = cfbd(31, "A", "B", 24, 20, [line("consensus", -3, 50), line("DraftKings", -7, 50), line("Bovada", -2, 50)])
    sel = m.select_market(m.normalize([row])[0]["31"], "spread", 1)
    assert sel["provider"] == "consensus" and sel["status"] == "ok"   # books disagree (range 5): no replacement; |-3 - (-4.5)| = 1.5


def test_totals_selected_independently_with_recorded_fallback():
    total = m.select_market(m.normalize([TTU_LATECH])[0]["400869359"], "total", 1)
    assert total["provider"] == "teamrankings" and total["reason"] == "fallback_missing_value"
    assert total["value"] == 82.5 and total["status"] == "ok"  # |82.5-80.5| = 2 < 3


def test_selection_is_deterministic_regardless_of_row_order():
    rows = []
    for _ in range(20):
        r = json.loads(json.dumps(TTU_LATECH))
        random.shuffle(r["lines"])
        rows.append(m.select_market(m.normalize([r])[0]["400869359"], "spread", 1))
    assert all(x == rows[0] for x in rows)


def test_opening_values_only_from_selected_provider():
    row = cfbd(1, "A", "B", 20, 10, [line("DraftKings", -3, 50, spread_open=None, total_open=None),
                                     line("Bovada", -3.5, 50.5, spread_open=-1, total_open=48)])
    sel = m.select_market(m.normalize([row])[0]["1"], "spread", 1)
    assert sel["provider"] == "DraftKings" and sel["open"] is None and sel["reason"] == "fallback_missing_consensus"


def test_unknown_providers_sorted_after_priority_list():
    row = cfbd(2, "A", "B", 20, 10, [line("Zeta Book", -2), line("Alpha Book", -2.5)])
    assert m.select_market(m.normalize([row])[0]["2"], "spread", 1)["provider"] == "Alpha Book"


# ---------------------------------------------------------------- ATS / O-U arithmetic and sign convention
def test_spread_sign_convention_texas_tech_kansas():
    by_id, _ = statuses([TTU_KU])
    o = by_id["400869598"]
    assert o["home_spread"] == -27.5 and o["home_cover"] == 8.5 and o["home_ats"] == "W"
    assert o["ou"] == "U"  # 74 < 78.5


def test_formatted_spread_contradiction_is_suspicious():
    row = cfbd(3, "Texas Tech", "Kansas", 55, 19, [line("consensus", 27.5, formatted="Texas Tech -27.5")])
    assert m.select_market(m.normalize([row])[0]["3"], "spread", 1)["status"] == "suspicious"


@pytest.mark.parametrize("margin,spread,expected", [(7, -6.5, "W"), (7, -7, "P"), (7, -7.5, "L"), (-3, 3, "P"), (-3, 0, "L"), (0, 0, "P")])
def test_ats_results_and_pushes(margin, spread, expected):
    assert m.ats_result(margin, spread)[0] == expected


@pytest.mark.parametrize("points,total,expected", [(51, 50.5, "O"), (50, 50, "P"), (49, 50.5, "U")])
def test_over_under_results_and_pushes(points, total, expected):
    assert m.ou_result(points, total) == expected


def test_team_perspective_inversion_pickem_and_neutral_splits():
    rows = [cfbd(10, "A", "B", 24, 20, [line("consensus", -3.5, 40)]),       # A favourite covers; over
            cfbd(11, "B", "A", 21, 21, [line("consensus", 0, 42)]),          # pick'em push; total push
            cfbd(12, "A", "C", 10, 17, [line("consensus", 3, 30)])]          # A underdog home loses by 7 -> L; under? 27<30
    res = results_for(rows)
    res["12"]["neutral_site"] = True
    outcomes, _ = m.build_season(2016, rows, res)
    teams = m.team_statistics(outcomes)
    a, b = teams["A"]["overall"], teams["B"]["overall"]
    assert a["ats"] == {"w": 1, "l": 1, "p": 1} and b["ats"] == {"w": 0, "l": 1, "p": 1}
    assert a["splits"]["favorite"]["ats"]["w"] == 1 and a["splits"]["pickem"]["ats"]["p"] == 1
    assert a["splits"]["underdog"]["ats"]["l"] == 1 and a["splits"]["neutral"]["ats"]["l"] == 1
    assert a["ou"] == {"o": 1, "u": 1, "p": 1}
    assert teams["A"]["recent_results"][0] == {"season": 2016, "ats": "L"}


# ---------------------------------------------------------------- missing, malformed, duplicates, identity
def test_missing_lines_counted_not_invented():
    _, cov = statuses([cfbd(20, "A", "B", 10, 7, [])])
    assert cov["spread_no_line"] == 1 and cov["total_no_line"] == 1


@pytest.mark.parametrize("bad", [{"spread": 75}, {"spread": -3.3}, {"overUnder": 15}, {"overUnder": 120}, {"spread": "abc"}])
def test_suspicious_values_are_excluded(bad):
    ln = line("consensus", -3, 50)
    ln.update(bad)
    games, _ = m.normalize([cfbd(21, "A", "B", 10, 7, [ln])])
    market = "total" if "overUnder" in bad else "spread"
    assert m.select_market(games["21"], market, 1)["status"] == "suspicious"


def test_identical_duplicates_collapse_conflicting_duplicates_reject():
    row = cfbd(22, "A", "B", 10, 7, [line("consensus", -3, 50)])
    _, cov = statuses([row, json.loads(json.dumps(row))])
    assert cov["conflicting_duplicates"] == 0
    other = cfbd(22, "A", "B", 10, 7, [line("consensus", -4, 50)])
    _, cov = statuses([row, other])
    with pytest.raises(ArchiveRejected, match="conflicting"):
        m.validate_season(2016, cov, completed_season=False)


def test_identity_and_score_mismatch_reject_and_swapped_orientation_flips_sign():
    row = cfbd(23, "A", "B", 10, 7, [line("consensus", -3, 50)])
    res = results_for([row])
    swapped = dict(res["23"], home="B", away="A", home_score=7, away_score=10)
    outcomes, _ = m.build_season(2016, [row], {"23": swapped})
    assert outcomes[0]["home_spread"] == 3 and outcomes[0]["home_ats"] == "P"  # lost by 3 as +3 underdog
    with pytest.raises(ArchiveRejected, match="identity"):
        m.build_season(2016, [row], {"23": dict(res["23"], home="Z")})
    with pytest.raises(ArchiveRejected, match="score"):
        m.build_season(2016, [row], {"23": dict(res["23"], home_score=11)})


def test_aliases_reuse_existing_team_identity_map():
    row = cfbd(24, "Miami", "UL Monroe", 30, 10, [line("consensus", -20, 55)])
    res = {"24": {**results_for([row])["24"], "home": "Miami (FL)", "away": "ULM"}}
    outcomes, cov = m.build_season(2016, [row], res)
    assert cov["matched"] == 1 and outcomes[0]["home_ats"] == "P"  # 20-point win vs -20


def test_unmatched_archive_games_are_counted():
    res = results_for([TTU_KU])
    res["999"] = dict(res["400869598"], game_id="999")
    _, cov = m.build_season(2016, [TTU_KU], res)
    assert cov["archive_games"] == 2 and cov["matched"] == 1 and cov["unmatched"] == 1


# ---------------------------------------------------------------- coverage thresholds
def test_coverage_reconciles_and_thresholds_enforced():
    rows = [cfbd(100 + i, "A", "B", 20, 10, [line("consensus", -3, 50)]) for i in range(60)]
    _, cov = statuses(rows)
    m.validate_season(2016, cov)
    rows[0]["lines"] = []
    rows[1]["lines"] = []
    _, cov = statuses(rows)
    with pytest.raises(ArchiveRejected, match="spread coverage"):
        m.validate_season(2016, cov)


def test_disputed_share_above_threshold_stops_for_review():
    rows = [cfbd(200 + i, "A", "B", 20, 10, [line("consensus", -3, 50), line("Bovada", -7, 50)]) for i in range(10)]
    _, cov = statuses(rows)
    with pytest.raises(ArchiveRejected, match="disputed share"):
        m.validate_season(2016, cov)


# ---------------------------------------------------------------- sensitivity
def test_sensitivity_reports_effect_of_disputed_games_without_changing_primary_denominator():
    disputed = cfbd(32, "Texas Tech", "Baylor", 54, 35, [line("consensus", 2.5, 83), line("DraftKings", 7, 83)])
    rows = DOCUMENTED + [disputed]
    outcomes, cov = m.build_season(2016, rows, results_for(rows))
    assert cov["spread_disputed"] == 1
    ttu = m.team_statistics(outcomes)["Texas Tech"]
    assert ttu["overall"]["ats"] == {"w": 3, "l": 2, "p": 0}        # disputed Baylor game excluded from the primary record
    assert ttu["overall"]["spread_excluded"]["disputed"] == 1
    assert ttu["sensitivity_including_disputed"]["ats"] == {"w": 4, "l": 2, "p": 0}   # selected consensus +2.5: won by 19
    summary = m.sensitivity_summary(m.team_statistics(outcomes))
    assert summary["ats_games_including_disputed"] - summary["ats_games_primary"] == 1


# ---------------------------------------------------------------- licensing guard
def test_public_payload_passes_guard_and_hides_small_sample_averages():
    outcomes, cov = m.build_season(2016, DOCUMENTED, results_for(DOCUMENTED))
    receipts = {"seasons": {"2016": {"regular": {"retrieved_at": "2026-11-16T00:00:00+00:00"}}}}
    payload = m.build_public(outcomes, {"2016": cov}, receipts)
    blob = json.dumps(payload)
    for forbidden in ('"spread":', '"total":', '"home_cover"', '"cover_margin"', '"game_id"', '"provider":', '"value"'):
        assert forbidden not in blob
    lou = payload["teams"]["Louisiana Tech"]["overall"]
    assert lou["avg_cover_margin"] is None and lou["avg_cover_margin_games"] == 1  # one game would reveal the line


@pytest.mark.parametrize("leak", [{"spread": -3.5}, {"home_cover": 2.5}, {"game_id": "1"}, {"recent_results": [{"season": 2016, "ats": "W", "spread": -3}]},
                                  {"stat": 0.5}])
def test_licensing_guard_rejects_restricted_fields(leak):
    with pytest.raises(ArchiveRejected):
        m.assert_public_safe({"teams": {"A": leak}})


def test_committed_public_archive_is_license_safe():
    path = Path(m.PUBLIC)
    if not path.exists():
        pytest.skip("public archive not generated yet")
    payload = json.loads(path.read_text())
    m.assert_public_safe(payload)
    assert payload["attribution"] == m.ATTRIBUTION and payload["provider_policy_version"] == m.POLICY_VERSION
    receipts = json.loads(Path(m.RECEIPTS).read_text())
    for season in payload["seasons"]:
        entry = receipts["seasons"][str(season)]
        for st in m.SEASON_TYPES:
            assert len(entry[st]["sha256"]) == 64 and entry[st]["retrieved_at"] and isinstance(entry[st]["rows"], int)
        assert "spread" not in json.dumps(entry).replace("spread_", "")  # counts only, no line values
    for season, cov in payload["coverage"].items():
        if int(season) != payload["current_season"]:
            m.validate_season(int(season), cov)


# ---------------------------------------------------------------- end-to-end run: provenance, reproducibility, fail-safe
def write_archive(tmp, games_by_season):
    path = tmp / "archive.json.gz"
    path.write_bytes(gzip.compress(json.dumps({str(s): g for s, g in games_by_season.items()}).encode()))
    return path


def synthetic_season(season, n=60, base=1000):
    rows, games = [], []
    for i in range(n):
        gid = base + season * 100 + i
        hs, as_ = 20 + (i % 9), 14 + (i % 13)
        rows.append(cfbd(gid, f"T{i % 12}", f"T{(i + 5) % 12}", hs, as_,
                         [line("consensus", -3.5 + (i % 4), 47.5 + (i % 5)), line("Bovada", -3.5 + (i % 4), 47.5 + (i % 5))]))
        games.append(archive_game(gid, season, f"T{i % 12}", f"T{(i + 5) % 12}", hs, as_, f"{season}-09-{1 + i % 28:02d}T18:00:00Z"))
    return rows, games


@pytest.fixture
def world(tmp_path):
    feeds, games = {}, {}
    for season in (2018, 2019):
        rows, g = synthetic_season(season)
        feeds[(season, "regular")], feeds[(season, "postseason")] = rows, []
        games[season] = g
    cur_rows, cur_games = synthetic_season(2026, n=10, base=5000)
    feeds[(2026, "regular")], feeds[(2026, "postseason")] = cur_rows, []
    snap = {"season": 2026, "games": [{"game_id": int(g["game_id"]), "season": 2026, "week": 1, "home": g["home"], "away": g["away"],
                                       "completed": True, "home_score": g["home_score"], "away_score": g["away_score"],
                                       "neutral_site": False, "start_date": "2026-09-05T16:00:00.000Z"} for g in cur_games]}
    (tmp_path / "games.json").write_text(json.dumps(snap))
    (tmp_path / "report.json").write_text(json.dumps({"rankings": [{"team": f"T{i}"} for i in range(12)]}))
    calls = []

    def fetch(season, st, key):
        calls.append((season, st))
        return json.loads(json.dumps(feeds[(season, st)]))
    env = dict(archive=write_archive(tmp_path, games), games_path=tmp_path / "games.json", report_path=tmp_path / "report.json",
               receipts_path=tmp_path / "receipts.json", public_path=tmp_path / "public.json",
               now=datetime(2026, 11, 16, tzinfo=timezone.utc))
    return feeds, fetch, calls, env, tmp_path


def test_backfill_writes_provenance_and_is_reproducible(world):
    feeds, fetch, calls, env, tmp = world
    receipts, payload = m.run([2018, 2019], None, "k", tmp / "cache", fetch=fetch, **env)
    first = (env["receipts_path"].read_bytes(), env["public_path"].read_bytes())
    for s in ("2018", "2019"):
        assert receipts["seasons"][s]["regular"]["rows"] == 60 and len(receipts["seasons"][s]["regular"]["sha256"]) == 64
    assert len(calls) == 4
    # Offline regeneration from the private snapshot reproduces byte-identical outputs without any download.
    m.run([2018, 2019], None, "", tmp / "cache", offline=True, fetch=fetch, **env)
    assert (env["receipts_path"].read_bytes(), env["public_path"].read_bytes()) == first and len(calls) == 4


def test_incremental_current_season_equals_full_rebuild_without_historical_download(world):
    feeds, fetch, calls, env, tmp = world
    m.run([2018, 2019], None, "k", None, fetch=fetch, **env)
    calls.clear()
    m.run([2026], 2026, "k", None, incremental=True, fetch=fetch, **env)
    assert calls == [(2026, "regular"), (2026, "postseason")]
    incremental = json.loads(env["public_path"].read_text())
    full_env = dict(env, receipts_path=tmp / "r2.json", public_path=tmp / "p2.json")
    m.run([2018, 2019, 2026], 2026, "k", None, fetch=fetch, **full_env)
    full = json.loads(full_env["public_path"].read_text())
    assert incremental["teams"] == full["teams"] and incremental["coverage"] == full["coverage"]


def test_future_games_are_never_counted(world):
    feeds, fetch, calls, env, tmp = world
    snap = json.loads(env["games_path"].read_text())
    snap["games"][0]["start_date"] = "2026-12-31T00:00:00.000Z"     # marked completed but kickoff in the future
    snap["games"][1]["completed"] = False
    env["games_path"].write_text(json.dumps(snap))
    res = m.current_results(2026, env["games_path"], env["report_path"], env["now"])
    assert sum(r["completed"] for r in res.values()) == 8


def test_upstream_historical_change_fails_closed_until_accepted(world):
    feeds, fetch, calls, env, tmp = world
    m.run([2018, 2019], None, "k", None, fetch=fetch, **env)
    before = (env["receipts_path"].read_bytes(), env["public_path"].read_bytes())
    feeds[(2018, "regular")][0]["lines"][0]["spread"] = -6.5
    with pytest.raises(ArchiveRejected, match="upstream change"):
        m.run([2018, 2019], None, "k", None, fetch=fetch, **env)
    assert (env["receipts_path"].read_bytes(), env["public_path"].read_bytes()) == before
    m.run([2018, 2019], None, "k", None, accept_upstream=True, fetch=fetch, **env)
    assert env["public_path"].read_bytes() != before[1]


@pytest.mark.parametrize("failure", ["http503", "timeout", "empty", "truncated", "not_list", "score_mismatch"])
def test_failed_refresh_preserves_last_verified_outputs(world, failure):
    feeds, fetch, calls, env, tmp = world
    m.run([2018, 2019], None, "k", None, fetch=fetch, **env)
    before = (env["receipts_path"].read_bytes(), env["public_path"].read_bytes())

    def broken(season, st, key):
        if season == 2019 and st == "regular":
            if failure == "http503":
                raise urllib.error.HTTPError("u", 503, "unavailable", {}, None)
            if failure == "timeout":
                raise TimeoutError("timed out")
            if failure == "empty":
                return []
            if failure == "truncated":
                return feeds[(season, st)][:30]
            if failure == "not_list":
                return {"message": "rate limited"}
            if failure == "score_mismatch":
                rows = json.loads(json.dumps(feeds[(season, st)]))
                rows[0]["homeScore"] += 1
                return rows
        return fetch(season, st, key)
    with pytest.raises((ArchiveRejected, urllib.error.HTTPError, TimeoutError)):
        m.run([2018, 2019], None, "k", None, accept_upstream=True, fetch=broken, **env)
    assert (env["receipts_path"].read_bytes(), env["public_path"].read_bytes()) == before


def test_incremental_refuses_without_verified_archive_or_after_policy_change(world):
    feeds, fetch, calls, env, tmp = world
    with pytest.raises(ArchiveRejected, match="existing verified"):
        m.run([2026], 2026, "k", None, incremental=True, fetch=fetch, **env)
    m.run([2018, 2019], None, "k", None, fetch=fetch, **env)
    pub = json.loads(env["public_path"].read_text())
    pub["provider_policy_version"] = 0
    env["public_path"].write_text(json.dumps(pub))
    with pytest.raises(ArchiveRejected, match="policy"):
        m.run([2026], 2026, "k", None, incremental=True, fetch=fetch, **env)


def test_dispute_diagnostics_identify_consensus_as_sole_outlier():
    diag = m.diagnose_season(2016, DOCUMENTED, results_for(DOCUMENTED))
    assert diag["spread_disputed"] == 2 and diag["spread_consensus_sole_outlier"] == 2
    assert diag["policy_v2_spread_disputed"] == 0 and diag["policy_v2_spread_consensus_replaced"] == 2
    assert diag["spread_consensus_opposite_favourite"] == 2  # WVU: -1 vs +3; ASU: -5 vs +1.5/+1
    assert "value" not in json.dumps(diag)


@pytest.mark.parametrize("home,away,formatted,spread,conflict", [
    ("Texas", "Texas Tech", "Texas Tech -3", 3, False),       # away favourite named by the longer name
    ("Texas", "Texas Tech", "Texas -3", -3, False),
    ("Texas Tech", "Texas", "Texas -7", -7, True),            # home spread negative but away named: conflict
    ("Georgia", "Georgia Tech", "Georgia Tech -2.5", 2.5, False),
    ("Miami (OH)", "Miami", "Miami -10", 10, False)])
def test_formatted_spread_name_matching_handles_shared_prefixes(home, away, formatted, spread, conflict):
    assert m._favored_name_conflict(formatted, spread, home, away) is conflict


def test_selected_sportsbook_replaced_when_it_is_the_sole_outlier():
    row = cfbd(40, "A", "B", 24, 20, [line("DraftKings", -10, 61), line("Bovada", -6, 55), line("ESPN Bet", -6.5, 55.5)])
    games = m.normalize([row])[0]
    spread, total = m.select_market(games["40"], "spread", 1), m.select_market(games["40"], "total", 1)
    assert spread["provider"] == "ESPN Bet" and spread["reason"] == "priority_outlier_replaced" and spread["status"] == "ok"
    assert total["provider"] == "ESPN Bet" and total["reason"] == "priority_outlier_replaced"


def test_current_season_snapshot_names_are_canonicalized_like_the_report(world):
    feeds, fetch, calls, env, tmp = world
    snap = json.loads(env["games_path"].read_text())
    snap["games"][0]["away"] = "UL Monroe"
    env["games_path"].write_text(json.dumps(snap))
    report = json.loads(env["report_path"].read_text())
    report["rankings"].append({"team": "ULM"})
    env["report_path"].write_text(json.dumps(report))
    res = m.current_results(2026, env["games_path"], env["report_path"], env["now"])
    assert res[str(snap["games"][0]["game_id"])]["away"] == "ULM"
