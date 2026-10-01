# DATABASE.BIG / roster.bin format

Updated 2026-10-01 with executable-backed corrections. Applies to the supplied
stock database; expanded databases are not implemented. Executable addresses,
limits, evidence levels and reproduction commands are in [executable.md](executable.md).

## Archive

`DATABASE.BIG` is 518,251 bytes (`0x7E86B`), SHA-256
`35f93770a501c47b85e9e8add380aa603adbdf9eb59e807fbdb30ba0b8f0d252`.
It has BIGF magic, ten members, a 217-byte directory/header, and aligned data
starting at byte 220 (`0xDC`).

| Directory field | Encoding |
|---|---|
| bytes 4..7, archive length | little-endian u32 |
| bytes 8..11, member count | big-endian u32 |
| bytes 12..15, directory/header length | big-endian u32 |
| member entry | big-endian u32 offset, big-endian u32 size, NUL-terminated name |

| File | Offset | Compressed bytes | Decoded bytes |
|---|---:|---:|---:|
| location.dat | `0xDC` | 1470 | 3272 |
| conf.dat | `0x69C` | 563 | 1235 |
| team.dat | `0x8D0` | 3 | plain `;\r\n` |
| tstat.dat | `0x8D4` | 2281 | 7068 |
| default.dat | `0x11C0` | 174 | 504 |
| roster.bin | `0x1270` | 35964 | 104915 |
| pitcher.dat | `0x9EEC` | 71115 | 275980 |
| rhattrib.dat | `0x1B4B8` | 101744 | 642883 |
| lhattrib.dat | `0x34228` | 102908 | 643126 |
| attrib.dat | `0x4D424` | 201799 | 1023951 |

Populated members use EA RefPack/QFS. `roster.bin` begins `10 FB 01 99 D3`:
RefPack signature followed by 24-bit big-endian uncompressed length 104915.
Fragmented strings in compressed data were literals interrupted by backrefs,
not a non-byte-aligned custom format. `tools/refpack.py` decodes these streams;
`tools/extract_big.py` extracts original members without interpretation.

The decoded DATs are text schema/data tables. Nine-character hex row keys fit
in u32 and join numeric roster player IDs to general, LH/RH batting and pitcher
rows. `attrib.dat` has a default plus 3800 roster-player rows; `pitcher.dat` has
1609 stock rows. `team.dat` is empty, so adding text rows there alone does not
add the binary team records. Conference records live in `conf.dat` (16 rows).

## Top-level roster framing: confirmed

| Offset | Bytes | Meaning |
|---:|---:|---|
| `0x000` | 4 | little-endian total serialized team-record count, 153 |
| `0x004` | 487 | empty sentinel team record, roster count zero |
| `0x1EB` | `152*687` | 152 playable team records, 25 slots each |

`4 + 487 + 152*687 = 104915`, with no unexplained tail. The previous description
of the first 491 bytes as an unknown "global region" is superseded: the team
serializer at `0x6B19D0` and table serializer at `0x6B1CC0` establish count and
sentinel framing. Preserve both; current stock parsers still treat them together
as a 491-byte prefix. Table record 0 is the sentinel; editor/playable index 0
is Arizona State, table record 1.

## Serialized playable team record: 687 bytes

| Offset | Bytes | Meaning / evidence |
|---:|---:|---|
| `0x000` | 8 | internal team key |
| `0x008` | 48 | full school/team name |
| `0x038` | 16 | abbreviation |
| `0x048` | 40 | city |
| `0x070` | 32 | nickname |
| `0x090` | 48 | packed metadata, partially mapped |
| `0x0C0` | 4 | little-endian slot count, 25 in all playable stock records |
| `0x0C4` | 200 | 25 slots ×8 bytes |
| `0x18C` | 3 | three starting-pitcher slot indexes |
| `0x18F` | 288 | custom-ballpark-associated block; zero in stock sample |

The last block starts at `0x18F`; there is no separately serialized padding
byte there. Runtime layout differs and has one omitted padding byte before the
block. The tail's subsystem association is proven through team accessors and
custom-ballpark initialization/debug strings; every byte's meaning is not mapped.
Do not use it as free roster storage. See the complete runtime/serialized map
in [executable.md](executable.md).

Strings are fixed buffers containing NUL-terminated Latin-1/ASCII values.
Bytes after the terminator need not be zero in runtime saves. Writers clear
only an edited string buffer; untouched content is preserved.

Examples: playable index 0 = `ArizSt / Arizona State / ASU / Tempe / Sun Devils`;
index 1 = `ArkSt / Arkansas State / ASU / Jonesboro / Indians`.

## Roster slots and lineup roles

Each slot at `0x0C4 + 8*s` contains a little-endian u32 player ID and a role
DWORD. All 3800 stock slots join `attrib.dat`, `lhattrib.dat` and `rhattrib.dat`;
pitchers additionally join `pitcher.dat`. Arizona State slot 0 has ID
`0xC186D538` (bytes `38 D5 86 C1`), DAT row index 526.

The three bytes at `0x18C..0x18E` are slot indexes 0..24. Across all 152 teams,
the three referenced players have primary position 0, 456 starters total.
Executable rotation setters additionally establish the three-index design.

| Role bits | Meaning | Status |
|---|---|---|
| 0..3 | defense channel/selector 0 | confirmed getter/setter |
| 4..7 | defense channel/selector 1 | confirmed getter/setter |
| 8..14 | batting order: decimal tens/ones pair | confirmed getter/setter; selector 0 tens, 1 ones |
| 15..17 | pitching-role value | confirmed width/accessor; some labels unresolved |
| 18..20 | additional field | confirmed width/accessor; semantics unresolved |
| 21..31 | remaining bits | incompletely mapped; preserve |

Examples: `0x2C33` means batting pair 44 (4/4), defense 3/3; `0x4D44`
means 77 (7/7), defense 4/4; `0x3C0A` means 60 (6/0), defense 10/0.
All stock defensive nibbles are 0..10 and batting pairs 0..99. Different channels
explain values that the earlier equal-digit heuristic could not decode.

The user describes default and secondary lineups as vs RHP/vs LHP. The stored
channels are proven, but mapping engine selector numbers to pitcher hand still
needs a controlled unequal-channel comparison. Do not infer it from equal values.

Stock upper-role buckets: 0 ordinary/bench; `0x8000` starters (all 456);
`0x10000` and `0x18000` relief groups; `0x28000` likely closer (one/team in 147
teams, two in five). Relief labels and closer interpretation are correlations,
not completed UI-diff proof. Bits 18..20 being zero in stock does not mean unused.
The earlier stamina comparison suggests `0x10000` may represent long relief and
`0x18000` middle relief; retain these as candidate labels until controlled tests.

## Packed team metadata

These fields are at serialized offsets and are independently consistent with
DAT rows. The executable accessors confirm the location/conference/division widths.

| Word / bits | Interpretation | Status |
|---|---|---|
| `+0xA0`, 0..5 | location ID, 1..49 observed | confirmed |
| `+0xA0`, 6..10 | conference ID, 1..16 observed | confirmed |
| `+0xA0`, 11 | conference division selector | confirmed |
| `+0xA0`, 12..20 | nine-bit reference matching primary art ID in stock | value correlation confirmed; separate consumer semantics incomplete |
| `+0xA0`, 21..29 | another nine-bit reference | getter identified; final meaning unresolved |
| `+0xA4`, 1..9 | primary team art ID used by logo formatting | confirmed |
| `+0xA4`, 10..18 and 19..27 | two further art/reference IDs, matching first in stock | values/getters confirmed; consumer distinctions unresolved |
| `+0xA4`, 0 | flag set only for BYU in sample | unknown meaning |
| `+0xA4`, 28..30 | value 1..7 | unknown meaning |
| `+0xA4`, 31 | zero in sample | unknown meaning |

Stock art IDs skip 50 and extend through 153. Do not confuse IDs with the 153
serialized team records including the sentinel. Nine-bit encodings hold 0..511;
other consumers have narrower gates and capacities.

Division selector is set for the second named division in ACC (Atlantic), SEC
(West), and WCC (West); `conf.dat` provides the corresponding labels. Broader
league changes need schedule/dynasty evidence beyond these fields.

Still-unlabeled correlations worth preserving for future research:

- `+0xA8` is a nine-bit ID, 52 distinct stock values.
- `+0xAC` holds two nine-bit IDs: 17 distinct low values and 21 high values;
  bits 18..31 are zero in stock. Audio/presentation/color references are hypotheses.
- Serialized `+0x090` has 141 distinct values across 152 teams; announcer/stadium
  hash/reference is a hypothesis. It corresponds to runtime `+0x09C`, not `+0x090`.
- Serialized bytes `+0xB0..+0xBF` are zero in all stock records; still preserve them.

## Tooling and continuation

Stock read and experimental write paths exist in `src/mvp07_modding_suite/model.py`
and `documents.py`. CLI parser `tools/parse_roster.py` uses the same stock sizes.
Preserve unknown bytes and count/sentinel framing, modify decompressed content,
recompress and rebuild aligned BIGF entries. Compressed bytes need not match the
original as long as decoded content matches. Literal-only compression is larger
and has not been validated in-game.

Remaining work: establish edited-file runtime compatibility, confirm lineup hand
labels and unresolved metadata, inspect graphics/scheduling archives, and build
explicit expanded profiles after executable/serializer changes are proven.
