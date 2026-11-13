"""Compare the retained historical results archive with a second provider's export.

Example:
  python -m cfb_analytics.v5_historical_results_compare_cli \
    --independent path/to/independent-team-season-records.json \
    --independent-source https://independent.example/source \
    --output research/v5-results-comparison.json

No source is promoted automatically. Review the provider independence and
exceptions before using matching records for publication.
"""
import argparse
import json
from pathlib import Path

from .v5_historical_results_comparison import compare_historical_results

DEFAULT_PRIMARY = Path("research/archive/results/team-season-records-2016-2025.json")
DEFAULT_OUTPUT = Path("research/v5-results-comparison.json")
PRIMARY_SOURCE = "https://github.com/sportsdataverse/sportsdataverse-data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--primary-source", default=PRIMARY_SOURCE)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--independent-source", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.primary.resolve() == args.independent.resolve():
        parser.error("Independent input must be a different file")
    try:
        primary = json.loads(args.primary.read_text(encoding="utf-8"))
        independent = json.loads(args.independent.read_text(encoding="utf-8"))
        result = compare_historical_results(
            primary, independent,
            primary_source=args.primary_source,
            independent_source=args.independent_source,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Matching records: {result['matching_count']}; exceptions: {result['exception_count']}")
    print("Comparison only: independent-source review and publication approval still required.")


if __name__ == "__main__":
    main()
