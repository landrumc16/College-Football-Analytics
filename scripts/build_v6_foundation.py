"""Rebuild V6 derived research from checksum-pinned publisher files in a private cache.

Raw files (including CFBD-origin coach names and enriched athlete biographies)
are never copied into the public repository. Only derived team-season summaries
and source receipts are published. Install the optional research dependency.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path
from urllib.request import urlopen

from cfb_analytics.v6_foundation import recruiting_summary, roster_summary, validate_foundation, validate_registry
from scripts.reconcile_v5_historical_sources import canonical, normalized

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'research/v6'


def packed(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())


def acquire(spec, cache, offline=False):
    for source in spec['sources']:
        target = cache / source['cache_name']
        if not target.exists():
            if offline:
                raise ValueError('Missing retained input: ' + target.name)
            with urlopen(source['url'], timeout=45) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != source['sha256']:
                raise ValueError('Publisher bytes changed; refusing replacement')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != source['sha256']:
            raise ValueError('Cached source checksum mismatch: ' + target.name)


def universe():
    identities = read(DEST / 'identities.json')
    return {int(season): {row['team'] for row in teams} for season, teams in identities['seasons'].items()}


def build(spec, cache):
    import pyarrow.parquet as pq
    eligible = universe()
    # Canonical identity is shared with the retained independent-source review.
    lookup = {normalized(name): name for names in eligible.values() for name in names}
    roster, recruits, talents, crosswalk = {}, {}, {}, {}
    quarantined = Counter()
    for season in range(2015, 2027):
        path = cache / f'cfb_rosters_{season}.parquet'
        columns = ['season', 'team_id', 'athlete_id', 'team_location', 'team_short_display_name', 'team_display_name', 'experience_years']
        by_id = defaultdict(list)
        for row in pq.read_table(path, columns=columns).to_pylist():
            if row['season'] != season:
                raise ValueError('Roster crossed season boundary')
            by_id[str(row['team_id'])].append(row)
        ids_for_season = {}
        labels_for_season = defaultdict(set)
        for team_id, players in by_id.items():
            matches = {lookup[normalized(canonical(str(row[name]))) ] for row in players[:1]
                       for name in ('team_location', 'team_short_display_name', 'team_display_name')
                       if row[name] and normalized(canonical(str(row[name]))) in lookup}
            if len(matches) != 1:
                quarantined['unresolved_roster_identity'] += len(players)
                continue
            team = next(iter(matches))
            if season in eligible and team not in eligible[season]:
                continue
            if (season, team) in roster:
                raise ValueError('Multiple ESPN IDs mapped to same team-season')
            roster[(season, team)] = players
            ids_for_season[team_id] = team
            crosswalk[(season, team)] = team_id
            for label in ('team_location', 'team_short_display_name', 'team_display_name'):
                if players[0].get(label): labels_for_season[normalized(players[0][label])].add(team)
        for dataset, target in [('cfb_recruits', recruits), ('cfb_team_talent', talents)]:
            grouped = defaultdict(list)
            for row in pq.read_table(cache / f'{dataset}_{season}.parquet').to_pylist():
                if row['season'] != season:
                    raise ValueError('Source crossed season boundary')
                team = ids_for_season.get(str(row['team_id']))
                if team is None and row['team_id'] is None:
                    matches = labels_for_season.get(normalized(str(row.get('team', ''))), set())
                    if len(matches) == 1:
                        team = next(iter(matches))
                        quarantined[dataset + '_missing_id_resolved_by_exact_label'] += 1
                if team is not None:
                    grouped[team].append(row)
                else:
                    quarantined[dataset + '_unresolved_identity'] += 1
            for team, rows in grouped.items():
                target[(season, team)] = rows
    coach_groups = defaultdict(list)
    for row in csv.DictReader((cache / 'cfb_coach_seasons.csv').open()):
        season = int(row['season'])
        team = lookup.get(normalized(canonical(row['school'])))
        if team and 2015 <= season <= 2026:
            coach_groups[(season, team)].append(row)
    primary = {}
    for key, rows in coach_groups.items():
        selected = {row['coach'] for row in rows if row['clean_attribution'].lower() == 'true'}
        primary[key] = next(iter(selected)) if len(selected) == 1 else None
    rows = []
    coverage = []
    for season in range(2016, 2027):
        stats = Counter()
        for team in sorted(eligible[season]):
            key = (season, team)
            rr = roster.get(key)
            previous = roster.get((season-1, team))
            roster_stats = roster_summary(rr, {str(p['athlete_id']) for p in previous} if previous else None,
                                          current_season=season == 2026) if rr else None
            rec = recruiting_summary(recruits[key]) if key in recruits else None
            coach = primary.get(key)
            prior = primary.get((season-1, team))
            coaching = None
            if key in coach_groups:
                tenure = 1 if coach else None
                year = season-1
                while coach and primary.get((year, team)) == coach:
                    tenure += 1
                    year -= 1
                coaching = {'reported_assignments': len(coach_groups[key]),
                            'unambiguous_dominant_coach': coach is not None,
                            'same_dominant_coach_as_prior_season': coach == prior if coach and prior else None,
                            'consecutive_observed_seasons': tenure,
                            'scope': 'dominant season attribution, not exact hire dates or current staff; identities retained only in private source cache'}
            four_class = talents.get(key)
            if four_class and len(four_class) != 1:
                raise ValueError('Duplicate recruiting cohort')
            if rec is not None:stats['recruiting'] += 1
            if roster_stats is not None:stats['roster'] += 1
            if coaching is not None:stats['coaching'] += 1
            if all(item is not None for item in (rec, roster_stats, coaching)):stats['all_domains'] += 1
            sources = [f'{name}_{season}' for name, present in [('cfb_recruits',rec),('cfb_rosters',roster_stats)] if present is not None]
            if coaching is not None:sources.append('coach_seasons')
            if four_class:sources.append(f'cfb_team_talent_{season}')
            conferences = {r['conference'] for r in coach_groups.get(key, []) if r['conference']}
            rows.append({'season': season, 'team': team, 'conference': next(iter(conferences)) if len(conferences) == 1 else None, 'espn_team_id': crosswalk.get(key),
                         'recruiting': rec, 'roster': roster_stats, 'coaching': coaching,
                         'four_class_recruits': four_class[0]['n_recruits'] if four_class else None,
                         'source_ids': sources,
                         'season_complete': season < 2026,
                         'historical_pregame_eligible': False})
        coverage.append({'season':season,'eligible_programs':len(eligible[season]),**dict(stats)})
    payload = {'schema_version':1, 'latest_season':2026, 'knowledge_as_of':max(x['retrieved_at'] for x in spec['sources']),
               'historical_asof_verified':False, 'status':'descriptive_source_verified_not_historical_pregame',
               'eligibility_basis': 'NCAA division 11, including transition and opt-out programs; missing domains remain unavailable',
               'team_seasons':rows, 'coverage':coverage, 'identity_diagnostics':dict(quarantined),
               'limitations':['Season labels are not original publication times; historical pregame use is blocked',
                              'Historical roster biography experience excluded due to backfill risk',
                              'Roster overlap measures membership, not returning playing production',
                              'Dominant head-coach continuity is not a causal coaching score or exact effective-date history',
                              '247-derived recruiting and roster observations are publisher snapshots, not independently corroborated player facts',
                              '2020 remains retained for source coverage but excluded from V5 trajectory and primary V6 evaluation']}
    validate_foundation(payload)
    return payload


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    spec = read(DEST / 'sources.json')
    validate_registry(spec)
    acquire(spec,args.cache,args.offline)
    payload = build(spec,args.cache)
    output = gzip.compress(packed(payload),mtime=0)
    target = DEST / 'foundation.json.gz'
    if args.check:
        if target.read_bytes() != output:raise ValueError('Foundation regeneration differs from retained output')
    else:target.write_bytes(output)
    print(json.dumps(validate_foundation(payload)))
    print(json.dumps(payload['coverage']))


if __name__ == '__main__':main()
