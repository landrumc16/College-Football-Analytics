"""Validate approved collegiate PWA artwork without regenerating or replacing it."""
from pathlib import Path
import struct

ICONS = Path(__file__).resolve().parents[1] / "web" / "public" / "icons"


def validate_png(path: Path, expected: int) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing approved collegiate icon: {path}. Publish approved assets before building.")
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\\x89PNG\\r\\n\\x1a\\n" or header[12:16] != b"IHDR":
        raise SystemExit(f"Invalid PNG icon: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (expected, expected):
        raise SystemExit(f"Incorrect icon dimensions for {path}: {width}x{height}")


if __name__ == "__main__":
    for size in (192, 512):
        validate_png(ICONS / f"icon-{size}.png", size)
    print("Approved PWA icons present and dimensions validated; no icons regenerated.")
