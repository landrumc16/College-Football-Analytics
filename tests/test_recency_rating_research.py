"""Weighted ratings remain research-only and preserve baseline at unit weights."""
import unittest
from cfb_analytics.ratings import Team, Game, calculate_ratings
from scripts.recency_rating_research import calculate_weighted_ratings


class WeightedRatingsResearchTests(unittest.TestCase):
    def setUp(self):
        self.teams = [Team("A", "X", 3.0), Team("B", "X", -2.0),
                      Team("C", "Y", 1.0)]
        self.games = [
            Game("A", "B", 14, 7, 1), Game("C", "A", 10, 17, 2),
            Game("B", "C", 28, 14, 3), Game("A", "C", 35, 7, 4),
            Game("B", "A", 17, 14, 5), Game("C", "B", 21, 7, 6),
            Game("A", "B", 31, 14, 7),
        ]

    def test_unit_weights_reproduce_incumbent(self):
        incumbent = calculate_ratings(self.teams, self.games)
        candidate = calculate_weighted_ratings(self.teams, self.games,
                                               early=1, middle=1, recent=1)
        for team in self.teams:
            self.assertAlmostEqual(candidate[team.name],
                                   incumbent[team.name].adaptive_rating, places=10)

    def test_nonunit_weights_change_at_least_one_rating(self):
        incumbent = calculate_ratings(self.teams, self.games)
        candidate = calculate_weighted_ratings(self.teams, self.games)
        self.assertTrue(any(abs(candidate[t.name] - incumbent[t.name].adaptive_rating) > 1e-6
                            for t in self.teams))

    def test_invalid_game_rejected(self):
        with self.assertRaises(ValueError):
            calculate_weighted_ratings(self.teams, [Game("A", "A", 7, 3)])


if __name__ == "__main__":
    unittest.main()
