"""Replay the bounded V5 independent-source review entirely offline.

Original research inputs remain unchanged. Only corroborated records enter the
accepted snapshot; disputed scores and 2020 season totals remain explicit.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from cfb_analytics.v4_team_season_records import team_season_records
from cfb_analytics.v5_program_report_card_pipeline import assemble_report_cards
from scripts.fetch_v5_historical_polls import valid_top25

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'research/archive/verified'
SOURCE = 'https://github.com/landrumc16/College-Football-Analytics/tree/v5-development/research/archive/verified'
ALIASES = {
    'Miami': 'Miami (FL)', 'Mississippi': 'Ole Miss', 'App State': 'Appalachian State',
    'UL Monroe': 'ULM', 'Sam Houston': 'Sam Houston State',
    'Army West Point': 'Army', 'FIU': 'Florida International',
    'Fla. Atlantic': 'Florida Atlantic', 'Ga. Southern': 'Georgia Southern',
    'Middle Tenn.': 'Middle Tennessee', 'NIU': 'Northern Illinois',
    'South Fla.': 'South Florida', 'Southern California': 'USC',
    'Southern Miss.': 'Southern Miss', 'Western Ky.': 'Western Kentucky',
    'Central Mich.': 'Central Michigan', 'Eastern Mich.': 'Eastern Michigan',
    'Western Mich.': 'Western Michigan', 'North Carolina St.': 'NC State',
    'Appalachian St.': 'Appalachian State', 'Louisiana-Lafayette': 'Louisiana',
    'La.-Monroe': 'ULM', 'Connecticut': 'UConn', 'Hawaii': "Hawai'i",
}


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def write(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    if path.suffix == '.gz':
        path.write_bytes(gzip.compress(raw, mtime=0))
    else:
        path.write_bytes(raw)


def canonical(name):
    return ALIASES.get(name, name)


def normalized(name):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower())


def ncaa_inputs():
    report = read(ROOT / 'data/season-2026-report.json')
    historical = read(ROOT / 'research/archive/results/team-season-records-2016-2025.json')
    names = {canonical(t['team']) for s in historical['seasons'] for t in s['teams']} | {r['team'] for r in report['rankings']}
    lookup = {normalized(t): t for t in names}

    def resolve(name):
        name = canonical(name)
        if name.endswith(' St.'):
            name = name[:-4] + ' State'
        return lookup.get(normalized(name))

    def rows(year, dataset):
        path = ARCHIVE / 'ncaa' / f'ncaa_mfb_{dataset}_{year}.csv.gz'
        return list(csv.DictReader(gzip.decompress(path.read_bytes()).decode('utf-8-sig').splitlines()))

    rosters, schedules = {}, {}
    for year in range(2016, 2027):
        teams = rows(year, 'teams')
        fbs = {r['team_id']: resolve(r['team_name']) for r in teams if r['division'] == '11'}
        if any(t is None for t in fbs.values()) or len(set(fbs.values())) != len(fbs):
            raise ValueError(f'{year}: unresolved or duplicate FBS identities')
        rosters[year] = fbs
        if year <= 2025:
            schedules[year] = rows(year, 'schedule')
    return rosters, schedules, resolve


def reconcile():
    # Check retained source bytes before interpreting them.
    inventory = read(ARCHIVE / 'ncaa/inventory.json')
    for item in inventory['seasons']:
        if hashlib.sha256((ARCHIVE / 'ncaa' / item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('NCAA source hash mismatch: ' + item['path'])
    rosters, schedules, resolve = ncaa_inputs()
    games = json.loads(gzip.decompress((ARCHIVE / 'espn-games.json.gz').read_bytes()))
    original = read(ROOT / 'research/archive/results/team-season-records-2016-2025.json')
    accepted_seasons, season_exceptions, score_exceptions, game_counts = [], [], [], []
    for season in original['seasons']:
        year = season['season']
        # Reproduce the retained summary using the actual retained game inputs.
        replay = team_season_records(games[str(year)], year)
        expected = {canonical(r['team']): (r['fbs_wins'], r['fbs_losses']) for r in season['teams']}
        actual = {r['team']: (r['fbs_wins'], r['fbs_losses']) for r in replay['teams']}
        if actual != expected:
            raise ValueError(f'{year}: retained season totals differ from source games')
        fbs = rosters[year]
        totals = {t: [0, 0] for t in fbs.values() if t in expected}
        seen = set()
        game_index = defaultdict(set)
        for r in schedules[year]:
            if not r['team_score'].isdigit() or not r['opponent_score'].isdigit():
                continue  # Cancellations and unplayed fixtures have no result.
            team, opponent = fbs.get(r['team_id']), fbs.get(r['opponent_id'])
            if not team or not opponent or opponent not in expected or team not in totals:
                continue
            key = (r['team_id'], r['contest_id'] or r['date'] + '-' + r['opponent_id'])
            if key in seen:
                raise ValueError(f'{year}: duplicate NCAA team-contest')
            seen.add(key)
            us, them = int(r['team_score']), int(r['opponent_score'])
            if us == them:
                raise ValueError('Unexpected tied modern game')
            totals[team][0 if us > them else 1] += 1
            pair = tuple(sorted((team, opponent)))
            score = tuple(sorted(((team, us), (opponent, them))))
            day = datetime.strptime(r['date'], '%m/%d/%Y').date()
            game_index[pair].add((score, day))
        accepted = []
        for team, counts in sorted(expected.items()):
            if totals.get(team) == list(counts):
                accepted.append({'team': team, 'fbs_wins': counts[0], 'fbs_losses': counts[1]})
            else:
                season_exceptions.append({'season': year, 'team': team, 'espn': list(counts), 'ncaa': totals.get(team), 'disposition': 'exclude disputed team-season; 2020 excluded from trajectories'})
        matched = 0
        for g in games[str(year)]:
            if not g['fbs_game']:
                continue
            pair = tuple(sorted((g['home'], g['away'])))
            score = tuple(sorted(((g['home'], g['home_score']), (g['away'], g['away_score']))))
            day = datetime.fromisoformat(g['kickoff'].replace('Z', '+00:00')).date()
            candidates = [(s, d) for s, d in game_index[pair] if abs((d - day).days) <= 1]
            if any(s == score for s, _ in candidates):
                matched += 1
            else:
                score_exceptions.append({'season': year, 'game_id': g['game_id'], 'espn': dict(score), 'ncaa': [dict(s) for s, _ in candidates], 'disposition': 'exact score excluded from verified cohort; season win/loss totals independently corroborated'})
        game_counts.append({'season': year, 'matching_fbs_game_scores': matched, 'eligible_fbs_games': sum(g['fbs_game'] for g in games[str(year)])})
        accepted_seasons.append({'season': year, 'teams': accepted})
    # Compare all 40 snapshots, including complete ranked membership, not anchors.
    mapping = {k: canonical(v) for k, v in read(ROOT / 'research/v5-national-identity-candidates.json')['mapping'].items()}
    independent = read(ARCHIVE / 'independent-polls.json')
    poll_history = []
    primary_rosters = {s['season']: {canonical(r['team']) for r in s['teams']} for s in original['seasons']}
    full_history = set.intersection(*(set(rosters[y].values()) & (primary_rosters[y] if y != 2020 else set(rosters[y].values())) for y in range(2016, 2026)))
    for year in range(2016, 2026):
        primary = read(ROOT / f'research/archive/polls/poll-snapshots-{year}.json')
        for poll, label in [('ap', 'AP'), ('coaches', 'Coaches')]:
            ranks = {}
            for phase in ['preseason', 'final']:
                left = {mapping[str(r['team_id'])]: r['rank'] for r in primary['snapshots'][f'{poll}_{phase}']}
                right = next(p for p in independent['snapshots'] if (p['season'], p['phase'], p['poll']) == (year, phase, poll))
                rows = right['rows']
                if not valid_top25([r['rank'] for r in rows], [r['team'] for r in rows]):
                    raise ValueError(f'{year} {poll} {phase}: invalid independent top 25')
                if left != {r['team']: r['rank'] for r in rows}:
                    raise ValueError(f'{year} {poll} {phase}: independent poll mismatch')
                ranks[phase] = left
            for team in sorted(full_history):
                poll_history.append({'team': team, 'season': year, 'poll': label, 'preseason_rank': ranks['preseason'].get(team), 'final_rank': ranks['final'].get(team), 'source': primary['source_url'] if year != 2025 else '; '.join(primary['preseason_provenance'][poll]['source_urls'] + [primary['source_url']]), 'source_sha256': primary['source_sha256']})
    report = read(ROOT / 'data/season-2026-report.json')
    eligible = sorted(rosters[2026].values())
    if set(eligible) != {r['team'] for r in report['rankings']}:
        raise ValueError('Current incumbent roster differs from independent NCAA FBS roster')
    records = {'seasons': accepted_seasons}
    cards = assemble_report_cards(poll_rows=poll_history, season_records=records,
        current_rankings=report['rankings'], eligible_fbs=eligible,
        as_of=report['retrieved_at'], latest_completed_season=2025,
        poll_reviewed=True, results_reviewed=True, strength_reviewed=True,
        strength_source='https://github.com/landrumc16/College-Football-Analytics/blob/v5-development/data/season-2026-report.json', results_source=SOURCE)
    cards['publication_status'] = 'complete'
    cards['historical_period'] = [2016, 2025]
    cards['eligible_fbs_source'] = 'https://github.com/sportsdataverse/sportsdataverse-data/releases/download/ncaa_mfb_teams/ncaa_mfb_teams_2026.csv.gz'
    from cfb_analytics.v5_program_trajectory import trajectory_measurements
    trajectory = trajectory_measurements(records, latest_completed_season=2025, source=SOURCE, source_reviewed=True)
    for card in cards['programs']:
        team = card['team']
        card['trajectory'] = trajectory.get(team)
        card['hype'] = {}
        for poll in ['AP', 'Coaches']:
            rows = [r for r in poll_history if r['team'] == team and r['poll'] == poll]
            if len(rows) == 10:
                card['hype'][poll] = {
                    'seasons': 10, 'preseason_top25': sum(r['preseason_rank'] is not None for r in rows),
                    'retained_top25': sum(r['preseason_rank'] is not None and r['final_rank'] is not None for r in rows),
                    'dropped_out': sum(r['preseason_rank'] is not None and r['final_rank'] is None for r in rows),
                    'entered_top25': sum(r['preseason_rank'] is None and r['final_rank'] is not None for r in rows),
                    'ranked_to_ranked_movement': sum(r['preseason_rank']-r['final_rank'] for r in rows if r['preseason_rank'] is not None and r['final_rank'] is not None),
                }
    cards['sources'] = [SOURCE, cards['eligible_fbs_source']]
    summary = {'schema_version': 1, 'policy': 'two independent sources; exception review only',
        'poll_snapshots_compared': 40, 'ranked_placements_compared': 1000,
        'accepted_team_seasons': sum(len(s['teams']) for s in accepted_seasons),
        'season_exceptions': season_exceptions, 'score_exceptions': score_exceptions,
        'game_coverage': game_counts, 'coverage': cards['coverage'],
        'excluded_from_trajectory': [2020], 'identity_mapping_version': 1}
    return records, poll_history, cards, summary


def main():
    records, polls, cards, summary = reconcile()
    write(ARCHIVE / 'accepted-team-seasons.json', records)
    write(ARCHIVE / 'accepted-poll-history.json.gz', polls)
    write(ARCHIVE / 'comparison.json', summary)
    write(ROOT / 'web/public/v5-program-report-cards.json', cards)
    by_year = {s['season']: {r['team']: r for r in s['teams']} for s in records['seasons']}
    results = []
    for team in sorted({r['team'] for s in records['seasons'] for r in s['teams']}):
        windows = {}
        for span in [3, 5, 10]:
            years = [y for y in range(2026-span, 2026) if y != 2020]
            if all(team in by_year[y] for y in years):
                wins = sum(by_year[y][team]['fbs_wins'] for y in years)
                losses = sum(by_year[y][team]['fbs_losses'] for y in years)
                windows[str(span)] = {'wins': wins, 'losses': losses, 'win_pct': wins/(wins+losses), 'seasons': years}
        results.append({'team': team, 'windows': windows})
    write(ROOT / 'web/public/v5-historical-results.json', {
        'schema_version': 1, 'status': 'independently_corroborated_results',
        'source_review_attested': True, 'national_grades_available': False,
        'latest_completed_season': 2025, 'excluded_seasons': [2020],
        'source': SOURCE, 'programs': results})
    print(json.dumps({k: summary[k] for k in ['accepted_team_seasons', 'poll_snapshots_compared', 'coverage']}))


if __name__ == '__main__':
    main()
