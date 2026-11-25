"""Stage a scenario packet paired to exact review-report bytes; offline only."""
import argparse
import hashlib
import json
from pathlib import Path
from cfb_analytics.v6_scenarios import scenario_input


def build_packet(report_bytes, games_bytes):
    report = json.loads(report_bytes)
    packet = scenario_input(report, json.loads(games_bytes))
    packet['report_sha256'] = hashlib.sha256(report_bytes).hexdigest()
    return packet


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--games', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    packet = build_packet(args.report.read_bytes(), args.games.read_bytes())
    args.output.write_text(json.dumps(packet, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
