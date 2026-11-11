"""Reconcile sourced fast observations and atomically publish safe update state.

Usage: python -m cfb_analytics.v5_fast_updates_cli --input observations.json
--confirmed existing-confirmed.json --output web/public/fast-updates.json

Confirmed records are retained when new observations disagree or are merely
provisional. Never feed provisional scores into the prediction model.
"""
import argparse
import json
import os
from pathlib import Path
from .v5_fast_updates import reconcile, _timestamp


def publish(observations, previous=None):
    result = reconcile(observations)
    previous = previous or {}
    confirmed = previous.get("confirmed")
    if result["status"] == "confirmed":
        incoming = result["data"]
        if confirmed is not None:
            if confirmed.get("kind") != incoming["kind"]:
                raise ValueError("Confirmed snapshot kind mismatch")
            if incoming["kind"] != "game_final":
                older = (confirmed.get("season"), confirmed.get("week"))
                newer = (incoming.get("season"), incoming.get("week"))
                if newer < older:
                    raise ValueError("Refusing to replace newer confirmed poll")
                if newer == older and confirmed.get("rankings") != incoming.get("rankings"):
                    raise ValueError("Conflicting confirmed rankings for same poll week")
            elif confirmed.get("game_id") != incoming.get("game_id"):
                raise ValueError("Game identifier mismatch")
            elif _timestamp(incoming["published_at"]) < _timestamp(confirmed["published_at"]):
                raise ValueError("Refusing older confirmed game update")
        confirmed = incoming
    if confirmed is not None and confirmed.get("kind") != result["kind"]:
        raise ValueError("Confirmed snapshot kind mismatch")
    return {
        "schema_version": 1,
        "kind": result["kind"],
        "status": result["status"],
        "provisional": result["data"] if result["status"] == "provisional" else None,
        "confirmed": confirmed,
        "sources": result["sources"],
        "model_ingestion_allowed": result["status"] == "confirmed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--confirmed", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    observations = json.loads(args.input.read_text(encoding="utf-8"))
    previous = json.loads(args.confirmed.read_text(encoding="utf-8")) if args.confirmed and args.confirmed.exists() else None
    output = publish(observations, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_name(args.output.name + ".tmp")
    try:
        temp.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, args.output)
    finally:
        temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
