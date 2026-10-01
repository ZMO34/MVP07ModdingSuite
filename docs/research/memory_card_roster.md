# PS2 memory-card roster save

Updated 2026-10-01. Applies to the supplied default roster save after the user's
reported random-name generation prompt. This is a separate binary serialization
backend from the compressed text DATs on disc.

## Source and evidence

ZIP: `BASLUS-21582R659be98.zip`. Roster member:
`BASLUS-21582R659be98/Rost1.sav`, 1,185,992 bytes, SHA-256
`34dd9c930dc56eae194729b9b254451c39d721b18863a0336611e57e36415556`.

This save contains runtime team and packed player data, not just a name overlay.
It independently validates roster IDs, team strings/metadata, roles and rotations.
The [executable map](executable.md) explains serializers and runtime capacities;
[save_player_format.md](save_player_format.md) lists individual packed fields.

## Team framing

| File offset | Meaning |
|---:|---|
| `0x1DE8` | little-endian total team-record count 153 |
| `0x1DEC` | sentinel team record, 727 bytes, count 30 |
| `0x20C3` | first of 152 playable team records |
| `0x1D06B` | end of playable team block (`0x20C3 + 152*727`) |

The save sentinel contains nonzero slot bytes; preserve it. The editor indexes
only the playable records. It does not regenerate the sentinel or other headers.

### Serialized playable team: 727 bytes

| Relative offset | Bytes | Meaning |
|---:|---:|---|
| `0x000` | 8 | team key |
| `0x008` | 48 | school/team name |
| `0x038` | 16 | abbreviation |
| `0x048` | 40 | city |
| `0x070` | 32 | nickname |
| `0x090` | 48 | partially mapped team metadata |
| `0x0C0` | 4 | serialized roster slot count, 30 |
| `0x0C4` | 240 | 30 eight-byte roster slots |
| `0x1B4` | 3 | starting-pitcher slot indexes |
| `0x1B7` | 288 | custom-ballpark-associated block |

There is no separately serialized padding at `0x1B7`; runtime padding is omitted.
The 30-slot serialized record is 727 bytes; runtime team stride is 728.
Five extra slots explain the 40-byte increase from the 687-byte stock disc record.

Across the 152 teams, visible strings, metadata `0x090..0x0BF`, first 25 slots,
and the three rotation indexes match the supplied disc database. Count changes
25 ->30; save slots 25..29 are zero in this default sample. This is storage
capacity, not evidence that the game accepts 30 active players: executable
validation distinguishes counts >=26.

## General player records

The physical array begins at **`0x2C407`**. Its **3826 populated records ×84 bytes**
end at **`0x7AB6F`**. The full serialized array has **4035 records**, ending at
**`0x7F003`**, with 209 zero surplus records. The Default first-name anchor is **`0x2C43F`**,
56 bytes into record 0. Earlier claims of 4096 name-first records are superseded;
they would misinterpret following data and overlap known later structures.

| Relative offset | Bytes | Meaning |
|---:|---:|---|
| `0x00` | 56 | packed general attributes |
| `0x38` | 12 | first-name buffer |
| `0x44` | 16 | last-name buffer |

Indexes: 0 Default template; 1..3800 stock players in `attrib.dat` row order;
3801..3825 the 25 created-player reserve entries. Executable initialization
constructs created-player ID hashes in a 25-iteration loop, and all 25 reserved
IDs join the matching pitcher reserves. A controlled created-player save is still
needed to establish their exact lifecycle, activation and deletion behavior.
Populated count 3826 differs from the **4035 full serialized/allocated capacity**.
Neither value is proof of a universal 4096/12-bit player-index limit.

The backend's `player_base` is the **name anchor**, not the physical record base.
`general_record_base` subtracts 56. `player_record()` is a name-anchored slice
whose name readers use only the first 28 bytes; use `player_payload()` for
attributes. Expanded backend work must preserve this distinction or replace it
with a clearly versioned physical-record API.

Names are materialized into player records while team slots retain the same
stable player IDs. Example: ID `0xC186D538`, `attrib.dat` row 526, stock placeholder
`Arizona State / 2`, saved name `Chuck Bourque` at index 526.

Strings may retain old content after their first NUL, e.g. `Keith\0 Stat\0`.
Read bounded C strings; do not require zero padding. The writer clears only an
edited name buffer. First-name limit is 11 bytes, last-name limit 15, leaving NUL.

## ID-index mapping

Mapping entries observed in the pre-player region are triples:
`[u32 player_id][u32 row_index][u32 same_row_index]`, little-endian.
Example for `0xC186D538`: `38 D5 86 C1 0E 02 00 00 0E 02 00 00` -> index 526.

The backend scans between the team block and player anchor, restricts candidates
to roster IDs, and selects a consistent bijective mapping. It resolves all 3800
rostered IDs in this sample; this is heuristic discovery, not a completely mapped
hash-table format. Default/CAP IDs are not all exposed by that roster-only map.
Do not copy its bounds or assumptions unchanged into an expanded save.

For CAP verification, scanning the same pre-player area finds exactly one unique
ID for each general index 3801..3825. All 25 IDs also map to pitcher indexes
1609..1633 in corresponding order. This supports a shared reserved-player pool.

## Batting and pitcher arrays

| Table | Physical base offset | Record bytes | Populated/editable rows | Full serialized/allocated rows |
|---|---:|---:|---:|---:|
| general | `0x2C407` | 84 | 3826 | 4035 |
| LH batting | `0x7F007` | 16 | 3826 | 4035 |
| RH batting | `0x8EC3B` | 16 | 3826 | 4035 |
| pitcher | `0xF22E3` | 20 | 1634 | 1650 |

Each physical array is preceded by a four-byte table ID/hash header, serialized
by generic helper `0x1A14F8`. General/LH/RH header value is `0xF58F3C1B`; pitcher
is `0x19FC5623`. Those are not row counts or the first record. General and batting
arrays include 209 zero reserve rows each; pitcher includes 16 zero rows.

Earlier batting anchors were four bytes early. The corrected bases reveal
FB/LD/GB percentages at bits 96/103/110; contact starts at 0. LF/CF/RF/HR
start at 68/75/82/89, all seven-bit fields, confirmed by executable getters.
All 27 fields match all 3801 default/stock rows on each side. The old assertion
that FB/LD/GB were absent or that the low DWORD was a hot/cold map is superseded.

Batting arrays use general-player indexes. Pitcher arrays have a separate ID-index
mapping; 1609 stock rows include Default plus 1608 actual stock pitcher rows,
followed by 25 reserves. The backend scans a bounded region immediately before
the pitcher array for consistent ID/index triples. These absolute offsets are
sample-profile values; serializer resizing can move every subsequent region.

Mapped fields reproduce stock DAT values under observed serialization rules:

- All 3800 rostered general records agree for mapped fields except 22 negative
  bunting sentinels: fourteen `-1` and eight `-2` values are packed as zero.
  All nonnegative bunting values match.
- All 27 mapped LH/RH batting fields agree for the 3801 Default/stock rows.
- All 1609 stock pitcher rows agree for mapped numeric values. Pitch-5 type 15
  means absent in this sample: its four DAT `-` parameters serialize as zero
  in 1152 rows. Type/sentinel meaning beyond this sample remains to be tested.
- Stamina is duplicated at bits 133..139; the writer updates both copies.

The player-format note and `memory_save.py` are the bitfield references.
Unknown bits are preserved. Body-type transform and derived eye-protection UI
labels still require controlled visual tests; a stock constant cannot prove a label.

## Editor behavior and remaining work

The editor can display/edit generated names and mapped general/appearance,
batting and pitching attributes, team strings, raw role DWORDs and rotations.
Former blanket read-only packed-attribute notes are obsolete. Unknown data stays
untouched. ZIP writing preserves other members and file metadata while rebuilding
the container; byte equality of the ZIP container itself is not required.

No-change raw save output is byte-identical in the supplied sample; ZIP member
contents are preserved. Edited saves are still experimental: no game load/save
compatibility or checksum update has been established by runtime tests.

Next: controlled edits to confirm hand/channel and appearance labels; fully map
ID-index/table framing and headers; trace name generation and CAP lifecycle;
validate edited saves in-game; implement explicit expanded profiles only after
runtime serialization changes are proven. See [handoff.md](handoff.md) and
[executable.md](executable.md) for the accepted 34-player/CAP-removal direction.
