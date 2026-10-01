# MVP 07 Modding Suite

Reverse-engineering and roster tooling for **MVP 07: NCAA Baseball (PS2,
SLUS-21582)**. Updated **2026-10-01** after executable research.

## Current status

| Area | Status |
|---|---|
| BIGF extraction and RefPack decoding | Implemented; supplied database decoded and cross-file joins verified |
| Unified roster editor | Opens `DATABASE.BIG`, stock `roster.bin`, `.sav`, and PCSX2 save ZIPs |
| Stock team/roster layout | Confirmed: 152 playable teams plus sentinel; 25-slot disc / 30-slot save records |
| Player editing | DAT fields and mapped save names, general/appearance, all 27 batting fields and mapped pitching fields writable; unknown bits preserved |
| Lineups and rotation | Role packing and rotation indexes mapped; raw-role/rotation editing supported; hand-to-channel association still needs controlled verification |
| Writers | Experimental: structural round trips checked; modified game files have not been boot/gameplay tested |
| Executable research | Team serializer, runtime layout, roster/player/team/conference limits, ballpark tail and asset-loading paths mapped |\n| Stadium / 3D assets | BIG resource layout, 23 authentic + 10 generic packages, and VENU day/dusk/night member differences documented; ORD/ORL conversion not yet proven |
| 34-player rosters, added teams/conferences/assets | Hypotheses documented; executable patches, expanded editor profiles and game validation not implemented |

The executable has **30-slot runtime team storage**, a validation branch for
**26 or more roster players**, **4035-capacity general player pools**, and a
**16-conference constructor**. These are separate constraints. Removing the
25-slot Create-a-Player feature alone cannot supply the **5169 general records**
needed for 152 teams ×34 players plus a default record.

The accepted future direction is **34 game-generated players per team, editable
through the external roster editor**, with Create-a-Player removable. Generation
of additional complete player records still needs tracing; the existing save
proves name generation for stock players, not automatic expansion to 34.

## What was completed in this research pass

- Traced the executable's team/roster serialization and corrected the count,
  sentinel, padding and save-player layout explanations.
- Identified fixed roster loops, validation, player/pitcher pool capacities,
  team/conference initialization, role getters/setters, custom-ballpark data,
  logo formatting and uniform lookup constraints.
- Corrected batting array framing and percentage widths, recovered FB/LD/GB
  tendencies, and distinguished full serialized capacity from populated rows.
- Added a read-only ELF inspector with exact-build checks and a reproducible
  stock-profile verification tool.
- Updated the format and GUI notes; repaired malformed Python launcher/package
  newlines; removed a connectivity-test file and ignored caches/local game inputs.

Start with [the agent handoff](docs/research/handoff.md), then the
[full executable evidence and hypotheses](docs/research/executable.md).
Supporting maps: [DATABASE.BIG / roster.bin](docs/research/database_big_roster.md),
[memory-card save](docs/research/memory_card_roster.md), and
[GUI capabilities and limitations](docs/gui_roster_editor.md), and\n[stadium / 3D asset research](docs/research/stadium_3d_assets.md).

## Run the editor

Requires Python 3.10+ and Tkinter. No third-party packages are needed by the editor.
Some Linux installations package Tkinter separately as `python3-tk`.

```bash
python run_editor.py
```

Use a copy of the game files. The stock editor is not an expanded-roster editor:
it currently assumes 152 playable teams, 25 disc slots or 30 save slots, and the
analyzed save profile's table counts/offsets. Rebuilt BIG archives use valid
literal-only RefPack streams and can be larger than the originals.

For executable inspection, see the optional Capstone commands in the research
report. Originals and extracted game assets are not included in this repository.

## Future directions

1. Establish emulator baselines and validate edited stock files through load,
   play, save/reload and dynasty simulation.
2. Test realignment of one existing team; inspect `schedule.big` and downstream
   scheduling/bracket consumers.
3. Trace player/name creation, audit layout/count consumers, and test roster
   validation before coordinated 34-slot/player-pool expansion.
4. Add one team using existing assets, then test new logos/uniforms and one new
   conference before scaling.
5. Add explicit expanded-file profiles, lineup editing controls, player movement,
   change tracking and better compression to the editor.

## Research rules

Preserve originals and unknown bytes. Distinguish direct evidence, correlation,
hypotheses and runtime-tested behavior. Record executable hashes and virtual
addresses. A representable ID or one dynamic loader is not proof of an engine-wide
limit. Keep reproducible research and tooling; omit temporary dumps and duplicate
binaries. No global constant replacement or unsupported-field rewriting.
