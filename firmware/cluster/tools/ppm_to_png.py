#!/usr/bin/env python3
"""Convert the host harness's RGB P6 captures to PNG using only the standard library."""
import argparse
from pathlib import Path
import struct
import zlib


def convert(path: Path) -> Path:
    magic, dimensions, depth, pixels = path.read_bytes().split(b'\n', 3)
    if magic != b'P6' or depth != b'255':
        raise ValueError(f'{path}: expected binary 8-bit RGB P6 capture')
    width, height = map(int, dimensions.split())
    if width != 1280 or height != 800 or len(pixels) != width * height * 3:
        raise ValueError(f'{path}: invalid 1280x800 RGB capture length')

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    scanlines = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(scanlines, 6)) + chunk(b'IEND', b'')
    target = path.with_suffix('.png')
    target.write_bytes(png)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    captures = sorted(args.directory.glob('*.ppm'))
    if not captures:
        parser.error('no PPM captures in directory')
    for capture in captures:
        print(convert(capture))
