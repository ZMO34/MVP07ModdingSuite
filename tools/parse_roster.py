#!/usr/bin/env python3
"""Parse the confirmed static structure of decompressed MVP 07 roster.bin."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from refpack import decompress


GLOBAL_HEADER_SIZE = 491
TEAM_RECORD_SIZE = 687
TEAM_COUNT = 152
ROSTER_COUNT_OFFSET = 0x0C0
ROSTER_SLOTS_OFFSET = 0x0C4
ROSTER_SLOT_SIZE = 8
ROSTER_SLOTS = 25
STARTER_INDEX_OFFSET = 0x18C


@dataclass
class RosterSlot:
    player_id: int
    role_flags: int


@dataclass
class TeamRecord:
    index: int
    internal_name: str
    full_name: str
    abbreviation: str
    city: str
    nickname: str
    metadata_hex: str
    roster_count: int
    roster: list[RosterSlot]
    starter_indexes: list[int]


def _cstr(buf: bytes, offset: int, size: int) -> str:
    return buf[offset : offset + size].split(b"\0", 1)[0].decode("latin-1")


def parse_decompressed(data: bytes) -> tuple[bytes, list[TeamRecord]]:
    expected = GLOBAL_HEADER_SIZE + TEAM_COUNT * TEAM_RECORD_SIZE
    if len(data) != expected:
        raise ValueError(f"Expected {expected} decompressed bytes, got {len(data)}")

    header = data[:GLOBAL_HEADER_SIZE]
    teams: list[TeamRecord] = []

    for index in range(TEAM_COUNT):
        start = GLOBAL_HEADER_SIZE + index * TEAM_RECORD_SIZE
        rec = data[start : start + TEAM_RECORD_SIZE]

        roster_count = int.from_bytes(
            rec[ROSTER_COUNT_OFFSET : ROSTER_COUNT_OFFSET + 4], "little"
        )

        roster: list[RosterSlot] = []
        for slot in range(ROSTER_SLOTS):
            off = ROSTER_SLOTS_OFFSET + slot * ROSTER_SLOT_SIZE
            roster.append(
                RosterSlot(
                    player_id=int.from_bytes(rec[off : off + 4], "little"),
                    role_flags=int.from_bytes(rec[off + 4 : off + 8], "little"),
                )
            )

        teams.append(
            TeamRecord(
                index=index,
                internal_name=_cstr(rec, 0x000, 8),
                full_name=_cstr(rec, 0x008, 48),
                abbreviation=_cstr(rec, 0x038, 16),
                city=_cstr(rec, 0x048, 40),
                nickname=_cstr(rec, 0x070, 32),
                metadata_hex=rec[0x090:0x0C0].hex(),
                roster_count=roster_count,
                roster=roster,
                starter_indexes=list(
                    rec[STARTER_INDEX_OFFSET : STARTER_INDEX_OFFSET + 3]
                ),
            )
        )

    return header, teams


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("roster_bin", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw = args.roster_bin.read_bytes()
    data = decompress(raw) if len(raw) >= 2 and raw[1] == 0xFB else raw
    _, teams = parse_decompressed(data)

    if args.json:
        print(json.dumps([asdict(t) for t in teams], indent=2))
        return

    for team in teams:
        starters = ",".join(str(x) for x in team.starter_indexes)
        print(
            f"{team.index:3d} {team.internal_name:8} "
            f"{team.full_name:28} {team.abbreviation:5} "
            f"{team.city:20} {team.nickname:20} starters=[{starters}]"
        )


if __name__ == "__main__":
    main()
