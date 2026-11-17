import unittest
from cfb_analytics.ratings import Team
from cfb_analytics.recency_replay_research import paired_replay, paired_metrics


def g(n, kickoff, home, away, hs, ass):
    return {"game_id": n, "start_date": kickoff, "home": home, "away": away,
            "home_score": hs, "away_score": ass, "completed": True}


class PairedReplayTests(unittest.TestCase):
    def setUp(self):
        self.teams = [Team("A", "X", 2), Team("B", "X", -2)]
        self.games = [
            g(1, "2026-09-01T12:00:00Z", "A", "B", 14, 7),
            g(2, "2026-09-01T13:00:00Z", "B", "A", 7, 28),
            g(3, "2026-09-08T12:00:00Z", "A", "B", 10, 17),
            g(4, "2026-09-15T12:00:00Z", "B", "A", 14, 35),
        ]

    def test_no_same_day_leakage_and_stable_input_order(self):
        rows = paired_replay(self.teams, list(reversed(self.games)))
        self.assertEqual([r["history_games"] for r in rows], [0, 0, 2, 3])
        self.assertEqual(rows, paired_replay(self.teams, self.games))

    def test_challenger_and_incumbent_match_before_fourth_prior_game(self):
        rows = paired_replay(self.teams, self.games)
        for row in rows[:3]:
            self.assertAlmostEqual(row["incumbent_probability"],
                                   row["challenger_probability"])

    def test_metrics_have_paired_games(self):
        result = paired_metrics(paired_replay(self.teams, self.games))
        self.assertEqual(result["games"], 4)
        for key in ("incumbent", "challenger"):
            self.assertTrue(0 <= result[key]["brier"] <= 1)

    def test_duplicate_and_missing_kickoff_rejected(self):
        with self.assertRaises(ValueError):
            paired_replay(self.teams, self.games + [self.games[0]])
        with self.assertRaises(ValueError):
            paired_replay(self.teams, [{**self.games[0], "start_date": None}])


if __name__ == "__main__":
    unittest.main()
