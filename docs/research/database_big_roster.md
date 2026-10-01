# DATABASE.BIG / roster.bin reverse-engineering notes

Date: 2026-10-01

## Source artifact

Analyzed user-supplied `DATABASE.BIG`.

- Archive magic: `BIGF`
- Archive byte length: `518251` (`0x7E86B`)
- File count: `10`
- Header/table declared length: `217` bytes
- Data begins at offset `220` (`0xDC`), with 4-byte alignment after the directory.

BIGF directory details:
- bytes 0x04..0x07: archive size, little-endian
- bytes 0x08..0x0B: file count, big-endian
- bytes 0x0C..0x0F: directory/header length, big-endian
- each entry: big-endian u32 offset + big-endian u32 size + NUL-terminated filename

## Archive directory

| File | Offset | Hex | Compressed size | Decompressed size |
|---|---:|---:|---:|---:|
| location.dat | 220 | 0xDC | 1470 | 3272 |
| conf.dat | 1692 | 0x69C | 563 | 1235 |
| team.dat | 2256 | 0x8D0 | 3 | n/a (plain `;\r\n`) |
| tstat.dat | 2260 | 0x8D4 | 2281 | 7068 |
| default.dat | 4544 | 0x11C0 | 174 | 504 |
| roster.bin | 4720 | 0x1270 | 35964 | 104915 |
| pitcher.dat | 40684 | 0x9EEC | 71115 | 275980 |
| rhattrib.dat | 111800 | 0x1B4B8 | 101744 | 642883 |
| lhattrib.dat | 213544 | 0x34228 | 102908 | 643126 |
| attrib.dat | 316452 | 0x4D424 | 201799 | 1023951 |

## Critical discovery: RefPack/QFS

**CONFIRMED:** `roster.bin` and every populated database `.dat` member are EA
RefPack/QFS compressed, not custom 7-bit or non-byte-aligned data.

Observed header for `roster.bin`:
- `10 FB`: RefPack signature/flags
- `01 99 D3`: 24-bit big-endian uncompressed length = `104915`
- compressed command stream begins immediately after the 5-byte header

The apparently fragmented strings seen in the compressed bytes were RefPack
literal data separated by LZ-style back-reference commands.

The RefPack decoder is implemented in `tools/refpack.py`.

## Decompressed companion DAT files

**CONFIRMED:** `attrib.dat`, `rhattrib.dat`, `lhattrib.dat`, `pitcher.dat`,
`location.dat`, `conf.dat`, `tstat.dat`, and `default.dat` decompress to
plain text database tables.

Examples:
- `attrib.dat` schema exposes jersey number, bats/throws, primary/secondary
  position, height, weight, year, appearance, speed, fielding, arm ratings,
  batting stance, scholarship, attitude, academics, etc.
- `pitcher.dat` exposes stamina, pickoff and individual pitch attributes.
- `rhattrib.dat` / `lhattrib.dat` expose batting attributes and tendencies.
- Row keys are 9-character hexadecimal IDs whose numeric value fits in u32.

This means the player ID in `roster.bin` can be joined directly to the player
rows in the four attribute tables.

## Decompressed roster.bin layout

**CONFIRMED:** decompressed size is exactly `104915` bytes.

The structure is:

```
0x00000 .. 0x001EA   491-byte global/header region
0x001EB .. EOF       152 team records * 687 bytes
```

Proof:

```
491 + (152 * 687) = 104915
```

There is no unexplained tail.

EA's own product information states the game contains 152 playable teams, which
matches the record count exactly.

### Team record: 687 bytes

Offsets below are relative to the start of each team record.

| Offset | Size | Meaning | Status |
|---:|---:|---|---|
| 0x000 | 8 | internal team key, NUL padded | CONFIRMED |
| 0x008 | 48 | full school/team name, NUL padded | CONFIRMED |
| 0x038 | 16 | abbreviation, NUL padded | CONFIRMED |
| 0x048 | 40 | city, NUL padded | CONFIRMED |
| 0x070 | 32 | nickname/mascot, NUL padded | CONFIRMED |
| 0x090 | 48 | team metadata, not fully mapped | UNKNOWN |
| 0x0C0 | 4 | roster count (little-endian u32), always 25 | CONFIRMED |
| 0x0C4 | 200 | 25 roster slots * 8 bytes | CONFIRMED |
| 0x18C | 3 | roster-slot indexes of the three starting pitchers | CONFIRMED |
| 0x18F | 1 | zero/padding | CONFIRMED |
| 0x190 | 287 | zero-filled reserved region in all 152 stock records | CONFIRMED |

Example record 0:
- internal key: `ArizSt`
- full name: `Arizona State`
- abbreviation: `ASU`
- city: `Tempe`
- nickname: `Sun Devils`

Record 1:
- `ArkSt`
- `Arkansas State`
- `ASU`
- `Jonesboro`
- `Indians`

### Roster slot: 8 bytes

At team-relative `0x0C4 + slot*8`:

| Offset in slot | Size | Meaning | Status |
|---:|---:|---|---|
| +0x0 | 4 | player database ID, little-endian u32 | CONFIRMED |
| +0x4 | 4 | roster/lineup/role flags | PARTIALLY MAPPED |

All 3,800 stock roster slots (`152*25`) use IDs found in `attrib.dat`.
The same IDs join to the left/right batting tables; pitcher IDs also join to
`pitcher.dat`.

Arizona State example: slot 0 contains bytes `38 D5 86 C1`, interpreted
little-endian as player ID `0xC186D538`, which exists in `attrib.dat`.

### Starting rotation indexes

Bytes `0x18C`, `0x18D`, and `0x18E` are each values from 0..24 and index
the team's 25 roster slots.

**CONFIRMED:** for every one of the 152 teams, all three indexed players have
`playerattrib_primaryposition = 0`. There are exactly three such players per
team (456 total), so these bytes encode the game's three-man college starting
rotation. Byte `0x18F` is zero in every stock record.

### Roster-slot flags (+4)

The second u32 in each 8-byte roster slot is clearly structured and correlates
with player role/position, but its exact bit/nibble meanings are not fully
decoded yet.

Strong observations:
- primary-position 0 players (the three starters) commonly use `0x00008011`
- other pitcher-role records (primary position 10) commonly use
  `0x00010000`, `0x00018000`, or `0x00028000`
- position-player values include patterned values such as `0x2C33`,
  `0x0B88`, `0x2155`, `0x5866`, `0x6322`, etc.
- zero is common for bench/non-lineup players

Current interpretation: this u32 stores lineup/defensive/role assignment rather
than player identity. Preserve it losslessly until each subfield is proven.

## Remaining unknown team metadata

Team-relative bytes `0x090..0x0BF` (48 bytes) vary by team and contain compact
metadata. They likely include one or more IDs/assets/conference/uniform/stadium
references. These fields are the next static-mapping target.

## Header/global region

The first 491 decompressed bytes precede team record 0. Its purpose is not yet
fully mapped. It includes structured binary values plus a large zero-filled
area. It must be preserved byte-for-byte until understood.

## Tooling / implementation rules

1. Extract the BIG archive losslessly.
2. RefPack-decompress members before interpreting them.
3. Never edit compressed offsets directly.
4. Join roster player IDs to DAT rows using the numeric hex row key.
5. Preserve unknown metadata/flags and the 491-byte global region.
6. When writing later, rebuild the decompressed structure, RefPack-compress it,
   then rebuild `DATABASE.BIG` with correct offsets/alignment.
7. Recompression does not need to reproduce the original compressed byte stream;
   it must only produce valid RefPack that decompresses identically.

## Evidence levels

- **CONFIRMED**: directly demonstrated by deterministic decoding/cross-file joins.
- **PARTIALLY MAPPED**: structure is known but individual subfields are incomplete.
- **UNKNOWN**: preserve as opaque bytes.

## Next targets

1. Decode team metadata at `0x090..0x0BF`.
2. Decode the roster-slot role/lineup u32 at slot offset +4.
3. Map primary/secondary position enum values.
4. Determine the 491-byte global header.
5. Add RefPack compression and BIGF rebuild support after the read path is fully
   validated.


## 2026-10-01 additional static findings

### Team metadata: repeated 9-bit asset ID

**CONFIRMED:** team-relative bytes `0x0A4..0x0A7` are a packed little-endian
u32 containing three repeated copies of the same 9-bit team asset ID:

- bits 1..9: asset ID copy 1
- bits 10..18: asset ID copy 2
- bits 19..27: asset ID copy 3
- bit 0: separate flag (set only for BYU in the stock database)
- bits 28..30: separate 3-bit value in the range 1..7
- bit 31: zero in all stock records

The three 9-bit copies agree for every team.

Asset-ID sequence:
- roster records 1..49 encode IDs 1..49
- roster record 50 encodes ID 51
- subsequent records continue through ID 153

Therefore asset ID 50 is deliberately reserved/skipped. The meanings of bit 0
and bits 28..30 remain unknown and must not yet be labeled in the GUI.

### Roster-slot role flags: common starting-lineup patterns

**PARTIALLY MAPPED:** for ordinary starting position players, the low byte often
contains two identical nibbles equal to `primary_position + 1`:

- position 1 -> `0x22`
- position 2 -> `0x33`
- ...
- position 9 -> `0xAA`

The next byte commonly takes one of nine values:

`0x0B, 0x16, 0x21, 0x2C, 0x37, 0x42, 0x4D, 0x58, 0x63`

These map empirically to batting-order slots 1..9 respectively. Examples include
`0x0B88`, `0x2C33`, `0x5866`, and `0x6322`.

Not every starter uses the simple form; several teams contain alternate values
such as `0x1403`, `0x230`, `0x4603`, etc. This strongly suggests the u32
contains multiple lineup/role assignments (likely split/platoon configurations)
rather than one simple position+order pair. The GUI may display the simple
inference but must preserve the complete raw u32.

### Global prefix

The 491-byte prefix is almost entirely zero. Only the first four bytes are
non-zero: little-endian u32 `153`. This matches the maximum encoded team asset
ID (153) and is consistent with an ID-space/count sentinel, but the exact
semantics are still not proven.

### First GUI/editor implementation

A first GUI implementation now lives under `src/mvp07_modding_suite/`.

It can:
- open the original `DATABASE.BIG`
- browse 152 teams and 25-player rosters
- join player IDs to the four attribute tables
- edit confirmed team strings and selected player attributes
- show raw role flags plus safe batting-order inference
- rebuild the BIG archive and verify that the rebuilt file can be parsed again

The current writer uses literal-only valid RefPack streams. This is structurally
verified but still requires an ISO/game runtime test before being considered
production-safe.
