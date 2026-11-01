"""Compare the Python rating engine against frozen Google Sheets outputs.

Run: python -m cfb_analytics.parity
This reports discrepancies; it does not claim the model has passed parity.
"""
import json
from pathlib import Path
from .ratings import Team, Game, calculate_ratings
from .projections import ScheduledGame, project_season


def load_baseline(folder=None):
    folder = Path(folder) if folder else Path(__file__).resolve().parents[2] / "tests" / "fixtures"
    def read(kind):
        records = []
        for path in sorted(folder.glob("2026-week7-" + kind + "-[0-9][0-9].json")):
            records.extend(json.loads(path.read_text(encoding="utf-8")))
        return records
    return read("teams"), read("games")


def compare():
    teams, games = load_baseline()
    if len(teams) != 138 or len(games) != 510:
        raise RuntimeError(f"Incomplete baseline: {len(teams)} teams, {len(games)} games")
    results = calculate_ratings(
        [Team(t["name"], t["conference"], t["prior"]) for t in teams],
        [Game(g["home"], g["away"], g["home_score"], g["away_score"], g["week"]) for g in games],
    )
    discrepancies = []
    for ref in teams:
        actual = results[ref["name"]]
        for field, value in (("adaptive", actual.adaptive_rating),
                             ("sos", actual.strength_of_schedule)):
            if ref[field] is not None:
                discrepancies.append((abs(ref[field] - value), ref["name"], field,
                                      ref[field], value))
        for index, expected in enumerate(ref["passes"], 1):
            if expected is not None:
                discrepancies.append((abs(expected - actual.passes[index]),
                                      ref["name"], "pass_" + str(index), expected,
                                      actual.passes[index]))
        for field in ("wins", "losses", "quality_wins", "bad_losses"):
            expected = ref[field]
            observed = getattr(actual, field)
            discrepancies.append((abs(expected - observed), ref["name"], field,
                                  expected, observed))
    schedule = []
    for fixture in sorted((Path(__file__).resolve().parents[2] / 'tests' / 'fixtures').glob('2026-week7-schedule-[0-9][0-9].json')):
        schedule.extend(json.loads(fixture.read_text(encoding='utf-8')))
    if len(schedule) != 888:
        raise RuntimeError(f'Incomplete schedule fixture: {len(schedule)} games')
    projected = project_season(
        {t['name']: (t['conference'], results[t['name']].adaptive_rating,
                     results[t['name']].wins, 0) for t in teams},
        [ScheduledGame(g['home'], g['away'], g['completed']) for g in schedule],
    )
    for ref in teams:
        actual = projected[ref['name']].projected_wins
        discrepancies.append((abs(ref['projected_wins'] - actual), ref['name'],
                              'projected_wins', ref['projected_wins'], actual))
    discrepancies.sort(reverse=True)
    return discrepancies


if __name__ == "__main__":
    differences = compare()
    print("Compared", len(differences), "team metrics")
    print("Largest discrepancies (absolute):")
    for delta, team, field, expected, actual in differences[:25]:
        print(f"{team:25s} {field:15s} expected={expected:12.6f} actual={actual:12.6f} delta={delta:.6f}")
    print("Metrics differing by >0.001:", sum(d[0] > 0.001 for d in differences))
