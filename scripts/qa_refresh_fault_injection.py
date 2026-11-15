"""Isolated refresh fault injection (final pre-beta QA, 2026-11-15).

Run ONLY inside a disposable detached worktree; it rewrites data/ files there and restores them.
No network, no git commit/push:  git worktree add --detach /tmp/wt HEAD && cd /tmp/wt &&
  pip install pyyaml && python scripts/qa_refresh_fault_injection.py /tmp/wt
"""
import json, os, re, shutil, subprocess, sys, copy
from pathlib import Path
from unittest.mock import patch
import yaml
WT = Path(sys.argv[1]); os.chdir(WT); sys.path.insert(0, str(WT / 'src'))
from cfb_analytics import refresh as R
GOOD = {p: Path(p).read_bytes() for p in ['data/cfbd-2026-games.json', 'data/season-2026-report.json', 'data/pregame-2026-history.json']}
base = json.loads(GOOD['data/cfbd-2026-games.json'])
def raw_from_snapshot(games):
    out = []
    for g in games:
        out.append({'id': g['game_id'], 'season': 2026, 'week': g['week'], 'homeTeam': g['home'], 'awayTeam': g['away'],
                    'homePoints': g['home_score'], 'awayPoints': g['away_score'], 'completed': g['completed'],
                    'neutralSite': g['neutral_site'], 'startDate': g['start_date']})
    return out
RAW = raw_from_snapshot(base['games'])
def heredocs(wf, step):
    doc = yaml.safe_load(Path(f'.github/workflows/{wf}').read_text())
    for job in doc['jobs'].values():
        for s in job['steps']:
            if s.get('name') == step:
                return [m.replace("${{ github.event_name }}", 'workflow_run') for m in re.findall(r"<<'PY'\n(.*?)\n\s*PY\b", s['run'], re.S)]
    raise KeyError(step)
CHECKS = [('refresh-data.yml', 'Verify live kickoff timestamps are available'), ('refresh-data.yml', 'Verify archived forecast provenance and accuracy')]
def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, 'PYTHONPATH': 'src'})
    return p.returncode, (p.stderr or p.stdout).strip().splitlines()[-2:]
def scenario(name, raw=None, exc=None):
    for p, b in GOOD.items(): Path(p).write_bytes(b)
    res = {'scenario': name}
    try:
        with patch.object(R, 'fetch_cfbd_games', side_effect=exc) if exc else patch.object(R, 'fetch_cfbd_games', return_value=raw):
            res['refresh'] = R.refresh(2026, Path('data/cfbd-2026-games.json'), 'fake')
    except Exception as e:
        res['refresh'] = f'REJECTED: {type(e).__name__}: {str(e)[:90]}'
        res['snapshot_unchanged'] = Path('data/cfbd-2026-games.json').read_bytes() == GOOD['data/cfbd-2026-games.json']
        res['would_commit'] = False; return res
    code, tail = run([sys.executable, '-m', 'cfb_analytics.report', '--season', '2026'])
    res['report'] = 'ok' if code == 0 else f'FAILED {tail}'
    if code: res['would_commit'] = False; return res
    for wf, step in CHECKS:
        for src in heredocs(wf, step):
            code, tail = run([sys.executable, '-c', src])
            if code: res['gate'] = f'{step}: FAILED {tail}'; res['would_commit'] = False; return res
    # Dashboard pre-deploy validation of the published report (build job)
    Path('web/dist').mkdir(parents=True, exist_ok=True); Path('web/dist/index.html').write_text('stub'); shutil.copy('data/season-2026-report.json', 'web/dist/season-report.json')
    if not Path('web/dist/historical-backtest.json').exists():
        run([sys.executable, '-m', 'cfb_analytics.backtest', '--output', 'web/dist/historical-backtest.json'])
    for src in heredocs('dashboard.yml', 'Include and validate published season report'):
        src = src.replace('cp data/season-2026-report.json web/dist/season-report.json', '')
        code, tail = run([sys.executable, '-c', src])
        if code: res['dashboard_gate'] = f'FAILED {tail}'; res['would_deploy'] = False; return res
    rep = json.loads(Path('data/season-2026-report.json').read_text())
    res['would_commit'] = True; res['would_deploy'] = True
    res['published'] = {'teams': rep['summary']['teams'], 'completed': rep['summary']['completed_games'], 'upcoming': rep['summary']['upcoming_games'],
                        'TexasTech': next((f"#{t['rank']} {t['wins']}-{t['losses']}" for t in rep['rankings'] if t['team'] == 'Texas Tech'), None)}
    return res
fbs_completed = [i for i, r in enumerate(RAW) if r['completed']]
cases = [('baseline (unchanged response)', RAW)]
cases.append(('truncated response: first 15% of games', RAW[: len(RAW) * 15 // 100]))
cases.append(('truncated response: only weeks 10-15', [r for r in RAW if r['week'] >= 10]))
reverted = copy.deepcopy(RAW)
for i in fbs_completed[:400]: reverted[i].update(completed=False, homePoints=None, awayPoints=None)
cases.append(('400 completed games regress to unplayed', reverted))
swapped = copy.deepcopy(RAW)
for i in fbs_completed[:200]: swapped[i]['homePoints'], swapped[i]['awayPoints'] = swapped[i]['awayPoints'], swapped[i]['homePoints']
cases.append(('200 final scores swapped home/away', swapped))
nokick = copy.deepcopy(RAW)
for r in nokick: r['startDate'] = None
cases.append(('all kickoff timestamps missing', nokick))
neg = copy.deepcopy(RAW); neg[fbs_completed[0]]['homePoints'] = -7
cases.append(('negative score', neg))
cases.append(('JSON error object instead of list', {'message': 'rate limited'}))
cases.append(('empty list', []))
out = [scenario(n, r) for n, r in cases]
import urllib.error, socket
out.append(scenario('HTTP 503 from CFBD', exc=urllib.error.HTTPError('u', 503, 'Service Unavailable', {}, None)))
out.append(scenario('network timeout', exc=socket.timeout('timed out')))
out.append(scenario('truncated JSON body', exc=json.JSONDecodeError('Unterminated string', '[{"id":', 7)))
for p, b in GOOD.items(): Path(p).write_bytes(b)
print(json.dumps(out, indent=1))
