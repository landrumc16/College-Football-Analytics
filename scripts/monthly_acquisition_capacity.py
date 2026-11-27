"""Explicit planning allowances, not observations or a guarantee of five-minute publication."""
import calendar
import json
import math

# Active union hours (batch across all games), publication waves, poll windows, stats passes.
MONTHS = {'August': (24, 20, 3, 2), 'September': (80, 80, 4, 5),
          'October': (110, 100, 5, 5), 'November': (115, 115, 8, 5),
          'December': (70, 50, 3, 5), 'January': (30, 15, 2, 3)}


def estimate(minutes):
    rows = {}
    for name, (hours, waves, polls, stats) in MONTHS.items():
        days = calendar.monthrange(2027 if name == 'January' else 2026, list(calendar.month_name).index(name))[1]
        pieces = {'status': math.ceil(hours * 60 / minutes), 'score_publication': waves * 2,
                  'ranking_detection': polls * math.ceil(60 / minutes), 'ranking_publication': polls * 2,
                  'advanced_stats': stats * 7, 'schedule_and_baseline': days * 2,
                  'market': days * 2, 'individual_and_team_boxscores': waves * 2,
                  'cold_cache_and_corrections': 100}
        # PR78 warm regular-season passes use five calls; reserve seven for mixed postseason.
        if name in ('August', 'September', 'October', 'November'):
            pieces['advanced_stats'] = stats * 5
        subtotal = sum(pieces.values())
        rows[name] = {'active_hours_assumed': hours, 'waves_assumed': waves, 'components': pieces,
                      'subtotal': subtotal, 'with_30_percent_contingency': math.ceil(subtotal * 1.3)}
    return rows


if __name__ == '__main__':
    print(json.dumps({'kind': 'planning_estimate_not_measurement', 'source_calls_made': 0,
                      'intervals': {str(m): estimate(m) for m in (2, 3, 5)},
                      'peak_week_assumption': {'hours': 40, 'waves': 40, 'poll_windows': 2,
                                              'two_minute_with_30_percent_contingency': math.ceil((1200 + 80 + 60 + 4 + 5 + 14 + 14 + 80 + 25) * 1.3)},
                      'limitations': ['Future event durations are assumptions, not actual endpoint measurements.',
                                      'New boxscore consumers are reserved allowances, not implemented features.',
                                      'No source availability, billing reset policy or SLO is inferred.']}, indent=2))
