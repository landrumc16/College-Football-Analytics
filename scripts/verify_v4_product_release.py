"""V4 product-only release guard: never silently promote the research challenger."""
import argparse
import json
from pathlib import Path


def validate_product_report(report: dict) -> dict:
    metadata = report.get("model_metadata") or {}
    model_id = metadata.get("model_id")
    model_status = metadata.get("model_status")
    # Only the existing production workbook model may drive the product release.
    if model_id != "workbook_2026_baseline" or model_status != "incumbent_not_v3_promoted":
        raise ValueError("V4 product release must retain the existing incumbent model identity")
    if metadata.get("historical_study") != "retrospective_research_only":
        raise ValueError("Historical evaluation must remain explicitly retrospective")
    games = report.get("predictions")
    if not isinstance(games, list) or not games:
        raise ValueError("Product release requires nonempty incumbent predictions")
    ids = set()
    for game in games:
        key = game.get("game_id")
        if key is None or key in ids:
            raise ValueError("Missing or duplicate prediction game ID")
        ids.add(key)
        p = game.get("home_win_probability")
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 <= p <= 1:
            raise ValueError("Invalid incumbent win probability")
        if game.get("predicted_winner") not in (game.get("home"), game.get("away")):
            raise ValueError("Predicted winner must be a participating team")
    return {"status": "incumbent_identity_guard_pass", "model_id": model_id,
            "model_status": model_status, "predictions": len(games),
            "challenger_promoted": False,
            "disclaimer": "Model identity checks are not independent verification of frozen V3.4.2 parity."}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(validate_product_report(json.loads(args.report.read_text())), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
