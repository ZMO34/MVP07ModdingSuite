# MVP 07 Modding Suite

Reverse-engineering and roster tooling for **MVP 07: NCAA Baseball (PS2,
SLUS-21582)**. Updated **2026-10-01**.

## Current status

| Area | Status |
|---|---|
| BIGF extraction and RefPack decoding | Implemented; supplied database decoded and cross-file joins verified |
| Unified roster editor | Opens `DATABASE.BIG`, stock `roster.bin`, `.sav`, and PCSX2 save ZIPs |
| Editor usability | Redesigned three-pane UI with search/filter, scrollable forms, validation, enum drop-downs/autocomplete, dirty-state tracking and Undo/Redo |
| CSV | Full-roster CSV export/import for supported team, role, rotation and mapped player fields; player IDs are guarded against accidental reassignment |
| Starting rotation | Dedicated three-starter UI using player-name selectors; no raw comma-separated index entry required |
| Stock team/roster layout | Confirmed: 152 playable teams plus sentinel; 25-slot disc / 30-slot save records |
| Player editing | DAT fields and mapped save names, general/appearance, all 27 batting fields and mapped pitching fields writable; unknown bits preserved |
| Lineups | Role packing is mapped and displayed; direct graphical batting/defensive lineup editing is still pending |
| Writers | Experimental: structural round trips checked; modified game files have not been boot/gameplay tested |
| Executable research | Team serializer, runtime layout, roster/player/team/conference limits, ballpark tail and asset-loading paths mapped |
| Stadium / 3D assets | BIG resource layout, 23 authentic + 10 generic packages, and VENU day/dusk/night member differences documented; ORD/ORL conversion not yet proven |
| 34-player rosters, added teams/conferences/assets | Hypotheses documented; executable patches, expanded editor profiles and game validation not implemented |

The executable has **30-slot runtime team storage**, a validation branch for
**26 or more roster players**, **4035-capacity general player pools**, and a
**16-conference constructor**. These are separate constraints. Removing the
25-slot Create-a-Player feature alone cannot supply the **5169 general records**
needed for 152 teams × 34 players plus a default record.

The accepted future direction is **34 game-generated players per team, editable
through the external roster editor**, with Create-a-Player removable. Generation
of additional complete player records still needs tracing; the existing save
proves name generation for stock players, not automatic expansion to 34.

## Roster editor

The current editor is intended to be usable without exposing the reverse-
engineering details for routine roster work.

Highlights:

- searchable team list
- searchable roster table
- readable field labels
- editable drop-downs for appropriate enum-style fields
- keyboard autocomplete for drop-downs, including handedness
- field-range validation before writes
- dedicated starting-rotation editor
- CSV import/export
- Undo/Redo history
- unsaved-change indicator and close/open protection
- scrollable Player, vs RHP, vs LHP, Pitching and Appearance forms
- Advanced tab for raw save diagnostics

CSV details are documented in
[docs/csv_roster_format.md](docs/csv_roster_format.md). GUI capabilities and
remaining limitations are tracked in
[docs/gui_roster_editor.md](docs/gui_roster_editor.md).

## Research completed

- Traced executable team/roster serialization and corrected count, sentinel,
  padding and save-player layout explanations.
- Identified fixed roster loops, validation, player/pitcher pool capacities,
  team/conference initialization, role getters/setters, custom-ballpark data,
  logo formatting and uniform lookup constraints.
- Corrected batting array framing and percentage widths and recovered FB/LD/GB
  tendencies.
- Added a read-only ELF inspector with exact-build checks and a reproducible
  stock-profile verification tool.
- Mapped `DATABASE.BIG` / `roster.bin`, the analyzed memory-card roster save,
  player packed fields, stadium packages and major executable consumers.

Start with [the agent handoff](docs/research/handoff.md), then the
[full executable evidence and hypotheses](docs/research/executable.md).

Supporting maps:

- [DATABASE.BIG / roster.bin](docs/research/database_big_roster.md)
- [memory-card save](docs/research/memory_card_roster.md)
- [save player format](docs/research/save_player_format.md)
- [stadium / 3D assets](docs/research/stadium_3d_assets.md)

## Run the editor

Requires Python 3.10+ and Tkinter. The editor has no third-party runtime
dependencies. Some Linux distributions package Tkinter separately as
`python3-tk`.

```bash
python run_editor.py
```

Use a copy of game/save files. The stock editor is not an expanded-roster
editor: it currently assumes 152 playable teams, 25 disc slots or 30 save
slots, and the analyzed save profile's table counts/offsets.

Rebuilt BIG archives currently use valid literal-only RefPack streams and can be
larger than the originals.

## Useful checks

```bash
python -m compileall -q src tools run_editor.py
python -m unittest discover -s tests -v
```

For executable inspection, see the optional Capstone commands in the research
report. Originals and extracted game assets are not included in this repository.

## Immediate directions

1. Validate ordinary edited stock files in PCSX2 through load, gameplay,
   save/reload and dynasty simulation.
2. Add direct batting-order and defensive-alignment controls using the already
   mapped role packing.
3. Add explicit player move/swap workflows.
4. Continue controlled roster/executable work before attempting 34-player or
   team-expansion profiles.
5. Improve RefPack compression and graphical/stadium workflows after the stock
   editor path is proven in-game.

## Research rules

Preserve originals and unknown bytes. Distinguish direct evidence, correlation,
hypotheses and runtime-tested behavior. Record executable hashes and virtual
addresses. A representable ID or one dynamic loader is not proof of an
engine-wide limit. Keep reproducible research and tooling; omit temporary dumps
and duplicate binaries. No global constant replacement or unsupported-field
rewriting.
