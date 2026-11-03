"""CLI for historical recruiting research collection (no production forecasts)."""
import argparse
import json
import os
from pathlib import Path
from .v34_recruiting_history import refresh_history


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=2016)
    parser.add_argument("--end", type=int, default=2025)
    parser.add_argument("--output", type=Path, default=Path("data/cfbd-recruiting-history.json"))
    args = parser.parse_args()
    if args.end < args.start or args.end - args.start > 19:
        parser.error("Expected chronological range of at most 20 seasons")
    print(json.dumps(refresh_history(range(args.start, args.end + 1), args.output,
                                     os.getenv("CFBD_API_KEY", ""))))


if __name__ == "__main__":
    main()
