# DATABASE.BIG / roster.bin reverse-engineering notes

Date: 2026-10-01

## Source artifact

Analyzed user-supplied `DATABASE.BIG`.

- Archive magic: `BIGF`
- Archive byte length: `518251` (`0x7E86B`)
- File count: `10`
- Header/table declared length: `217` bytes
- Data begins at offset `220` (`0xDC`), implying 4-byte alignment/padding after the directory.

The archive uses a mixed-endian header:
- bytes 0x04..0x07: archive size, little-endian
- bytes 0x08..0x0B: file count, big-endian
- bytes 0x0C..0x0F: directory/header length, big-endian
- each directory entry: big-endian 32-bit offset + big-endian 32-bit size + NUL-terminated filename

## Directory

| File | Offset (dec) | Offset (hex) | Size |
|---|---:|---:|---:|
| location.dat | 220 | 0xDC | 1470 |
| conf.dat | 1692 | 0x69C | 563 |
| team.dat | 2256 | 0x8D0 | 3 |
| tstat.dat | 2260 | 0x8D4 | 2281 |
| default.dat | 4544 | 0x11C0 | 174 |
| roster.bin | 4720 | 0x1270 | 35964 |
| pitcher.dat | 40684 | 0x9EEC | 71115 |
| rhattrib.dat | 111800 | 0x1B4B8 | 101744 |
| lhattrib.dat | 213544 | 0x34228 | 102908 |
| attrib.dat | 316452 | 0x4D424 | 201799 |

## roster.bin

- Exact extracted size: `35964` bytes
- SHA-256: `5b239be2ad19f0dd480651a7b37d35667cbd4200edb05b5501ea76dc0307bb3a`
- First known readable content includes Arizona State / Tempe / Sun Devils.
- Plain ASCII scanning produces fragmented strings (for example pieces of "Arizona State", "Tempe", and "Sun Devils") rather than conventional NUL-terminated records.
- This is strong evidence that roster.bin fields are bit-packed and/or not byte-aligned. Do **not** assume fixed C strings or blindly edit byte substrings.
- Initial 7-bit grouping experiments produce unusually high printable-character rates but do not yet prove the packing scheme. Field boundaries and bit order remain unconfirmed.

## Working hypothesis

`roster.bin` likely stores team/roster identity and indexing data, while player ratings/handedness/pitching attributes may be distributed across the companion files `attrib.dat`, `rhattrib.dat`, `lhattrib.dat`, and `pitcher.dat`. Treat this only as a hypothesis until differential edits establish relationships.

## Reverse-engineering method

1. Preserve the original BIG archive and hashes.
2. Extract all members losslessly.
3. Build a bit-level reader and identify repeated record boundaries.
4. Correlate readable team names with known in-game teams and record starts.
5. Generate controlled one-field edits in-game/editor when possible.
6. Diff original vs modified archives and extracted members.
7. Promote a field to "confirmed" only after repeatable differential evidence.
8. Keep unknown bytes/bits untouched when building writers.

## Evidence levels

Use these labels in future notes:
- **CONFIRMED**: supported by controlled diffs or repeatable parsing.
- **LIKELY**: multiple observations support it, but no controlled diff yet.
- **SPECULATIVE**: plausible hypothesis only.

## Next targets

- Determine the exact bit ordering and string encoding used by roster.bin.
- Identify team-record boundaries and team count.
- Map roster/player references into companion attribute files.
- Establish whether any archive-level checksum is required after repacking.
