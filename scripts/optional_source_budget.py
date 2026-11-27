"""Reserve essential result capacity before optional market retrieval; /info only."""
import json
import math
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def allowed(info, now):
    remaining = info.get('remainingCalls')
    if type(remaining) is not int or remaining < 0:
        return False
    reset = datetime.fromisoformat(info['resetAt'].replace('Z', '+00:00'))
    days = max(1, math.ceil((reset - now).total_seconds() / 86400))
    # Existing daily allowance + immutable eight-call floor + two /lines calls.
    return remaining >= 6 * days + 8 + 2


def main():
    permit = False
    try:
        req = Request('https://api.collegefootballdata.com/info', headers={
            'Authorization': 'Bearer ' + os.environ['CFBD_API_KEY'], 'Accept': 'application/json'})
        with urlopen(req, timeout=15) as response:
            permit = allowed(json.load(response), datetime.now(timezone.utc))
    except Exception:
        print('::warning::Optional market acquisition deferred: quota headroom unverified')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('allowed=' + str(permit).lower() + '\n')
    if not permit:
        print('Keeping last verified market archive; essential scores continue')


if __name__ == '__main__':
    main()
