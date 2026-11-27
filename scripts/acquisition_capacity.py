"""Explicit scenario estimates, not production latency or source-availability evidence."""
import json
from pathlib import Path

SCENARIOS = {
    'ordinary_saturday': {'active_hours': 12, 'status_calls_per_check': 1, 'publication_waves': 15},
    'rivalry_weekend': {'active_hours': 16, 'status_calls_per_check': 1, 'publication_waves': 24},
    'conference_championships': {'active_hours': 8, 'status_calls_per_check': 2, 'publication_waves': 6},
    'postseason_month': {'active_hours': 60, 'status_calls_per_check': 1, 'publication_waves': 20},
}


def estimate(active_hours, status_calls_per_check, publication_waves, interval_seconds):
    import math
    checks = math.ceil(active_hours * 3600 / interval_seconds) * status_calls_per_check
    return {'status_checks': checks, 'essential_publication_calls': publication_waves * 2,
            'total_calls': checks + publication_waves * 2}


def report():
    scenarios = {name: {'assumptions': spec, 'two_minute_checks': estimate(**spec, interval_seconds=120),
                         'five_minute_checks': estimate(**spec, interval_seconds=300)}
                 for name, spec in SCENARIOS.items()}
    # Four ordinary Saturdays, two 30-minute poll windows/Sunday at two minutes,
    # two poll-publication workflows/Sunday, one seven-call core refresh/week,
    # and a two-call daily essential reconciliation. Explicit planning assumptions.
    other = 4 * (30 + 4 + 7) + 30 * 2
    return {'kind': 'scenario_estimate_not_measurement', 'source_calls_made': 0,
            'free_monthly_limit': 1000, 'scenarios': scenarios,
            'ordinary_four_week_month': {
                'other_assumed_calls': other,
                'two_minute_total': 4 * scenarios['ordinary_saturday']['two_minute_checks']['total_calls'] + other,
                'five_minute_total': 4 * scenarios['ordinary_saturday']['five_minute_checks']['total_calls'] + other},
            'limitations': ['These are assumed windows/waves, not observed event counts.',
                           'Provider lag, failed requests, schedule changes and retry costs add consumption.',
                           'No time-to-publish distribution or 95% success rate is inferred.',
                           'Even five-minute detection can exceed five-minute end-to-end publication.']}


if __name__ == '__main__':
    result = report()
    out = Path('docs/evidence/acquisition-capacity-2026-11-27.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
