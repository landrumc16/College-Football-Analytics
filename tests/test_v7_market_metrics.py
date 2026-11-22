"""V7 M3 metrics engine: independent hand-computed fixtures, guards and committed-output checks."""
import json
import math
from pathlib import Path

import pytest

from cfb_analytics import v7_market_metrics as mm

ROOT = Path(__file__).resolve().parents[1]


def line(gid, spread, ts, os_, *, total=None, venue="home", opponent="Opp", season=2024, kickoff=None,
         spread_status=None, total_status=None, ats=None, ou=None, week=1, provider="consensus"):
    return {"game_id": gid, "season": season, "week": week, "season_type": "regular",
            "kickoff": kickoff or f"{season}-09-{int(gid) % 28 + 1:02d}T18:00:00.000Z",
            "opponent": opponent, "venue": venue, "team_score": ts, "opponent_score": os_,
            "spread": spread, "spread_provider": provider if spread is not None else None,
            "spread_status": spread_status or ("ok" if spread is not None else "no_line"),
            "total": total, "total_provider": provider if total is not None else None,
            "total_status": total_status or ("ok" if total is not None else "no_line"), "ats": ats, "ou": ou}


# ---------------------------------------------------------------- statistics helpers
def test_wilson_matches_published_values():
    assert mm.wilson(5, 10) == [0.237, 0.763]
    assert mm.wilson(0, 10) == [0.0, 0.278]
    assert mm.wilson(10, 10) == [0.722, 1.0]
    assert mm.wilson(0, 0) is None


@pytest.mark.parametrize("n,label", [(0, "insufficient"), (9, "insufficient"), (10, "limited"),
                                     (29, "limited"), (30, "adequate")])
def test_sample_labels_at_boundaries(n, label):
    assert mm.sample_label(n) == label


def test_rate_excludes_pushes_and_withholds_small_samples():
    small = mm.rate_block(6, 3, 4, "w", "l")
    assert small["decided"] == 9 and small["p"] == 4 and small["rate"] is None and small["ci95"] is None
    assert "fewer than 10" in small["na_reason"]
    block = mm.rate_block(7, 3, 5, "w", "l")
    assert block["rate"] == 0.7 and block["decided"] == 10 and block["sample"] == "limited"
    assert block["ci95"] == mm.wilson(7, 10) and block["ci_excludes_50"] is False
    assert mm.rate_block(30, 5, 0, "w", "l")["ci_excludes_50"] is True


def test_implied_probability_hand_values_and_symmetry():
    assert mm.implied_probability(0) == 0.5
    assert mm.implied_probability(-19.5) == pytest.approx(1 / (1 + 10 ** -1))
    assert mm.implied_probability(7) == pytest.approx(1 / (1 + 10 ** (7 / 19.5)))
    for s in (1.5, 3, 7, 14, 28.5):
        assert mm.implied_probability(-s) + mm.implied_probability(s) == pytest.approx(1)
        assert mm.implied_probability(-s) > 0.5


def test_distribution_bucket_boundaries_and_values():
    values = [-14.5, -14, -7, -3, 0, 3, 7, 14, 14.5]
    d = mm.distribution(values)
    assert d["buckets"] == {"lt_-14": 1, "-14_to_-7": 1, "-7_to_-3": 1, "-3_to_0": 1, "push": 1,
                            "0_to_3": 1, "3_to_7": 1, "7_to_14": 1, "gt_14": 1}
    assert d["n"] == 9 and d["mean"] == 0.0 and d["median"] == 0.0 and d["p25"] == -7.0 and d["p75"] == 7.0
    assert d["sd"] == round(math.sqrt(sum(v * v for v in values) / 8), 1)
    assert mm.distribution([1, 2, 3, 4])["mean"] is None and mm.distribution([1, 2, 3, 4])["na_reason"]


# ---------------------------------------------------------------- per-game classification
def test_classify_wins_losses_pushes_and_roles():
    push = mm.classify(line("1", -7, 31, 24, total=55, ats="P", ou="P"))
    assert push["ats"] == "P" and push["cover"] == 0 and push["role"] == "favorite" and push["ou"] == "P"
    win = mm.classify(line("2", -7, 30, 20, total=44.5))
    assert win["ats"] == "W" and win["cover"] == 3 and win["ou"] == "O" and win["total_margin"] == 5.5
    dog = mm.classify(line("3", 3.5, 21, 24, total=50))
    assert dog["ats"] == "W" and dog["cover"] == 0.5 and dog["role"] == "underdog" and dog["result"] == "L"
    assert dog["ou"] == "U" and dog["total_margin"] == -5
    pick = mm.classify(line("4", 0, 17, 20))
    assert pick["role"] == "pickem" and pick["ats"] == "L" and pick["implied"] == 0.5


def test_classify_unplayed_tied_and_missing_lines():
    void = mm.classify(line("5", -3, None, None, total=48))
    assert void["played"] is False and "ats" not in void and "ou" not in void and "result" not in void
    tie = mm.classify(line("6", -2.5, 20, 20))
    assert tie["result"] == "T" and tie["ats"] == "L"
    none = mm.classify(line("7", None, 28, 14))
    assert "ats" not in none and "role" not in none and "implied" not in none and none["result"] == "W"


def test_classify_rejects_letters_inconsistent_with_scores():
    with pytest.raises(mm.MetricsRejected, match="ATS"):
        mm.classify(line("8", -7, 30, 20, ats="L"))
    with pytest.raises(mm.MetricsRejected, match="O/U"):
        mm.classify(line("9", -7, 30, 20, total=40, ou="U"))


# ---------------------------------------------------------------- team aggregation
def team_fixture():
    rows = [
        line("10", -7, 30, 20, total=44.5),                                   # fav home W cover 3, O
        line("11", -7, 31, 24, total=55),                                     # fav home P, P
        line("12", 3.5, 21, 24, total=50, venue="away"),                      # dog away W 0.5, U
        line("13", 6, 10, 30, total=40, venue="away"),                        # dog away L -14, P
        line("14", 0, 17, 20, total=37, venue="neutral"),                     # pick neutral L -3, P
        line("15", -10, 13, 21, total=48, spread_status="disputed"),          # spread disputed (sensitivity: L); total U
        line("16", None, 42, 7),                                              # no line
        line("17", -3, 24, 10, total=900, total_status="suspicious"),         # spread ok W 11; total suspicious
        line("18", -4, None, None, total=51),                                 # line but no result (void/unplayed)
    ]
    return [mm.classify(r) for r in rows]


def test_team_block_counts_splits_exclusions_and_sensitivity():
    b = mm.team_block(team_fixture())
    assert b["games"] == 9
    assert {k: b["ats"][k] for k in ("w", "l", "p")} == {"w": 3, "l": 2, "p": 1}
    assert {k: b["ou"][k] for k in ("o", "u", "p")} == {"o": 1, "u": 2, "p": 3}
    assert b["ats_excluded"] == {"no_line": 1, "disputed": 1, "suspicious": 0, "no_result": 1}
    assert b["ou_excluded"] == {"no_line": 1, "disputed": 0, "suspicious": 1, "no_result": 1}
    sens = b["ats_including_disputed"]
    assert (sens["w"], sens["l"], sens["p"]) == (3, 3, 1)
    venue, role = b["splits"]["venue"], b["splits"]["role"]
    assert (venue["home"]["ats"]["w"], venue["home"]["ats"]["p"]) == (2, 1)
    assert (venue["away"]["ats"]["w"], venue["away"]["ats"]["l"]) == (1, 1)
    assert venue["neutral"]["ats"]["l"] == 1 and venue["neutral"]["ou"]["p"] == 1
    assert (role["favorite"]["ats"]["w"], role["favorite"]["ats"]["p"]) == (2, 1)
    assert (role["underdog"]["ats"]["w"], role["underdog"]["ats"]["l"]) == (1, 1)
    assert role["pickem"]["ats"]["l"] == 1
    # cover margins: 3, 0, 0.5, -14, -3, 11 -> mean -0.42, median 0.25 (rounds half-even to 0.2)
    cm = b["cover_margin"]
    assert (cm["n"], cm["mean"], cm["median"]) == (6, -0.4, 0.2)
    assert cm["buckets"] == {"lt_-14": 0, "-14_to_-7": 1, "-7_to_-3": 0, "-3_to_0": 1, "push": 1,
                             "0_to_3": 2, "3_to_7": 0, "7_to_14": 1, "gt_14": 0}
    # total margins: 5.5, 0, -5, 0, 0, -14 (game 15's total is not disputed)
    assert b["total_margin"]["n"] == 6 and b["total_margin"]["mean"] == round(-13.5 / 6, 1)
    assert b["ats"]["rate"] is None and b["ats"]["sample"] == "insufficient"


def test_market_expectation_hand_sum_and_small_sample_na():
    rows = [mm.classify(line(str(100 + i), -7 if i % 2 else 3, 28 if i % 3 else 10, 21)) for i in range(12)]
    b = mm.team_block(rows)["market_expectation"]
    expected = sum(mm.implied_probability(-7 if i % 2 else 3) for i in range(12))
    wins = sum(1 for i in range(12) if i % 3)
    assert b["games"] == 12 and b["actual_wins"] == wins
    assert b["market_expected_wins"] == round(expected, 1) and b["wins_vs_market"] == round(wins - expected, 1)
    small = mm.team_block(team_fixture())["market_expectation"]
    assert small["market_expected_wins"] is None and small["na_reason"]


def test_ties_are_excluded_from_market_expectation():
    rows = [mm.classify(line(str(200 + i), -3, 24, 20)) for i in range(10)] + [mm.classify(line("299", -3, 20, 20))]
    b = mm.team_block(rows)["market_expectation"]
    assert b["games"] == 10 and b["tied_finals_excluded"] == 1


def test_last_n_is_most_recent_first():
    rows = [mm.classify(line(str(300 + i), -3, 30 if i < 15 else 0, 20, kickoff=f"2024-09-{i + 1:02d}T18:00:00Z"))
            for i in range(25)]
    last = mm.team_block(rows)["last_n"]
    assert last["5"]["ats"] == {"w": 0, "l": 5, "p": 0}
    assert last["10"]["ats"] == {"w": 0, "l": 10, "p": 0}
    assert last["20"]["ats"] == {"w": 10, "l": 10, "p": 0}


# ---------------------------------------------------------------- calibration
def test_calibration_counts_each_game_once_from_home_side():
    lines = {"Alpha": [line("1", -7, 30, 20, venue="home", opponent="Beta"),
                       line("2", 3, 10, 20, venue="neutral", opponent="Beta")],
             "Beta": [line("1", 7, 20, 30, venue="away", opponent="Alpha"),
                      line("2", -3, 20, 10, venue="neutral", opponent="Alpha"),
                      line("3", -10, 20, 20, venue="home", opponent="Gamma"),                   # tie: excluded
                      line("4", -10, 30, 3, venue="home", opponent="Delta", spread_status="disputed")]}
    c = mm.calibration(lines)
    assert c["games"] == 2
    p1, p2 = mm.implied_probability(-7), mm.implied_probability(3)            # game 2 from Alpha (alphabetical)
    assert c["brier"] == round(((p1 - 1) ** 2 + (p2 - 0) ** 2) / 2, 4)
    assert sum(b["games"] for b in c["bins"]) == 2


# ---------------------------------------------------------------- authentic forecasts and model-vs-market
def forecast(**over):
    base = {"home": "Alpha", "away": "Beta", "home_win_probability": 0.7, "home_margin": 9.0, "model_id": "m1",
            "source": "generated_before_kickoff", "forecast_recorded_at": "2026-11-05T17:35:11+00:00",
            "scheduled_kickoff_at": "2026-11-07T17:45:00.000Z"}
    return {**base, **over}


@pytest.mark.parametrize("over,reason", [
    ({"source": "previously_published_forecast"}, "not_generated_before_kickoff"),
    ({"source": "retrospective_replay"}, "not_generated_before_kickoff"),
    ({"model_id": None}, "no_model_id"),
    ({"forecast_recorded_at": None}, "missing_timestamp"),
    ({"forecast_recorded_at": "2026-11-07T17:45:00+00:00"}, "recorded_at_or_after_kickoff"),
    ({"forecast_recorded_at": "2026-11-08T00:00:00+00:00"}, "recorded_at_or_after_kickoff"),
    ({"home_win_probability": True}, "invalid_probability"),
    ({"home_win_probability": 1.2}, "invalid_probability"),
    ({"home_win_probability": float("nan")}, "invalid_probability"),
    ({"home_margin": None}, "invalid_margin"),
])
def test_authentic_forecast_rejections(over, reason):
    assert mm.authentic_forecast(forecast(**over)) == (False, reason)


def test_authentic_forecast_rechecks_rescheduled_kickoff():
    assert mm.authentic_forecast(forecast()) == (True, None)
    assert mm.authentic_forecast(forecast(), "2026-11-05T12:00:00Z") == (False, "recorded_at_or_after_kickoff")


def comparison_inputs():
    lines = {"Alpha": [line("900", -3, 24, 20, opponent="Beta", season=2026, kickoff="2026-11-07T17:45:00.000Z"),
                       line("901", -10, 17, 14, opponent="Gamma", season=2026, kickoff="2026-11-07T20:00:00.000Z",
                            spread_status="disputed"),
                       line("903", 4, 20, 27, opponent="Delta", venue="away", season=2026, provider="DraftKings",
                            kickoff="2026-11-08T01:00:00.000Z")],
             "Beta": [line("900", 3, 20, 24, opponent="Alpha", venue="away", season=2026,
                           kickoff="2026-11-07T17:45:00.000Z")]}
    ledger = {"900": forecast(),
              "901": forecast(away="Gamma"),
              "902": forecast(home="FCS One", away="FCS Two"),
              "903": forecast(home="Delta", away="Alpha", home_win_probability=0.4, home_margin=-2.0,
                              scheduled_kickoff_at="2026-11-08T01:00:00.000Z"),
              "904": forecast(away="Beta", source="previously_published_forecast"),
              "905": forecast(),                                   # Alpha game not in archive
              "906": forecast(away="Zeta")}
    verified = {"900": {"home_win_probability": 0.7, "prediction_time": "2026-11-05T17:35:11+00:00"}}
    return lines, ledger, verified


def test_comparison_rows_hand_values_inversion_and_exclusions():
    lines, ledger, verified = comparison_inputs()
    rows, excluded = mm.comparison_rows(ledger, lines, verified)
    assert excluded == {"game_not_in_archive": 2, "non_fbs_matchup": 1, "not_generated_before_kickoff": 1,
                        "spread_disputed": 1}
    by = {r["game_id"]: r for r in rows}
    assert set(by) == {"900", "903"}
    r = by["900"]
    market = 1 / (1 + 10 ** (-3 / 19.5))
    assert r["market_home_win_probability"] == round(market, 4)
    assert r["probability_difference_points"] == round(100 * (0.7 - market), 1)
    assert r["margin_difference_points"] == 6.0 and r["favorite_agreement"] == "agree"
    assert r["publication_evidence"] == "independently_verified" and r["forecast_kind"] == "authentic_pregame"
    assert r["hours_before_kickoff"] == 48.2 and r["spread_provider"] == "consensus"
    # Delta (non-FBS home) found through Alpha's file and inverted: Alpha +4 away -> Delta home spread -4.
    d = by["903"]
    assert d["home_spread"] == -4 and d["home_score"] == 27 and d["away_score"] == 20
    assert d["margin_difference_points"] == -6.0 and d["favorite_agreement"] == "disagree"
    assert d["publication_evidence"] == "ledger_recorded_before_kickoff" and d["spread_provider"] == "DraftKings"


def test_comparison_rejects_conflicting_verified_record_and_team_mismatch():
    lines, ledger, verified = comparison_inputs()
    with pytest.raises(mm.MetricsRejected, match="verified"):
        mm.comparison_rows(ledger, lines, {"900": {"home_win_probability": 0.71,
                                                   "prediction_time": "2026-11-05T17:35:11+00:00"}})
    lines["Alpha"][0]["opponent"] = "Other"
    lines["Beta"] = []
    _, excluded = mm.comparison_rows({"900": ledger["900"]}, lines, verified)
    assert excluded == {"team_mismatch": 1}


def test_comparison_summary_separates_verified_subset_and_has_no_model_total():
    lines, ledger, verified = comparison_inputs()
    rows, excluded = mm.comparison_rows(ledger, lines, verified)
    s = mm.comparison_summary(rows, excluded)
    assert s["all_authentic"]["games"] == 2 and s["independently_verified_subset"]["games"] == 1
    assert s["all_authentic"]["favorite_agreement"] == {"agree": 1, "disagree": 1, "market_pickem": 0, "model_pickem": 0}
    assert s["model_total"]["status"] == "not_available"
    assert s["retrospective_replays"]["used"] is False
    assert mm.comparison_summary([], {})["all_authentic"]["games"] == 0


# ---------------------------------------------------------------- guards
def test_metrics_guard_rejects_lines_providers_and_model_totals():
    for bad in ({"spread": -3}, {"x": [{"game_id": "1"}]}, {"spread_provider": "x"},
                {"model_total_points": 51.5}, {"model_total": {"status": "available"}}):
        with pytest.raises(mm.MetricsRejected):
            mm.assert_metrics_safe(bad)
    mm.assert_metrics_safe({"model_total": mm.MODEL_TOTAL, "teams": {"A": {"ats": {"w": 1}}}})


def test_comparison_guard():
    lines, ledger, verified = comparison_inputs()
    _, files = mm.build(lines, ledger, verified, "2026-11-16T00:00:00+00:00")
    good = files["alpha"]
    mm.assert_comparison_safe(good)
    def broken(fn):
        p = json.loads(json.dumps(good)); fn(p); return p
    for mutate in (lambda p: p["games"][0].update(forecast_kind="retrospective_replay"),
                   lambda p: p["games"][0].update(spread_provider=None),
                   lambda p: p["games"][0].update(model_total=50),
                   lambda p: p["games"][0].update(forecast_recorded_at="2026-11-09T00:00:00+00:00"),
                   lambda p: p["games"].append(p["games"][0]),
                   lambda p: p.update(download_url="x"),
                   lambda p: p.update(model_total={"status": "available"})):
        with pytest.raises(mm.MetricsRejected):
            mm.assert_comparison_safe(broken(mutate))


def test_cross_check_detects_disagreement_with_archive():
    lines = {"Alpha": [line("1", -7, 30, 20)]}
    metrics, _ = mm.build(lines, {}, {}, "t")
    ours = metrics["teams"]["Alpha"]["overall"]
    blank = {"ats": {"w": 0, "l": 0, "p": 0}, "ou": {"o": 0, "u": 0, "p": 0}}
    history = {"teams": {"Alpha": {"overall": {"ats": {"w": 1, "l": 0, "p": 0}, "ou": {"o": 0, "u": 0, "p": 0},
                                               "splits": {**{v: blank for v in mm.VENUES}, **{r: blank for r in mm.ROLES},
                                                          "home": {"ats": {"w": 1, "l": 0, "p": 0}, "ou": blank["ou"]},
                                                          "favorite": {"ats": {"w": 1, "l": 0, "p": 0}, "ou": blank["ou"]}}}}}}
    assert mm.cross_check(metrics, history) == []
    history["teams"]["Alpha"]["overall"]["ats"]["w"] = 2
    assert mm.cross_check(metrics, history) and ours["ats"]["w"] == 1


def test_write_is_atomic_and_check_detects_changes(tmp_path):
    lines, ledger, verified = comparison_inputs()
    metrics, files = mm.build(lines, ledger, verified, "t")
    public, cdir = tmp_path / "m.json", tmp_path / "cmp"
    mm.write(metrics, files, public, cdir)
    assert mm.check(metrics, files, public, cdir) == []
    (cdir / "alpha.json").write_text("{}")
    assert mm.check(metrics, files, public, cdir) == [str(cdir / "alpha.json")]
    mm.write(metrics, files, public, cdir)
    assert sorted(f.name for f in tmp_path.iterdir()) == ["cmp", "m.json"]


# ---------------------------------------------------------------- committed real outputs
def test_committed_metrics_reproduce_and_match_archive(monkeypatch):
    monkeypatch.chdir(ROOT)
    metrics, files = mm.generate()                     # raises if any team disagrees with the M2 archive
    assert mm.check(metrics, files) == []
    assert len(metrics["teams"]) == 138


def test_committed_metrics_content(monkeypatch):
    monkeypatch.chdir(ROOT)
    m = json.loads(mm.PUBLIC.read_text())
    # Season-to-date records change whenever a refresh adds a final game, so they are recomputed below from the
    # published lines (test_committed_ats_and_totals_records_recomputed_from_lines). Completed seasons cannot change:
    # Texas Tech's 2016-2025 record is pinned there.
    s = m["model_vs_market"]
    assert s["independently_verified_subset"]["games"] == 65
    assert s["model_total"] == mm.MODEL_TOTAL and s["retrospective_replays"]["used"] is False
    cal = m["implied_probability_calibration"]
    assert cal["games"] > 9000 and cal["brier"] < 0.17
    for b in cal["bins"]:
        if b["games"] >= 300:
            assert abs(b["mean_implied"] - b["observed_win_rate"]) < 0.05
    mm.assert_metrics_safe(m)


def test_committed_comparison_files_are_authentic_and_licensed(monkeypatch):
    monkeypatch.chdir(ROOT)
    ledger = json.loads(mm.LEDGER.read_text())
    seen = set()
    for f in mm.COMPARISON_DIR.glob("*.json"):
        payload = json.loads(f.read_text())
        mm.assert_comparison_safe(payload)
        for g in payload["games"]:
            entry = ledger[g["game_id"]]
            assert entry["source"] == "generated_before_kickoff"
            assert g["model_home_win_probability"] == round(entry["home_win_probability"], 4)
            seen.add(g["game_id"])
    verified = {r["game_id"] for r in json.loads(mm.VERIFIED.read_text())}
    assert verified <= seen


def _records(games):
    """Plain ATS (team margin + spread) and over/under (combined points - total) records from scores and lines."""
    ats, ou = {"w": 0, "l": 0, "p": 0}, {"o": 0, "u": 0, "p": 0}
    for g in games:
        if g["team_score"] is None:
            continue
        if g["spread_status"] == "ok":
            cover = g["team_score"] - g["opponent_score"] + g["spread"]
            ats["w" if cover > 0 else "l" if cover < 0 else "p"] += 1
        if g["total_status"] == "ok":
            diff = g["team_score"] + g["opponent_score"] - g["total"]
            ou["o" if diff > 0 else "u" if diff < 0 else "p"] += 1
    return ats, ou


def test_committed_ats_and_totals_records_recomputed_from_lines(monkeypatch):
    """Every team's published ATS and over/under records equal plain recomputation from its published lines."""
    monkeypatch.chdir(ROOT)
    m = json.loads(mm.PUBLIC.read_text())
    checked = 0
    for f in sorted(mm.LINES_DIR.glob("*.json")):
        payload = json.loads(f.read_text())
        ats, ou = _records(payload["games"])
        t = m["teams"][payload["team"]]["overall"]
        assert {k: t["ats"][k] for k in ats} == ats, payload["team"]
        assert {k: t["ou"][k] for k in ou} == ou, payload["team"]
        checked += 1
    assert checked >= 130
    # Completed seasons are history and must not move: Texas Tech 2016-2025 (verified before the 2026 refreshes).
    tt = json.loads((mm.LINES_DIR / "texas-tech.json").read_text())["games"]
    history = [g for g in tt if g["season"] <= 2025]
    assert _records(history) == ({"w": 68, "l": 52, "p": 5}, {"o": 62, "u": 60, "p": 1})
    assert len(history) == 125


def test_committed_values_recomputed_independently_with_plain_code(monkeypatch):
    """Separate plain arithmetic over the public inputs; shares no helper with the engine."""
    monkeypatch.chdir(ROOT)
    m = json.loads(mm.PUBLIC.read_text())
    for f in sorted(mm.LINES_DIR.glob("*.json")):
        payload = json.loads(f.read_text())
        covers, implied, wins = [], 0.0, 0
        for g in payload["games"]:
            if g["spread_status"] == "ok" and g["team_score"] is not None:
                covers.append(g["team_score"] - g["opponent_score"] + g["spread"])
                if g["team_score"] != g["opponent_score"]:
                    implied += 1 / (1 + 10 ** (g["spread"] / 19.5))
                    wins += g["team_score"] > g["opponent_score"]
        t = m["teams"][payload["team"]]["overall"]
        if len(covers) >= 5:
            assert t["cover_margin"]["mean"] == round(sum(covers) / len(covers), 1), payload["team"]
        assert t["cover_margin"]["n"] == len(covers)
        if t["market_expectation"]["market_expected_wins"] is not None:
            assert t["market_expectation"]["market_expected_wins"] == round(implied, 1)
            assert t["market_expectation"]["actual_wins"] == wins
    ledger = json.loads(mm.LEDGER.read_text())
    checked = 0
    for f in mm.COMPARISON_DIR.glob("*.json"):
        for g in json.loads(f.read_text())["games"]:
            e = ledger[g["game_id"]]
            market = 1 / (1 + 10 ** (g["home_spread"] / 19.5))
            assert g["probability_difference_points"] == round(100 * (e["home_win_probability"] - market), 1)
            assert g["margin_difference_points"] == round(e["home_margin"] + g["home_spread"], 1)
            checked += 1
    assert checked >= 2 * 65
