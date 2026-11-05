"""Validate approved collegiate PWA artwork without regenerating or replacing it."""
from pathlib import Path
import struct
import hashlib

APPROVED_SHA256 = {
    192: '95ef5977128eb48466ef3f637a1ca41f65745f0032a732314fde568883032e7f',
    512: 'f6f9cb82de6bb10d6c7fd2279948f910623cce35768c9f1c4231bb36e340197d',
}

ICONS = Path(__file__).resolve().parents[1] / "web" / "public" / "icons"


def validate_png(path: Path, expected: int) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing approved collegiate icon: {path}. Publish approved assets before building.")
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\\x89PNG\\r\\n\\x1a\\n" or header[12:16] != b"IHDR":
        raise SystemExit(f"Invalid PNG icon: {path}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != APPROVED_SHA256[expected]:
        raise SystemExit(f'Icon does not match approved collegiate artwork: {path}')
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (expected, expected):
        raise SystemExit(f"Incorrect icon dimensions for {path}: {width}x{height}")


if __name__ == "__main__":
    for size in (192, 512):
        validate_png(ICONS / f"icon-{size}.png", size)
    print("Approved PWA icons present and dimensions validated; no icons regenerated.")
