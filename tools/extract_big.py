#!/usr/bin/env python3
"""Extract EA BIGF archives used by MVP 07.

Current format knowledge is documented in docs/research/database_big_roster.md.
This tool intentionally performs lossless extraction only; repacking will be
added after alignment/checksum behavior is confirmed.
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BigEntry:
    name: str
    offset: int
    size: int


def parse_bigf(path: Path) -> tuple[bytes, list[BigEntry]]:
    data = path.read_bytes()
    if len(data) < 16 or data[:4] != b"BIGF":
        raise ValueError("Not a supported BIGF archive")

    declared_size = struct.unpack_from("<I", data, 4)[0]
    file_count = struct.unpack_from(">I", data, 8)[0]
    header_size = struct.unpack_from(">I", data, 12)[0]

    if declared_size != len(data):
        raise ValueError(
            f"Declared archive size {declared_size} != actual size {len(data)}"
        )

    pos = 16
    entries: list[BigEntry] = []
    for _ in range(file_count):
        if pos + 8 > len(data):
            raise ValueError("Truncated BIGF directory")
        offset, size = struct.unpack_from(">II", data, pos)
        pos += 8

        try:
            end = data.index(0, pos)
        except ValueError as exc:
            raise ValueError("Unterminated BIGF filename") from exc

        name = data[pos:end].decode("latin-1")
        pos = end + 1

        if offset + size > len(data):
            raise ValueError(f"Entry {name!r} extends beyond archive")
        entries.append(BigEntry(name, offset, size))

    # header_size appears to describe the unaligned table end in the observed
    # MVP 07 archive. Do not require pos == header_size; preserve this as data
    # to investigate further.
    _ = header_size
    return data, entries


def extract(path: Path, output_dir: Path) -> None:
    data, entries = parse_bigf(path)
    output_dir.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        target = output_dir / entry.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data[entry.offset : entry.offset + entry.size])
        print(
            f"{entry.name:20} offset=0x{entry.offset:08X} "
            f"size={entry.size:8d} -> {target}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract an EA BIGF archive")
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("extracted_big")
    )
    args = parser.parse_args()
    extract(args.archive, args.output)


if __name__ == "__main__":
    main()
