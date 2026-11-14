"""Verify the approved branded homepage is present in a production JS bundle."""
from pathlib import Path
import sys


def verify_bundle(directory: Path) -> None:
    markers = (b"College Football Analytics collegiate logo", b"Featured Matchups", b"Program Spotlight")
    if not any(all(marker in bundle.read_bytes() for marker in markers)
               for bundle in (directory / "assets").glob("*.js")):
        raise SystemExit("Dashboard bundle identity missing: expected branded editorial homepage")
    print("Validated branded editorial homepage bundle")


if __name__ == "__main__":
    verify_bundle(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/dist"))
