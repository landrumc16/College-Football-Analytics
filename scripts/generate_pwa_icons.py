"""Validate approved collegiate PWA artwork without regenerating or replacing it."""
from pathlib import Path
import struct
import hashlib

APPROVED_SHA256 = {
    192: '9ee8f88f2896db12130ab7c8586f25f667a34ef6f83662874994d0442f13d16f',
    512: '55e67ccf6f63fd1c64ca2fa4172fb6213ff3e8e7ae5f7044067c98fddcb66ab9',
}

MASKABLE_SHA256 = {
    192: '25c1c24303f3a06d03b33a9bfb27cac70180d601770105d109ec63165acd33ea',
    512: '5f9cf598629df065cd2cb47bad7472ab6c15d561ebdd54d65bb11d5adb166133',
}

ICONS = Path(__file__).resolve().parents[1] / "web" / "public" / "icons"


def validate_png(path: Path, expected: int, checksum: str) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing approved collegiate icon: {path}. Publish approved assets before building.")
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != bytes.fromhex("89504e470d0a1a0a") or header[12:16] != b"IHDR":
        raise SystemExit(f"Invalid PNG icon: {path}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
        raise SystemExit(f'Icon does not match approved collegiate artwork: {path}')
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (expected, expected):
        raise SystemExit(f"Incorrect icon dimensions for {path}: {width}x{height}")


if __name__ == "__main__":
    for size in (192, 512):
        validate_png(ICONS / f"icon-{size}.png", size, APPROVED_SHA256[size])
        validate_png(ICONS / f"icon-maskable-{size}.png", size, MASKABLE_SHA256[size])
    print("Approved PWA icons present and dimensions validated; no icons regenerated.")
