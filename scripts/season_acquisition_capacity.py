"""Reproducible planning scenarios; no source calls or measured latency claims."""
import json
import math


def report(interval=120):
    windows = {'ordinary_saturdays': (12, 12, 1, 15),
               'weekday_windows': (14, 4, 1, 3),
               'rivalry_weekend': (1, 16, 1, 24),
               'championships': (1, 8, 2, 6),
               'postseason': (1, 60, 1, 20)}
    rows = {name: {'windows': n, 'hours_per_window': h, 'status_calls_per_check': c,
                   'publication_waves_per_window': w,
                   'calls': n * (math.ceil(h * 3600 / interval) * c + 2 * w)}
            for name, (n, h, c, w) in windows.items()}
    # 18 weeks: AP/Coaches share rankings, plus eight CFP releases.
    polls = (18 + 8) * (30 + 2)  # one hour at two-minute checks + publication
    stats = 18 * 5  # warm regular-season collector; postseason/cold cache adds cost
    baseline = 180 * 2
    subtotal = sum(x['calls'] for x in rows.values()) + polls + stats + baseline
    return {'kind': 'estimate_not_measurement', 'source_calls_made': 0,
            'interval_seconds': interval, 'windows': rows, 'poll_calls': polls,
            'warm_statistics_calls': stats, 'daily_reconciliation_calls': baseline,
            'subtotal': subtotal, 'with_20_percent_retry_delay_allowance': math.ceil(subtotal * 1.2),
            'peak_month_two_minute_previous_scenario': 1784,
            'limitations': ['Assumed volumes/windows, not observed provider behavior.',
                           'Cold caches and mixed postseason statistics add cost.',
                           'Provider lag and deployment latency are not inferred.',
                           'Monthly limits cannot be pooled across the season.']}


if __name__ == '__main__':
    print(json.dumps({'two_minute': report(), 'five_minute': report(300)}, indent=2))
