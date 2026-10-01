# GUI roster editor status

Initial editor architecture added 2026-10-01.

## Current capabilities

- Open `DATABASE.BIG` directly.
- Parse BIGF and RefPack/QFS members.
- Browse all 152 team records and all 25 roster slots per team.
- Resolve each roster player ID into `attrib.dat`, `rhattrib.dat`, `lhattrib.dat`, and `pitcher.dat`.
- Edit confirmed team text fields.
- Edit an initial set of player identity/general, batting, and pitching fields.
- Display inferred batting-order values when the stock role flag matches a confirmed common pattern.
- Display the confirmed team asset ID while leaving unresolved metadata explicitly unlabeled.
- Save a rebuilt `DATABASE.BIG` using conservative literal-only RefPack compression.
- Re-open the saved archive immediately as a structural verification step.

## Important limitation

The save path is structurally verified by our parser but has **not yet been game-tested in an ISO**. Keep it marked experimental until an ISO boot/gameplay test confirms EA's runtime accepts the larger literal-only RefPack streams.

## Next GUI work

- Add validation/ranges and friendly enum names.
- Add explicit lineup/rotation editing after the role bitfield is fully decoded.
- Add roster reassignment/player movement tools.
- Add undo/redo and change tracking.
- Add a faster RefPack compressor so rebuilt archives stay close to stock size.


## Unified document backends

The GUI now uses `src/mvp07_modding_suite/documents.py` and can directly open:

| Source | Team/roster | Names | DAT ratings | Save |
|---|---|---|---|---|
| DATABASE.BIG | yes, 25 slots | yes | yes | rebuilt BIGF |
| roster.bin | yes, 25 slots | IDs only | no companion DATs | RefPack/raw bin |
| Rost*.sav | yes, 30 slots | yes | packed payload read-only | raw save |
| PCSX2 save ZIP | yes, 30 slots | yes | packed payload read-only | ZIP preserved |

For memory-card saves the editor exposes the 56-byte unknown player payload as
hex for research but deliberately refuses to rewrite it. This is a preservation
rule, not a UI limitation: writing guessed bits would risk corrupting unrelated
player fields.

The save backend also discovers the game's explicit `player_id -> player_index`
mapping and uses it to resolve roster IDs to generated-name records.

### Writable .sav fields now

- team key/name/abbreviation/city/nickname
- 30 roster-slot role DWORDs
- three starting-pitcher indexes
- generated first and last names
- existing roster player IDs are preserved

### Pending .sav fields

The 56-byte packed general-attribute payload is not yet field-complete. Current
research shows strong statistical correlations (for example jersey number is
concentrated around payload bits 50..55), but it is not safe to call those
individual bit ranges proven because neighboring fields/transformations affect
the observed values. Unknown bits remain untouched until controlled evidence or
a complete packing model exists.
