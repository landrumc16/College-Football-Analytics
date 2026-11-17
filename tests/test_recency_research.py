"""Research-only recency-weight invariants."""
import unittest
from types import SimpleNamespace
from cfb_analytics.recency_research import rolling_tier_weights, team_game_weights


class RecencyResearchTests(unittest.TestCase):
    def test_ten_games_latest_three_equal(self):
        w = rolling_tier_weights(10)
        self.assertEqual(len(w), 10)
        self.assertAlmostEqual(sum(w), 1.0)
        self.assertEqual(w[7], w[8])
        self.assertEqual(w[8], w[9])
        self.assertLess(w[0], w[4])
        self.assertLess(w[4], w[7])

    def test_short_season_and_empty(self):
        self.assertEqual(rolling_tier_weights(0), ())
        self.assertEqual(rolling_tier_weights(2), (0.5, 0.5))
        self.assertEqual(len(set(rolling_tier_weights(3))), 1)

    def test_rolls_with_bye_week(self):
        games = [
            SimpleNamespace(home="A", away="B"),
            SimpleNamespace(home="C", away="D"),
            SimpleNamespace(home="A", away="C"),
            SimpleNamespace(home="D", away="A"),
            SimpleNamespace(home="A", away="B"),
        ]
        w = team_game_weights(games, "A")
        self.assertEqual(set(w), {0, 2, 3, 4})
        self.assertEqual(w[2], w[3])
        self.assertEqual(w[3], w[4])

    def test_rejects_invalid_parameters(self):
        for n in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                rolling_tier_weights(n)
        for v in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                rolling_tier_weights(10, recent=v)


if __name__ == "__main__":
    unittest.main()
