"""Exercise genuine GitHub CAS in an isolated test branch; zero CFBD requests."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from cfb_analytics import quota_client as q


def main():
    q.BRANCH = 'operations/quota-test-' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    ledger = q.GitHubLedger(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'])
    now = datetime.now(timezone.utc)
    info = {'remainingCalls': 10, 'resetAt': f'{now.year + 1}-01-01T00:00:00Z'}
    established = False
    try:
        ledger.read()  # establish the isolated branch before the contention test
        established = True
        def request(i):
            try:
                q.coordinate(ledger, info, f'test-{i}', 2, 'essential', now)
                return True
            except q.QuotaUnavailable:
                return False
        with ThreadPoolExecutor(max_workers=4) as pool:
            outcomes = list(pool.map(request, range(4)))
        state, _ = ledger.read()
        assert sum(outcomes) == 2 and state['remaining'] == q.FLOOR, (outcomes, state)
        result = {'test': 'genuine GitHub compare-and-swap contention', 'source_api_calls': 0,
                  'attempted': 4, 'reserved': sum(outcomes), 'protected_remaining': state['remaining'],
                  'measured_at': datetime.now(timezone.utc).isoformat(), 'production_ledger_changed': False}
        Path('shared-quota-acceptance.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
    finally:
        if established:
            ledger.api('git/refs/heads/' + q.BRANCH, 'DELETE')


if __name__ == '__main__':
    main()
