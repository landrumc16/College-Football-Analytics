import unittest
from dataclasses import replace
from cfb_analytics.lineup_advisory_research import LineupChange, lineup_advisory


class LineupAdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.change = LineupChange(
            team="Example", position="quarterback", change="replacement",
            effective_at="2026-11-01T12:00:00Z",
            verified_at="2026-11-01T13:00:00Z",
            source_url="https://example.org/verified",
            games_with_new_lineup=1,
        )
        self.as_of = "2026-11-10T00:00:00Z"

    def test_verified_change_shows_uncertainty_not_score_penalty(self):
        result = lineup_advisory(self.change, as_of=self.as_of)
        self.assertEqual(result.games_observed, 1)
        self.assertIn("may be less reliable", result.message)
        self.assertFalse(hasattr(result, "point_adjustment"))

    def test_three_games_clears_provisional_advisory(self):
        self.assertIsNone(lineup_advisory(replace(self.change, games_with_new_lineup=3),
                                          as_of=self.as_of))

    def test_future_or_unconfirmed_changes_are_not_published(self):
        self.assertIsNone(lineup_advisory(replace(self.change,
            verified_at="2026-11-11T00:00:00Z"), as_of=self.as_of))
        self.assertIsNone(lineup_advisory(replace(self.change,
            current_lineup_confirmed=False), as_of=self.as_of))

    def test_invalid_source_and_missing_timezone(self):
        self.assertIsNone(lineup_advisory(replace(self.change,
            source_url="unverified"), as_of=self.as_of))
        with self.assertRaises(ValueError):
            lineup_advisory(self.change, as_of="2026-11-10")


if __name__ == "__main__":
    unittest.main()
