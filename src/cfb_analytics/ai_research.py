"""AI-assisted rapid results research adapter (issue #74).

The adapter asks a research model, through web search, to report what public sources say about games that should
have finished. Each claim is cited. A result is published provisionally only when at least two independent source
families report the same final score, and any disagreeing family is clearly outnumbered. CFBD stays authoritative:
later CFBD refreshes verify or correct the result through the existing rapid lifecycle (``rapid_results``).

Nothing here runs unless the owner enables it. The registry ``operations/rapid-sources.json`` must contain
``"adapters": {"ai_research": true}`` and ``"enabled": true``, and the runtime needs an Anthropic API key (paid
usage). Search goes through the model provider's web search tool; this module never fetches publisher pages
itself. Only facts (scores, status, basic statistics) and citation URLs are stored, never article text.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .v5_fast_updates import _provider, _timestamp

ADAPTER = 'ai_research'
STAT_KEYS = ('total_yards', 'passing_yards', 'rushing_yards', 'turnovers', 'first_downs')
STATUSES = {'final', 'in_progress', 'scheduled', 'postponed', 'canceled', 'suspended', 'unknown'}
# Outlets that normally carry the Associated Press game story; several of them are one report, not several.
AP_SYNDICATORS = {'apnews.com', 'washingtonpost.com', 'usnews.com', 'abcnews.go.com', 'sfgate.com', 'startribune.com'}
# Never evidence: user-generated, social, encyclopedic or wagering pages.
EXCLUDED = {'wikipedia.org', 'reddit.com', 'x.com', 'twitter.com', 'facebook.com', 'instagram.com', 'tiktok.com',
            'youtube.com', 'draftkings.com', 'fanduel.com', 'covers.com', 'actionnetwork.com', 'oddsshark.com'}
TWO_LEVEL_SUFFIXES = {'co.uk', 'com.au', 'co.nz', 'co.za', 'go.com'}


def _host(url):
    return (urlsplit(url).hostname or '').lower().rstrip('.')


def _registrable(host):
    parts = host.split('.')
    if len(parts) >= 3 and '.'.join(parts[-2:]) in TWO_LEVEL_SUFFIXES:
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:]) if len(parts) >= 2 else host


def family(url, attribution=None):
    """Upstream family used for independence: syndicated copies of one report count once."""
    if isinstance(attribution, str) and attribution.strip().lower() in {'ap', 'associated press', 'the associated press'}:
        return 'ap'
    host = _host(url)
    domain = _registrable(host)
    if 'espn' in host.split('.') or domain.startswith('espn.'):
        return 'espn'  # international ESPN mirrors and CFBD (ESPN-derived) are one family
    if domain in {'cbssports.com', 'cbsnews.com'}:
        return 'cbs'
    if domain in AP_SYNDICATORS:
        return 'ap'
    known = _provider(url)
    return known if known in {'espn', 'ncaa'} else domain


def _excluded(url):
    return _registrable(_host(url)) in EXCLUDED


def _score(value):
    return value if type(value) is int and 0 <= value <= 200 else None


def _claims(raw):
    """Keep well-formed, cited, final-score claims; malformed model output is dropped, never repaired."""
    valid, rejected = [], []
    for claim in raw if isinstance(raw, list) else []:
        url = claim.get('url') if isinstance(claim, dict) else None
        reason = None
        if not isinstance(url, str) or not url.startswith('https://') or not _host(url):
            reason = 'missing https citation'
        elif _excluded(url):
            reason = 'excluded source type'
        elif _score(claim.get('home_score')) is None or _score(claim.get('away_score')) is None:
            reason = 'no explicit final score'
        elif claim['home_score'] == claim['away_score']:
            reason = 'tied score'
        if reason:
            rejected.append({'url': url if isinstance(url, str) else None, 'reason': reason})
            continue
        valid.append({**claim, 'family': family(url, claim.get('attribution'))})
    return valid, rejected


def _stats(claims):
    """Basic statistics only where a cited source states them; disagreeing values are dropped, never averaged."""
    seen = {}
    for claim in claims:
        stats = claim.get('basic_stats')
        if not isinstance(stats, dict):
            continue
        for side in ('home', 'away'):
            for key, value in (stats.get(side) or {}).items() if isinstance(stats.get(side), dict) else ():
                if key in STAT_KEYS and type(value) is int and value >= 0:
                    seen.setdefault((side, key), set()).add(value)
    out = {}
    for (side, key), values in sorted(seen.items()):
        if len(values) == 1:
            out.setdefault(side, {})[key] = values.pop()
    return out


def verify(game, report):
    """Decide whether one researched game may be published provisionally.

    Rule: the leading score needs at least two independent families, every alternative score at most one
    family, and the leader at least two more families than any alternative. Anything else is withheld.
    """
    status = report.get('status') if report.get('status') in STATUSES else 'unknown'
    claims, rejected = _claims(report.get('claims'))
    if status != 'final':
        return {'game_id': game['game_id'], 'decision': 'not_final', 'status': status, 'rejected': rejected}
    payloads = {}
    for claim in claims:
        payloads.setdefault((claim['home_score'], claim['away_score']), []).append(claim)
    if not payloads:
        return {'game_id': game['game_id'], 'decision': 'insufficient', 'status': status, 'families': 0, 'rejected': rejected}
    ranked = sorted(payloads.items(), key=lambda item: -len({c['family'] for c in item[1]}))
    (home_score, away_score), support = ranked[0]
    families = sorted({c['family'] for c in support})
    alternatives = [{'home_score': h, 'away_score': a, 'families': sorted({c['family'] for c in rows}),
                     'urls': sorted({c['url'] for c in rows})} for (h, a), rows in ranked[1:]]
    worst = max((len(alt['families']) for alt in alternatives), default=0)
    if len(families) < 2:
        decision = 'insufficient'
    elif worst > 1 or len(families) < worst + 2:
        decision = 'conflict'
    else:
        decision = 'publish'
    evidence = [{'url': c['url'], 'family': c['family'], 'publisher': c.get('publisher'),
                 'published_at': c.get('published_at')} for c in support]
    return {'game_id': game['game_id'], 'decision': decision, 'status': status, 'home_score': home_score,
            'away_score': away_score, 'families': families, 'evidence': evidence, 'conflicts': alternatives,
            'overtime': any(c.get('overtime') is True for c in support), 'basic_stats': _stats(support),
            'rejected': rejected}


def _primary(evidence):
    """Prefer a non-ESPN, non-syndicated citation (often the school's own page) for public attribution."""
    ranked = sorted(evidence, key=lambda e: (e['family'] in {'espn', 'ap', 'cbs'}, e['url']))
    return ranked[0]['url']


def observation(game, decision, observed_at):
    """Build a rapid-inbox observation (``rapid_results`` schema) for a ``publish`` decision."""
    if decision['decision'] != 'publish':
        raise ValueError('Only verified research decisions are publishable')
    times = []
    for item in decision['evidence']:
        try:
            stamp = _timestamp(item.get('published_at'))
        except (ValueError, TypeError):
            continue
        kickoff = game.get('start_date')
        if stamp <= observed_at and (not kickoff or stamp >= _timestamp(kickoff)):
            times.append(stamp)
    row = {'kind': 'game_final', 'status': 'final', 'game_id': game['game_id'], 'home': game['home'],
           'away': game['away'], 'home_score': decision['home_score'], 'away_score': decision['away_score'],
           'source': _primary(decision['evidence']), 'adapter': ADAPTER,
           # Earliest dated corroborating report; otherwise the time this adapter first saw the final.
           'published_at': (min(times) if times else observed_at).isoformat(),
           'observed_at': observed_at.isoformat(), 'independent_families': decision['families'],
           'evidence': decision['evidence'], 'conflicts': decision['conflicts'], 'overtime': decision['overtime']}
    if decision['basic_stats']:
        row['basic_stats'] = decision['basic_stats']
    return row


def intake_authorized(observation_row):
    """Re-check an inbox observation at publication time; the inbox file is never trusted on its own."""
    if observation_row.get('adapter') != ADAPTER:
        return False
    source = observation_row.get('source')
    if not isinstance(source, str) or not source.startswith('https://') or _registrable(_host(source)) == 'collegefootballdata.com':
        return False  # CFBD verification is reserved for the authoritative reconciliation path
    evidence = observation_row.get('evidence')
    if not isinstance(evidence, list) or source not in {e.get('url') for e in evidence if isinstance(e, dict)}:
        return False
    claims, _ = _claims([{**e, 'home_score': observation_row.get('home_score'), 'away_score': observation_row.get('away_score')}
                         for e in evidence if isinstance(e, dict)])
    families = {c['family'] for c in claims}
    conflicts = observation_row.get('conflicts') or []
    worst = max((len(set(c.get('families', []))) for c in conflicts if isinstance(c, dict)), default=0)
    return len(families) >= 2 and worst <= 1 and len(families) >= worst + 2


def authorized_sources(registry, observations):
    """Exact-URL registry plus, when the owner enabled the adapter, re-verified AI research citations."""
    if registry.get('enabled') is not True:
        return {}
    sources = dict(registry.get('sources', {}))
    if (registry.get('adapters') or {}).get(ADAPTER) is True:
        for row in observations:
            if intake_authorized(row) and row['source'] not in sources:
                sources[row['source']] = ADAPTER
    return sources


def due_games(schedule, state, now, attempts=None, *, settle=timedelta(minutes=150), horizon=timedelta(hours=12),
              retry=timedelta(minutes=5)):
    """Games past their likely final whistle that have no rapid result yet (event-window focus)."""
    attempts = attempts or {}
    known = {str(e['game_id']) for e in (state or {}).get('events', [])}
    due = []
    for game in schedule:
        if game.get('completed') or not game.get('start_date') or str(game['game_id']) in known:
            continue
        kickoff = _parse(game['start_date'])
        if kickoff is None or not kickoff + settle <= now <= kickoff + horizon:
            continue
        last = attempts.get(str(game['game_id']))
        if last and now - datetime.fromisoformat(last) < retry:
            continue
        due.append(game)
    return sorted(due, key=lambda g: (g['start_date'], str(g['game_id'])))


def _parse(value):
    try:
        moment = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None
    return moment if moment.tzinfo is not None else None


def batches(games, size):
    return [games[i:i + size] for i in range(0, len(games), size)]


def batch_id(observations, now):
    digest = hashlib.sha256(json.dumps(observations, sort_keys=True).encode()).hexdigest()[:12]
    return f"ai-{now.strftime('%Y%m%dT%H%M%SZ')}-{digest}"


def research_round(schedule, state, researcher, now, *, attempts=None, batch_size=8, max_games=40):
    """One adapter pass: research due games, verify, and return publishable observations plus a ledger."""
    attempts = dict(attempts or {})
    due = due_games(schedule, state, now, attempts)[:max_games]
    observations, ledger = [], []
    for group in batches(due, batch_size):
        try:
            reports = researcher(group, now)
        except Exception as error:  # a research failure must never break the watcher or publication path
            ledger.extend({'game_id': g['game_id'], 'decision': 'research_error', 'error': str(error)[:200]} for g in group)
            continue
        for game in group:
            attempts[str(game['game_id'])] = now.isoformat()
            report = reports.get(str(game['game_id']), {'status': 'unknown', 'claims': []})
            decision = verify(game, report)
            ledger.append(decision)
            if decision['decision'] == 'publish':
                observations.append(observation(game, decision, now))
    return observations, ledger, attempts


def prevalidate(observations, schedule, state, registry):
    """Drop rows the publisher would reject, so one bad row cannot block a whole batch."""
    from .rapid_results import transition
    sources = authorized_sources({**registry, 'enabled': True, 'adapters': {ADAPTER: True}}, observations)
    kept, dropped, trial = [], [], copy.deepcopy(state) if state else None
    for row in observations:
        try:
            trial = transition(trial, row, schedule, sources)
        except ValueError as error:
            dropped.append({'game_id': row.get('game_id'), 'reason': str(error)})
            continue
        kept.append(row)
    return kept, dropped


def write_batch(directory, index_path, observations, now):
    """Write an immutable batch file, then append its ID to the append-only index (PR #79 contract)."""
    if not observations:
        return None
    envelope = {'batch_id': batch_id(observations, now), 'observations': [{'observation': row} for row in observations]}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{envelope['batch_id']}.json"
    data = json.dumps(envelope, indent=2, sort_keys=True) + '\n'
    if path.exists() and path.read_text() != data:
        raise ValueError('Batch ID reused with different content')
    path.write_text(data)
    index_path = Path(index_path)
    index = json.loads(index_path.read_text()) if index_path.exists() else {'batch_ids': []}
    ids = list(index.get('batch_ids', []))
    if envelope['batch_id'] not in ids:
        ids.append(envelope['batch_id'])
    index_path.write_text(json.dumps({'batch_ids': ids}, indent=2) + '\n')
    return envelope['batch_id']


# --- Production researcher (Anthropic Messages API with the web search server tool) -----------------------------

REPORT_TOOL = {
    'name': 'report_results',
    'description': 'Report what cited public sources say about each requested game. Call exactly once, at the end.',
    'input_schema': {
        'type': 'object', 'additionalProperties': False, 'required': ['games'],
        'properties': {'games': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['game_id', 'status', 'claims'],
            'properties': {
                'game_id': {'type': 'string'},
                'status': {'type': 'string', 'enum': sorted(STATUSES)},
                'claims': {'type': 'array', 'items': {
                    'type': 'object', 'additionalProperties': False,
                    'required': ['url', 'publisher', 'home_score', 'away_score', 'published_at', 'attribution', 'overtime'],
                    'properties': {
                        'url': {'type': 'string'}, 'publisher': {'type': 'string'},
                        'home_score': {'type': ['integer', 'null']}, 'away_score': {'type': ['integer', 'null']},
                        'published_at': {'type': ['string', 'null']}, 'attribution': {'type': ['string', 'null']},
                        'overtime': {'type': ['boolean', 'null']},
                        'basic_stats': {'type': 'object', 'additionalProperties': False, 'properties': {
                            side: {'type': 'object', 'additionalProperties': False,
                                   'properties': {k: {'type': 'integer'} for k in STAT_KEYS}} for side in ('home', 'away')}},
                    }}},
            }}}},
    },
}

SYSTEM = (
    'You are a careful college football results researcher. For each requested game, use web search to find what '
    'public sources report right now. Prefer the two schools\' official athletics sites, the conference, NCAA.com, '
    'ESPN, Fox Sports, CBS Sports and AP. Report one claim per source page that explicitly states a final score, with '
    'its exact URL, the score oriented to the requested home and away teams, the page\'s publication time if shown, '
    'and the wire attribution if the page carries an AP story. Do not infer, compute or recall scores; never report a '
    'preview, prediction, betting line or a different season. If no source states a final, report the game status '
    '(in_progress, scheduled, postponed, canceled, suspended or unknown) with no claims. Include basic_stats only '
    'when a cited box score states them. Then call report_results once.'
)


class AnthropicResearcher:
    """Calls the Messages API with web search. Needs ANTHROPIC_API_KEY (an owner-provided, paid credential)."""

    def __init__(self, model='claude-opus-5-5', *, searches_per_game=3, effort='low', client=None):
        if client is None:
            import anthropic  # optional dependency: pip install 'cfb-analytics[research]'
            client = anthropic.Anthropic()
        self.client, self.model = client, model
        self.searches_per_game, self.effort = searches_per_game, effort
        self.usage = []

    def __call__(self, games, now):
        lines = [f"- game_id {g['game_id']}: {g['away']} at {g['home']}" + (' (neutral site)' if g.get('neutral_site') else '')
                 + f", kickoff {g['start_date']}" for g in games]
        messages = [{'role': 'user', 'content': f"Current time {now.isoformat()}. Research these games:\n" + '\n'.join(lines)}]
        tools = [{'type': 'web_search_20260209', 'name': 'web_search',
                  'max_uses': max(2, self.searches_per_game * len(games)), 'blocked_domains': sorted(EXCLUDED)}, REPORT_TOOL]
        for _ in range(4):
            response = self.client.messages.create(
                model=self.model, max_tokens=16000, system=SYSTEM, tools=tools, messages=messages,
                output_config={'effort': self.effort})
            usage = getattr(response, 'usage', None)
            self.usage.append({'input_tokens': getattr(usage, 'input_tokens', None), 'output_tokens': getattr(usage, 'output_tokens', None),
                               'web_search_requests': getattr(getattr(usage, 'server_tool_use', None), 'web_search_requests', None)})
            if response.stop_reason == 'pause_turn':
                messages.append({'role': 'assistant', 'content': response.content})
                continue
            if response.stop_reason == 'refusal':
                raise RuntimeError('Research request declined')
            for block in response.content:
                if getattr(block, 'type', None) == 'tool_use' and block.name == 'report_results':
                    wanted = {str(g['game_id']) for g in games}
                    return {str(item['game_id']): item for item in block.input.get('games', []) if str(item['game_id']) in wanted}
            raise RuntimeError('Research model did not report results')
        raise RuntimeError('Research did not finish')


def utcnow():
    return datetime.now(timezone.utc)


# --- Watcher integration ----------------------------------------------------------------------------------------

def research_schedule(report_schedule, cfbd_games):
    """Canonical report identities (what the publisher validates) plus CFBD kickoff times for event windows."""
    kickoffs = {str(g['game_id']): g.get('start_date') for g in cfbd_games}
    return [dict(g, start_date=g.get('start_date') or kickoffs.get(str(g['game_id']))) for g in report_schedule]


def publish_batch_github(providers, envelope):
    """Create the immutable batch file on main, then append its ID to the index (GitHub contents API)."""
    import base64

    def put(path, text, message, sha=None):
        body = {'message': message, 'branch': 'main', 'content': base64.b64encode(text.encode()).decode()}
        if sha:
            body['sha'] = sha
        return providers.github(f'contents/{path}', 'PUT', body)

    batch = envelope['batch_id']
    put(f'operations/rapid-inbox/{batch}.json', json.dumps(envelope, indent=2, sort_keys=True) + '\n',
        f'Add AI research rapid batch {batch}')
    for _ in range(3):  # the index is append-only; retry on a concurrent index update
        current = providers.github('contents/operations/rapid-inbox.json?ref=main')
        index = json.loads(base64.b64decode(current['content']).decode())
        ids = list(index.get('batch_ids', [index['batch_id']] if index.get('batch_id') else []))
        if batch in ids:
            return
        try:
            put('operations/rapid-inbox.json', json.dumps({'batch_ids': ids + [batch]}, indent=2) + '\n',
                f'Queue AI research rapid batch {batch}', current['sha'])
            return
        except Exception as error:
            if getattr(error, 'code', None) not in (409, 422):
                raise
    raise RuntimeError('Could not append the rapid batch to the index')


class ResearchStep:
    """Event-watcher step: every ``interval`` during event windows, research due games and queue a verified batch.

    Off unless the watcher is started with AI_RESEARCH_ENABLED=true and an API key, and the main-branch registry
    enables both rapid results and this adapter. Failures are recorded as alerts and never stop the watcher.
    """

    def __init__(self, providers, clock, schedule, researcher, *, enabled=False, dry_run=False,
                 interval=timedelta(minutes=5), max_requests=120, batch_size=8, on_batch=None):
        self.p, self.clock, self.schedule, self.researcher = providers, clock, schedule, researcher
        self.enabled, self.dry_run, self.interval = enabled and researcher is not None, dry_run, interval
        self.max_requests, self.batch_size, self.on_batch = max_requests, batch_size, on_batch
        self.requests, self.attempts, self.queued = 0, {}, set()
        self.next_run, self.ledger, self.batches, self.alerts = None, [], [], []

    def _counting(self, games, now):
        if self.requests >= self.max_requests:
            raise RuntimeError('AI research request cap reached for this watcher run')
        self.requests += 1
        return self.researcher(games, now)

    def step(self):
        if not self.enabled or self.dry_run:
            return
        now = self.clock()
        if self.next_run and now < self.next_run:
            return
        self.next_run = now + self.interval
        try:
            registry, _ = self.p.rapid_inbox(published=())
            if registry.get('enabled') is not True or (registry.get('adapters') or {}).get(ADAPTER) is not True:
                return
            live = self.p.live_fast_results()
            known = [e for e in live.get('events', []) if isinstance(e, dict)]
            state = {'events': known + [{'game_id': gid} for gid in self.queued]}
            if not due_games(self.schedule, state, now, self.attempts):
                return
            rows, ledger, self.attempts = research_round(self.schedule, state, self._counting, now,
                                                         attempts=self.attempts, batch_size=self.batch_size)
            self.ledger.extend({**d, 'researched_at': now.isoformat()} for d in ledger)
            rows, dropped = prevalidate(rows, self.schedule, None, registry)
            self.ledger.extend({'game_id': d['game_id'], 'decision': 'publisher_rejected', 'reason': d['reason']} for d in dropped)
            if not rows:
                return
            envelope = {'batch_id': batch_id(rows, now), 'observations': [{'observation': row} for row in rows]}
            publish_batch_github(self.p, envelope)
            self.queued |= {str(row['game_id']) for row in rows}
            self.batches.append({'batch_id': envelope['batch_id'], 'queued_at': now.isoformat(), 'games': len(rows)})
            if self.on_batch:
                self.on_batch()
        except Exception as error:
            message = 'AI research step failed: ' + str(error)[:160]
            if message not in self.alerts:
                self.alerts.append(message)

    def record(self):
        return {'enabled': self.enabled, 'requests': self.requests, 'batches': self.batches,
                'decisions': self.ledger[-200:], 'alerts': self.alerts}
