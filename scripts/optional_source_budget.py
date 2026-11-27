"""Reserve essential result capacity before optional market retrieval; /info only."""
import argparse
import json
import math
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def allowed(info, now, priority="supplemental", cost=2):
    if priority not in ('core', 'supplemental') or type(cost) is not int or cost < 1:
        return False
    remaining = info.get('remainingCalls')
    if type(remaining) is not int or remaining < 0:
        return False
    reset = datetime.fromisoformat(info['resetAt'].replace('Z', '+00:00'))
    days = max(1, math.ceil((reset - now).total_seconds() / 86400))
    # Essential daily allowance and floor; supplemental retrieval also reserves a core refresh.
    return remaining >= 6 * days + 8 + cost + (7 if priority == 'supplemental' else 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--priority', choices=['core', 'supplemental'], default='supplemental')
    parser.add_argument('--cost', type=int, default=2)
    args = parser.parse_args()
    permit = False
    try:
        req = Request('https://api.collegefootballdata.com/info', headers={
            'Authorization': 'Bearer ' + os.environ['CFBD_API_KEY'], 'Accept': 'application/json'})
        with urlopen(req, timeout=15) as response:
            permit = allowed(json.load(response), datetime.now(timezone.utc), args.priority, args.cost)
    except Exception:
        print('::warning::Optional market acquisition deferred: quota headroom unverified')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('allowed=' + str(permit).lower() + '\n')
    if not permit:
        print(f'Keeping last verified {args.priority} data; essential results and rankings retain priority')


if __name__ == '__main__':
    main()
