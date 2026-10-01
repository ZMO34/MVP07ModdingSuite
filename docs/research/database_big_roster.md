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
| `+0xA0`, 12..20 | school-name audio selector | confirmed by CAT CSV consumer, getter/setter; equals logo ID in stock |
| `+0xA0`, 21..29 | nickname audio selector | confirmed: 152/152 exact nickname CSV joins and CAT consumer |
| `+0xA4`, 1..9 | primary team art ID used by logo formatting | confirmed |
| `+0xA4`, 10..18 and 19..27 | two further art/reference IDs, matching first in stock | values/getters confirmed; consumer distinctions unresolved |
| `+0xA4`, 0 | flag set only for BYU in sample | unknown meaning |
| `+0xA4`, 28..30 | value 1..7 | unknown meaning |
| `+0xA4`, 31 | zero in sample | unknown meaning |
| `+0xA8`, 4..9 | six-bit stadium selector | confirmed getter `0x6F7C30`, resolver `0x197D50` |

Stock art IDs skip 50 and extend through 153. Do not confuse IDs with the 153
serialized team records including the sentinel. Nine-bit encodings hold 0..511;
other consumers have narrower gates and capacities.

Division selector is set for the second named division in ACC (Atlantic), SEC
(West), and WCC (West); `conf.dat` provides the corresponding labels. Broader
league changes need schedule/dynasty evidence beyond these fields.

Remaining metadata:

- `+0xA8` contains several fields, not one nine-bit stadium ID. Accessors also
  extract bits 0..1, 2..3 and 13..17; their semantics remain unresolved.
- `+0xAC` is accessed as **eight three-bit fields**, grouped into two indexed
  channels of four: `0,6,12,18` at `0x6F7EB0` and `3,9,15,21` at `0x6F7E28`.
  The previous two-nine-bit-reference description was an arbitrary statistical
  partition, not executable evidence. Color/presentation semantics remain unknown.
- Serialized `+0x090` maps to runtime `+0x09C`. `0x6F7B78` reads it as four
  indexed bytes; `0x6F7B88` searches those bytes. Its 141 distinct DWORD values
  do **not** identify the school/nickname selectors. Exact meaning remains unknown.
- Serialized `+0x094..+0x09F` maps to runtime `+0x090..+0x09B`; there is a text
  getter at `0x6F7B40` and an 11-byte bounded setter at `0x6F7B48`. Stock contents
  are zero; the role of this optional string still needs tracing.
- Serialized bytes `+0xB0..+0xBF` are zero in stock; indexed DWORD getter/setter
  `0x6F7F90` / `0x6F7FA0` exist. Preserve these fields.

## DBMisc and announcer selectors: direct join (2026-10-01)

Inputs used in this pass:

| Input | SHA-256 |
|---|---|
| `DBMISC(2).BIG` (19,446 bytes) | `af546dc94ff61ad27f45587fa6079f928a34059cb4a73bc28013f76d8023c993` |
| `DATABASE.BIG` | `35f93770a501c47b85e9e8add380aa603adbdf9eb59e807fbdb30ba0b8f0d252` |
| decoded stock `roster.bin` | `1bdd417263ab9751583f5abbb930d314718684af2896a682ca5b445647d4724e` |

The DBMisc archive has nine **uncompressed** members. It mixes playable-team
metadata, Create-a-Team choices, and other configuration; it is not uniformly
legacy MLB data or uniformly Create-a-Team data.

| Member | Direct evidence / practical role |
|---|---|
| `teaminfo.csv` | 152 playable rows. Join by `Logo ID`: every row matches roster abbreviation, nickname, city and location. Abbreviations are not unique join keys. |
| `uniform.bin` | LE `u16` count 304, exactly `2 + 304*7` bytes; every key `(1..152, 0/1)` occurs once. Ordinal team keys differ from stock logo/school IDs after the gap at 50. Payload meanings and 0/1 home/away labels remain unproved. |
| `schoolnameaudio.csv` | 160 school-name choices with numeric IDs 201..360. Includes both playable and non-playable schools; not a cut-team inventory. |
| `nicknameaudio.csv` | 212 ID/name rows: 1..106 and 201..306. Extended real-college vocabulary 201..275 and generic names 276..306. |
| `logotable.csv` | Mixed-section CSV: Custom logo range 201..243, Alpha 244..269; 69 logo choices with default nicknames. Separate namespace from audio IDs. |
| `citystatetable.csv` | 60 city/state text choices, no numeric ID column. Not a direct `Location ID` dictionary; `location.dat` is the established roster location join. |
| `stadium.csv` | MLB abbreviations/park factors; no NCAA roster-to-stadium assignment established. |
| `challengeitems.csv`, `challenges.csv` | Present; challenge/config content outside this focused audio pass. |

For a LE DWORD `w` at team-record `+0xA0`:

```python
school_audio_id = (w >> 12) & 0x1FF
nickname_audio_id = (w >> 21) & 0x1FF
# Preserve every other bit if writing either field.
w = (w & ~0x001FF000) | ((school_audio_id & 0x1FF) << 12)
w = (w & ~0x3FE00000) | ((nickname_audio_id & 0x1FF) << 21)
```

**Nickname identification:** all **152/152** decoded selectors resolve to the
exact roster nickname string. There are 120 distinct IDs; 18 teams already use
IDs from 201..275. Thus extended nicknames are used by ordinary stock teams too.
Nevada is `100 = Wolf Pack`; `101 = Wolfpack` is a different entry. Removing
spaces while matching names creates a false mismatch; retain exact text.

**School identification:** all stock selectors occupy 1..153 except 50, and
match the stock logo ID for all 152 teams. That equality originally caused this
field to be described as another graphics reference. Executable CSV-to-setter
tracing identifies its separate school-audio role. None of the stock selectors
joins directly to the 201..360 CSV namespace. There are 19 exact-name overlaps
between stock schools and the CAT school list, with different IDs; additional
name variants exist. Never assign CAT IDs by assuming a stock school with the
same name already uses them.

| Team / intended name | Stock school call | CAT school call for same name | Nickname call |
|---|---:|---:|---|
| Georgia | 79 | absent | 19 Bulldogs |
| Appalachian State | 139 | 206 | 66 Mountaineers |
| Georgia Southern | 131 | 252 | 33 Eagles |
| Marshall | 102 | 278 | 271 Thundering Herd |
| Xavier | 153 | 357 | 246 Musketeers |
| Coastal Carolina (not a stock team) | — | 226 | 213 Chanticleers (available vocabulary) |

The last row is a proposed assignment from two dictionaries, not an encoded
school/nickname pairing or proof of a playable added team. CSV rows do not prove
that every audio clip is present or that normal-game commentary will play it.

Executable confirmation uses the matching `SLUS_215.82` hash in
[executable.md](executable.md):

1. String VAs `0x94A8D8` / `0x94A8F0` identify the two audio CSVs.
2. Calls at `0x787034` / `0x78704C` feed them to `0x7884A0`. This loader parses
   the first column as a decimal ID (`0x7885B0`), stores it before the string
   (`0x7885B8`), and advances in 68-byte ID/string records.
3. School rows are stored at the CAT object `+0x907C`; nickname rows at `+0x560C`.
   CAT application searches the nickname text and passes its ID to setter
   `0x6F7CA8` at `0x789940`, then searches school-name text and calls setter
   `0x6F7C70` at `0x7899A0`. A failed text match selects ID zero.
4. Getter/setter pairs are school `0x6F7C60/0x6F7C70` (shift 12, mask 511)
   and nickname `0x6F7C98/0x6F7CA8` (shift 21, mask 511). A team-info consumer
   at `0x1A91C4/0x1A91D0` reads them independently from logo getter `0x6F7CD0`.
5. Serializer `0x6B19D0` transfers runtime `+0xA0..+0xAF` unchanged to the
   same serialized offsets. The separate `+0x090` DWORD is not either selector.

Reproduce without modifying inputs:

```bash
python tools/analyze_team_audio.py /path/to/DATABASE.BIG /path/to/DBMISC.BIG --verify-stock
python tools/analyze_team_audio.py /path/to/roster.bin /path/to/DBMISC.BIG --verify-stock --json
python tools/inspect_elf.py /path/to/SLUS_215.82 verify
```

The analyzer also accepts the decoded stock roster and prints all 152 joins
with `--json`. These selectors are confirmed statically, **not playback-tested**.
No announcer GUI controls, audio-bank edits, or game patches were added here.
Next practical test: change one existing team's school call to CAT ID 226,
leaving its nickname/art/location intact; separately change only nickname to
213. The user rebuilds the ISO and checks load, matchup introduction, normal
commentary, and save/reload against an untouched baseline. This isolates ID
selection from bank/event coverage; it does not require team expansion.

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
