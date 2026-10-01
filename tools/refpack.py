#!/usr/bin/env python3
"""EA RefPack/QFS decompressor used by MVP 07 database members."""

from __future__ import annotations

import argparse
from pathlib import Path


def decompress(data: bytes) -> bytes:
    if len(data) < 5 or data[1] != 0xFB:
        raise ValueError("Not a supported RefPack stream")

    signature = (data[0] << 8) | data[1]
    pos = 2

    # Header variants with bit 0x0100 contain a 24-bit compressed-size field.
    if signature & 0x0100:
        pos += 3

    if pos + 3 > len(data):
        raise ValueError("Truncated RefPack header")

    expected_size = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
    pos += 3

    out = bytearray()

    def copy_back(distance: int, length: int) -> None:
        if distance <= 0 or distance > len(out):
            raise ValueError(
                f"Invalid RefPack back-reference distance {distance} "
                f"at compressed offset 0x{pos:X}"
            )
        for _ in range(length):
            out.append(out[-distance])

    while True:
        if pos >= len(data):
            raise ValueError("RefPack stream ended before stop command")

        first = data[pos]
        pos += 1

        if not (first & 0x80):
            # 0DDRRRPP DDDDDDDD
            second = data[pos]
            pos += 1
            literal_len = first & 0x03
            out.extend(data[pos : pos + literal_len])
            pos += literal_len
            distance = ((first & 0x60) << 3) + second + 1
            run_len = ((first >> 2) & 0x07) + 3
            copy_back(distance, run_len)

        elif not (first & 0x40):
            # 10RRRRRR PPDDDDDD DDDDDDDD
            second = data[pos]
            third = data[pos + 1]
            pos += 2
            literal_len = second >> 6
            out.extend(data[pos : pos + literal_len])
            pos += literal_len
            distance = ((second & 0x3F) << 8) + third + 1
            run_len = (first & 0x3F) + 4
            copy_back(distance, run_len)

        elif not (first & 0x20):
            # 110DRRPP DDDDDDDD DDDDDDDD RRRRRRRR
            second = data[pos]
            third = data[pos + 1]
            fourth = data[pos + 2]
            pos += 3
            literal_len = first & 0x03
            out.extend(data[pos : pos + literal_len])
            pos += literal_len
            distance = ((first & 0x10) << 12) + (second << 8) + third + 1
            run_len = ((first & 0x0C) << 6) + fourth + 5
            copy_back(distance, run_len)

        else:
            # 111PPPPP -- literal block or stop command
            literal_len = (first & 0x1F) * 4 + 4
            if literal_len <= 0x70:
                out.extend(data[pos : pos + literal_len])
                pos += literal_len
            else:
                literal_len = first & 0x03
                out.extend(data[pos : pos + literal_len])
                pos += literal_len
                break

    if len(out) != expected_size:
        raise ValueError(
            f"RefPack size mismatch: expected {expected_size}, got {len(out)}"
        )

    return bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Decompress an EA RefPack/QFS file")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    decoded = decompress(args.input.read_bytes())
    args.output.write_bytes(decoded)
    print(f"Wrote {len(decoded)} bytes to {args.output}")


if __name__ == "__main__":
    main()
