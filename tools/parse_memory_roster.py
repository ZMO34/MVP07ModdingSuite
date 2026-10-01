#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mvp07_modding_suite.memory_save import MemoryRosterSave


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect an MVP 07 PS2 roster save")
    parser.add_argument("save", type=Path, help="Rost*.sav or PCSX2 save ZIP")
    parser.add_argument("--names", action="store_true", help="Print populated player-name records")
    args = parser.parse_args()

    save = MemoryRosterSave.load(args.save)
    print(f"team_base   = 0x{save.team_base:X}")
    print(f"player_base = 0x{save.player_base:X}")

    if args.names:
        for p in save.populated_player_names():
            print(f"{p.index:4d}  {p.first_name} {p.last_name}".rstrip())


if __name__ == "__main__":
    main()
