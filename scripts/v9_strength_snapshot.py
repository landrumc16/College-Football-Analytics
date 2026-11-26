"""Retain an immutable strength observation from an already published report."""
import argparse
import hashlib
import json
import os
import tempfile
import re
from datetime import datetime
from pathlib import Path


def archive(report_path, archive_dir, source_commit):
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("Expected exact source commit SHA")
    raw = Path(report_path).read_bytes()
    report = json.loads(raw)
    published = report.get('generated_at')
    if not published or datetime.fromisoformat(published.replace('Z', '+00:00')).tzinfo is None:
        raise ValueError('Report requires a timezone-aware generated_at')
    rankings = report.get('rankings', [])
    teams = [row['team'] for row in rankings]
    if not teams or len(teams) != len(set(teams)):
        raise ValueError('Expected nonempty unique team rankings')
    digest = hashlib.sha256(raw).hexdigest()
    payload = {
        'schema_version': 1,
        'kind': 'retained_report_observation',
        'report_generated_at': published,
        'retained_at': datetime.now().astimezone().isoformat(),
        'source_commit': source_commit,
        'source_sha256': digest,
        'source_receipt': report.get('retrieved_at'),
        'model_metadata': report.get('model_metadata'),
        'season': report['season'],
        'teams': [{key: row[key] for key in ('team', 'rank', 'rating', 'wins', 'losses')} for row in rankings],
    }
    directory = Path(archive_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f'{digest}.json'
    encoded = json.dumps(payload, indent=2, allow_nan=False) + '\n'
    with tempfile.NamedTemporaryFile(mode='w', dir=directory, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, target)
    except FileExistsError:
        existing = json.loads(target.read_text())
        expected = {key: value for key, value in payload.items() if key not in ('retained_at', 'source_commit')}
        actual = {key: value for key, value in existing.items() if key not in ('retained_at', 'source_commit')}
        if actual != expected:
            raise ValueError('Archive identity conflict')
    finally:
        temporary.unlink()
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    print(archive(args.report, args.archive, args.source_commit))
