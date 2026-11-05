"""Generate dependency-free PNG app icons with Python standard library."""
from pathlib import Path
import struct
import zlib

OUT = Path(__file__).resolve().parents[1] / "web" / "public" / "icons"

def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)

def icon(size):
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            u, v = (x + .5) / size, (y + .5) / size
            # Navy rounded square, golden stadium stripes and stylized football.
            inside = .10 <= u <= .90 and .10 <= v <= .90
            if inside and (u < .18 or u > .82) and (v < .18 or v > .82):
                inside = ((u - (.18 if u < .5 else .82))**2 + (v - (.18 if v < .5 else .82))**2) <= .08**2
            color = (10, 23, 42, 255) if inside else (10, 23, 42, 255)
            # Ball ellipse diagonal, dark brown fill and golden outline.
            dx, dy = u - .5, v - .50
            a = (dx + dy) / 1.41421356
            b = (dy - dx) / 1.41421356
            ellipse = (a / .34)**2 + (b / .17)**2
            if .81 <= ellipse <= 1.06:
                color = (244, 187, 67, 255)
            elif ellipse < .81:
                color = (143, 73, 35, 255)
            # White central lace with three crossbars.
            if abs(a) < .135 and abs(b) < .014:
                color = (250, 250, 246, 255)
            if any(abs(a - k) < .013 for k in (-.08, 0, .08)) and abs(b) < .075:
                color = (250, 250, 246, 255)
            raw.extend(color)
    header = b'\x89PNG\r\n\x1a\n'
    data = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return header + png_chunk(b'IHDR', data) + png_chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + png_chunk(b'IEND', b'')

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        path = OUT / f"icon-{size}.png"
        path.write_bytes(icon(size))
        print(f"Generated {path} ({path.stat().st_size} bytes)")
