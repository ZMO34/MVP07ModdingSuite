# Agent handoff: executable expansion research

Updated **2026-10-01**. Repository: `ZMO34/MVP07ModdingSuite`, branch `main`.
Start here to continue without relying on previous chat history.

## User objective and accepted tradeoff

Research hypotheses for adding playable team records, new team graphics,
conference realignment/expansion, and **34 players/team**. The user accepts
removing Create-a-Player/menu functionality and prefers game-generated players
that can be edited externally. This pass was research and factual documentation,
not implementation of expansion patches. The user requested all necessary
findings/status/future directions on GitHub and removal of unneeded clutter.

## Read order and evidence ownership

1. [Executable research](executable.md): exact input hashes, ELF mapping, named
   address inventory, serializers, layouts, hard limits, asset paths, hypotheses,
   missing artifacts and staged runtime experiments. This is the executable source of truth.
2. [Disc database format](database_big_roster.md): BIGF/RefPack directory and
   stock team/sentinel/role/metadata maps.
3. [Memory save](memory_card_roster.md): physical array framing, populated versus
   serialized counts, ID joins, strings and profile caveats.
4. [Player fields](save_player_format.md): exact general, batting and pitcher
   bit maps plus confidence levels for appearance interpretations.
5. [Editor status](../gui_roster_editor.md): supported backends, implemented
   fields, fixed-profile assumptions and runtime testing gaps.

Use the executable SHA-256 in the report to relocate addresses in other builds.
The supplied executable duplicates were identical. The game originals, extracted
DATs, save ZIP and disassembly dumps are excluded from Git. A future agent needs
matching local inputs or user-provided originals; documentation is sufficient to
reproduce the research but does not include copyrighted game data.

## Most consequential confirmed findings

- Team table framing includes a sentinel: count 153 = sentinel + 152 playable
  teams. Stock prefix =4+487; save count/sentinel/first playable offsets are
  `0x1DE8`/`0x1DEC`/`0x20C3`.
- Runtime team stride 728; serialized length `487+ 8*n` gives 687 (25) and
  727 (30). Metadata DWORD ordering differs between runtime and serialization.
- Fixed runtime storage/search loops use 30. A validation branch distinguishes
  counts >=26. Increasing only a serialized count would overwrite later fields.
- The tail at runtime `+0x1B4` / stock `+0x18F` / save `+0x1B7` belongs to
  custom-ballpark data; it is not a lineup array or safe spare storage.
- General/LH/RH full allocated **and serialized** arrays have 4035 rows; 3826
  are populated (Default + 3800 stock + 25 CAP), followed by 209 zero rows.
  Pitcher array has 1650 full rows, 1634 populated, then 16 zero rows.
- Correct batting physical bases are `0x7F007` / `0x8EC3B`, four bytes after
  former anchors. All percentage fields are seven bits; FB/LD/GB are recovered.
  Existing previously mapped fields keep the same absolute positions after
  both base and relative-bit corrections.
- General records are attributes-first at `0x2C407`; `player_base` in the current
  API is the name anchor `0x2C43F`. Keep those coordinate systems distinct.
- CAP initialization explicitly loops 25 created-player IDs. All 25 reserve IDs
  join general indexes 3801..3825 to pitcher indexes 1609..1633.
- 34×152 +Default =5169 general rows with CAP removed, exceeding 4035 by 1134.
  Removing CAP alone is insufficient. Actual creation of nine extra fully
  attributed players/team has not been traced; name generation alone is not enough.
- Team serialization can iterate a dynamic count, but initialization and other
  consumers contain153. Conference IDs are five bits, while the constructor
  provisions16. Membership enumeration uses metadata; schedules remain unverified.
- Logo paths format `../logos/a%03d.swf` from art ID. Uniform mapping uses
  seven-byte entries, byte-sized keys, and a local `<154` lookup gate.
  Those encoding/gate facts do not establish a global supported team maximum.

## Implemented changes in this pass

- Added `tools/inspect_elf.py`: ELF info, string search, direct call search,
  candidate address xrefs, partial R5900-aware disassembly, and exact-build
  verification of **35 instruction fingerprints**. It is read-only.
- Added `tools/verify_stock.py`: supplied-profile cross-file, table framing,
  reserve joins, decoded/no-change round trips and independent mask-preservation checks.
- Corrected batting bases, seven-bit percentage widths, and added FB/LD/GB
  mappings in `memory_save.py`; exposed the three recovered fields in the GUI.
  Added explicit full-capacity constants without exposing unpopulated reserves.
- Corrected documentation/API comments on sentinel framing, packed attributes,
  lineup hand-label uncertainty, array counts and bases. Preserved newer upstream
  `save_player_format.md` research and reconciled its conflicting claims.
- Fixed literal backslash-n syntax corruption in `run_editor.py` and package
  `__init__.py`. Added a normal guarded launcher.
- Removed `.github/chatgpt-write-test.txt`, a connectivity probe. Added ignores
  for Python caches, local inputs/extracted outputs and game binaries. Useful
  research stays in the repository; duplicate binaries/dumps/caches are excluded.

## Validation performed

Run on the exact supplied inputs; all checks passed:

```bash
python -m compileall -q src tools run_editor.py
python tools/inspect_elf.py /path/to/SLUS_215.82 verify
python tools/verify_stock.py /path/to/DATABASE.BIG /path/to/BASLUS-21582R659be98.zip
```

The stock verification covers:

- count/sentinel framing; all 152 visible team strings, metadata, first 25 slots,
  five empty save slots, rotation indexes and ballpark-associated tails;
- **3801** general and **3801 per side** batting rows, all mapped fields;
- **1609** pitcher rows, including Default;
- documented sentinels:14 bunting `-1` + 8 bunting `-2` -> 0; 1152 absent fifth pitches
  have `-` DAT parameters ->packed zero;
- 25 CAP general-to-pitcher ID joins; full serialized capacities/table headers
  and 209/16 zero reserve records;
- raw save byte identity, all ZIP member-content identity, all BIG decoded-member
  identity, stock `roster.bin` decoded identity and successful reopening;
- **122 field-write checks**: 43 general, 27 LH, 27 RH, 25 pitcher; readback and
  unchanged unrelated bits/adjacent bytes, including duplicated pitcher stamina.

Source/import checks are not a GUI interaction test. The GUI has not been
interactively tested in this execution environment. There is no modified-game
boot/gameplay/save-reload/dynasty test, expansion patch, new-team texture,
complete scheduling-archive map or proven save checksum procedure.

## Immediate next work

Begin with an unmodified PCSX2 baseline and edited-stock load/save tests.
Realigning one existing team is the smallest expansion-related experiment.
For 34-player work, trace the active-player validator, name/player registration,
all team layout consumers, 4035/1650 pools and save transfers before choosing
an inline34-slot redesign. Keep ballpark data and all save headers intact.
For teams/conferences, audit 153/16 consumers and acquire the schedule/art/uniform
archives. See the report's ordered experiments and candidate 34-slot offsets.

Unresolved field labels: batting/defense selector-to-pitcher-hand association,
relief categories, additional role bits, body-type transform, visual appearance
enums, some metadata/art copies, custom-ballpark trailing24 bytes, uniform key
semantics, full ID-table framing and overall memory/menu/dynasty limits.

Do not resume from superseded claims: 723-byte team serialization, unknown 491-byte
global header, 4096-player save array, 3826 as full serialized capacity, 16-byte
batting records starting at the old anchors, four lineup arrays in the tail,
or nine-bit art IDs as proof of 511 working teams.
