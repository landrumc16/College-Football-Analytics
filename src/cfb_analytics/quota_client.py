"""One optimistic-CAS quota ledger for current-checkout CFBD acquisition.

Reserve before every metered attempt, including retries. No raw source data or
credentials enter the ledger. A failed reservation never reaches the source.
"""
import base64
import copy
import json
import os
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen as network_open

BRANCH = 'operations/quota-ledger'
PATH = 'operations/cfbd-quota.json'
FLOOR = 8


class QuotaUnavailable(RuntimeError):
    pass


def priority(url, season):
    parsed = urlsplit(url)
    params = parse_qs(parsed.query)
    year = params.get('year', params.get('season', [str(season)]))[0]
    if year != str(season):
        return 'supplemental'
    if parsed.path in ('/games', '/rankings', '/scoreboard'):
        return 'essential'
    return 'supplemental' if parsed.path.startswith(('/lines', '/recruiting')) else 'core'


def reserve(state, info, run_id, limit, level, now):
    remaining = info.get('remainingCalls')
    reset = info.get('resetAt')
    if type(remaining) is not int or remaining < 0 or not reset:
        raise QuotaUnavailable('Provider quota is unknown; acquisition withheld')
    reset_time = datetime.fromisoformat(reset.replace('Z', '+00:00'))
    if reset_time.tzinfo is None or reset_time <= now:
        raise QuotaUnavailable('Provider quota reset is not current')
    reset = reset_time.astimezone(timezone.utc).isoformat()
    if level not in ('publication', 'essential', 'core', 'supplemental') or not 0 < limit <= 400:
        raise QuotaUnavailable('Invalid acquisition policy')
    s = copy.deepcopy(state) if state and state.get('reset_at') == reset else {
        'schema_version': 1, 'reset_at': reset, 'remaining': remaining, 'runs': {}}
    # Never reclaim a reservation from an in-flight or crashed process. A fresh
    # provider reading can lower capacity but cannot erase existing reservations.
    s['remaining'] = min(s['remaining'], remaining)
    used = s['runs'].get(run_id, {}).get('attempts', 0)
    # The floor exists for score publication: detection checks stop at it, publication may spend it to zero.
    # (Before 2026-11-28 publication was also held at the floor, so the last FLOOR calls could never be spent.)
    protected = {'publication': 0, 'essential': FLOOR}.get(level, FLOOR + 12 + (7 if level == 'supplemental' else 0))
    if used >= limit or s['remaining'] <= protected:
        raise QuotaUnavailable(f'{level} acquisition withheld: remaining={s["remaining"]}, protected={protected}, attempts={used}/{limit}')
    s['remaining'] -= 1
    s['runs'][run_id] = {'attempts': used + 1, 'limit': limit}
    s['updated_at'] = now.isoformat()
    return s


class GitHubLedger:
    def __init__(self, repo, token):
        self.repo, self.token = repo, token

    def api(self, path, method='GET', body=None):
        req = Request('https://api.github.com/repos/' + self.repo + '/' + path,
                      data=json.dumps(body).encode() if body is not None else None, method=method,
                      headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
                               'Content-Type': 'application/json'})
        with network_open(req, timeout=20) as response:
            return None if response.status == 204 else json.load(response)

    def read(self):
        try:
            row = self.api('contents/' + PATH + '?ref=' + BRANCH)
            return json.loads(base64.b64decode(row['content'])), row['sha']
        except HTTPError as error:
            if error.code != 404:
                raise
            # Initialize only a missing ledger branch, preserving existing refs.
            head = self.api('git/ref/heads/main')['object']['sha']
            try:
                self.api('git/refs', 'POST', {'ref': 'refs/heads/' + BRANCH, 'sha': head})
            except HTTPError as exists:
                if exists.code != 422:
                    raise
            return None, None

    def write(self, state, sha):
        body = {'message': 'Reserve CFBD acquisition attempt', 'branch': BRANCH,
                'content': base64.b64encode((json.dumps(state, sort_keys=True) + '\n').encode()).decode()}
        if sha:
            body['sha'] = sha
        try:
            self.api('contents/' + PATH, 'PUT', body)
            return True
        except HTTPError as error:
            if error.code in (409, 422):
                return False
            raise


def coordinate(ledger, info, run_id, limit, level, now, attempts=8):
    for attempt in range(attempts):
        state, sha = ledger.read()
        updated = reserve(state, info, run_id, limit, level, now)
        if ledger.write(updated, sha):
            return updated
        time.sleep(min(0.05 * (attempt + 1), 0.4))
    raise QuotaUnavailable('Shared acquisition ledger is busy; retry later')


def read_info(headers, attempts=4, pause=10):
    """The quota reading is free but was the first casualty of provider strain (2026-11-28: timeouts and 502s
    blocked every refresh before any metered call). Retry it with backoff instead of failing the publication."""
    for attempt in range(attempts):
        try:
            with network_open(Request('https://api.collegefootballdata.com/info', headers=headers), timeout=30) as response:
                return json.load(response)
        except (OSError, ValueError) as error:  # URLError/HTTPError/timeouts are OSError subclasses
            if attempt == attempts - 1 or getattr(error, 'code', 500) in (401, 403):
                raise
            time.sleep(pause * (attempt + 1))


def urlopen(request, *args, **kwargs):
    url = request.full_url if isinstance(request, Request) else str(request)
    parsed = urlsplit(url)
    if parsed.hostname != 'api.collegefootballdata.com' or parsed.path == '/info':
        return network_open(request, *args, **kwargs)
    # Local offline/unit-test workflows are unchanged. In Actions, all real
    # credentialed acquisitions must use the shared ledger; missing setup fails closed.
    if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('CFBD_API_KEY'):
        return network_open(request, *args, **kwargs)
    if os.environ.get('CFBD_SHARED_QUOTA') != 'github':
        raise QuotaUnavailable('Shared quota coordination is not configured')
    token, repo, run = (os.environ.get(k) for k in ('GITHUB_TOKEN', 'GITHUB_REPOSITORY', 'GITHUB_RUN_ID'))
    if not token or not repo or not run:
        raise QuotaUnavailable('Shared quota credentials or run identity unavailable')
    headers = {'Authorization': 'Bearer ' + os.environ['CFBD_API_KEY'], 'Accept': 'application/json'}
    info = read_info(headers)
    level = priority(url, int(os.environ.get('CFBD_SEASON', '2026')))
    if level == 'essential' and os.environ.get('CFBD_ACQUISITION_ROLE') == 'publication':
        level = 'publication'  # a refresh that publishes scores/rankings, not a detection check
    coordinate(GitHubLedger(repo, token), info, run, int(os.environ.get('CFBD_ACQUISITION_LIMIT', '8')),
               level, datetime.now(timezone.utc))
    return network_open(request, *args, **kwargs)
