# PS2 memory-card roster save reversing

Date: 2026-10-01

Source analyzed: user-supplied default roster save created by MVP 07 after
accepting the game's random-name generation prompt on boot.

Container ZIP:
- `BASLUS-21582R659be98.zip`

Roster payload:
- `Rost1.sav`
- size: `1,185,992` bytes
- SHA-256: `34dd9c930dc56eae194729b9b254451c39d721b18863a0336611e57e36415556`

## Important conclusion

The memory-card roster is not a small name overlay. It contains a largely
self-contained runtime roster database. The stock team/roster information is
copied into the save, while the player names are materialized into fixed-size
binary player records.

This gives us a second serialization of the same logical database and is useful
for validating the ISO format.

## Team block

For this save, the first team begins at file offset `0x20C3`.

There are exactly 152 fixed-size save team records:

- record size: **727 bytes**
- total team block: `152 * 727 = 110,504` bytes
- team block end: `0x1D06B`

The visible string fields use the same offsets as decompressed `roster.bin`:

| Offset | Size | Meaning |
|---:|---:|---|
| 0x000 | 8 | internal team key |
| 0x008 | 48 | school/team name |
| 0x038 | 16 | abbreviation |
| 0x048 | 40 | city |
| 0x070 | 32 | nickname |
| 0x090 | 48 | packed team metadata |
| 0x0C0 | 4 | roster capacity/count |
| 0x0C4 | 240 | 30 roster slots * 8 bytes |
| 0x1B4 | 3 | three starting-pitcher roster indexes |
| 0x1B7 | 1 | zero/padding |
| 0x1B8 | 287 | reserved/zero region |

The only structural expansion versus the stock ISO team record is the insertion
of five additional roster slots:

- stock `roster.bin`: 25 slots, 687-byte record
- memory save: 30 slots, 727-byte record
- difference: `5 * 8 = 40` bytes

### Stock-vs-save validation

Across all 152 teams:

- all visible team strings match the ISO database
- bytes `0x090..0x0BF` (team metadata) match **byte-for-byte**
- the first 25 roster-slot entries match **byte-for-byte**
- the three starting-rotation indexes match **byte-for-byte**
- roster count/capacity changes from 25 to 30
- save slots 25..29 are zero in this default save

This is strong independent confirmation that our decoded team metadata,
player-ID joins, lineup/role DWORDs, and rotation indexes are genuine game
runtime data, not artifacts of our ISO parser.

## String-copy behavior

The game often overwrites a string without clearing the entire fixed-width
buffer first.

Example: a stock first-name field containing `Oregon State` can become:

`Keith\0 Stat\0`

The C-string value is correctly `Keith`, but bytes after the first NUL still
contain remnants of the old placeholder.

Therefore:
- always parse these fields as NUL-terminated strings within fixed buffers
- never require padding bytes after the terminator to be zero
- writers should preferably clear the buffer before writing a new string even
  though the game itself does not always do so

## Player array

The packed player-record array begins at `0x2C43F` in this save.

Structure:

- capacity: **4096 records**
- record size: **84 bytes**
- total size: `4096 * 84 = 344,064` bytes
- end offset: `0x8043F`

### Player record

| Offset | Size | Meaning | Status |
|---:|---:|---|---|
| 0x00 | 12 | first-name buffer | CONFIRMED |
| 0x0C | 16 | last-name buffer | CONFIRMED |
| 0x1C | 56 | packed general player attributes | PARTIALLY MAPPED |

Record 0 is the `Default / Default` template.

Records 1..3800 correspond to the 3,800 stock roster players in
`attrib.dat` row order.

The game-generated random names are written directly into these records.

Example:

- player ID `0xC186D538`
- ISO `attrib.dat` row index: 526
- stock placeholder name: `Arizona State / 2`
- memory-save record 526: `Chuck Bourque`

The roster team entry continues to reference the same player ID. Therefore the
name randomization changes player-record content, not team roster identity.

### Reserved/generated player records

After the 3,801 stock/template records:

- records 3801..3825 contain 25 additional generated names
- records 3826..4095 are zero in this save

The exact gameplay purpose of those 25 pre-named reserved records is not yet
proven. They may be a generated-player/replacement pool. Do not label them as
created-player slots until tested.

## Player ID -> row index mapping

The save contains explicit mapping entries tying the 32-bit player database ID
to the packed player-record index.

Example bytes for Arizona State player `0xC186D538`:

```
38 D5 86 C1  0E 02 00 00  0E 02 00 00
^^^^^^^^^^^  ^^^^^^^^^^^  ^^^^^^^^^^^
player ID      526 LE       526 LE
```

This exactly matches `attrib.dat` row index 526.

This provides a deterministic bridge between:
- team roster player IDs
- ISO DAT rows
- memory-save packed player records

## Consequences for the editor

The GUI can now safely support:
1. importing random names from a PS2/PCSX2 roster save into the ISO database
2. identifying players by stable ID while displaying the save's generated names
3. future direct memory-card roster editing without reusing the ISO serializer

The memory-card save format should remain a separate backend from the
`DATABASE.BIG` backend because its player structures are packed binary records,
not the RefPack-compressed text DAT tables used on disc.

## Next reversing targets

1. Decode the 56-byte packed general-attribute payload in each 84-byte save
   player record by correlating all 3,800 known stock DAT rows.
2. Identify the save arrays corresponding to right-hand batting, left-hand
   batting, and pitching attributes.
3. Determine the exact ID-index table boundaries and hash/index organization.
4. Compare a save after a controlled lineup/position edit to isolate the complex
   roster-role DWORD subfields.
5. Compare a save after a single rating edit to map packed attribute bits.
