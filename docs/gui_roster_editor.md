# GUI roster editor status

Updated 2026-10-01. The unified Python/Tkinter editor operates on stock profiles.
Executable expansion research does not expand the editor's supported profiles.

## Current backends

| Source | Playable teams / slots | Names and attributes | Output |
|---|---|---|---|
| `DATABASE.BIG` | 152 / 25 | DAT-backed names, identity/general, appearance, batting and pitching fields | rebuilt BIGF with literal-only RefPack |
| raw/compressed `roster.bin` | 152 / 25 | IDs only; no companion DATs | same raw/compressed source kind |
| `Rost*.sav` | 152 / 30 | generated names and mapped packed general/appearance, batting and pitching fields | raw save |
| PCSX2 roster-save ZIP | 152 / 30 | same save backend | ZIP with other members preserved |

Shared functionality includes team key/name/abbreviation/city/nickname editing,
raw roster-role DWORD editing, starting-rotation index editing, and two batting
and defensive channels displayed from decoded role bits. Existing roster player
IDs are preserved by the GUI. Team art/conference/location metadata is displayed;
full graphical asset and conference editing workflows are not implemented.

The role packing is confirmed by executable getters/setters. vs-RHP/vs-LHP aliases
use the user's description of the default/secondary screen; the exact engine
selector-to-hand association still needs an unequal-channel controlled test.

## Save-player editing

The former "all packed attributes are read-only" status is obsolete. Corrected
batting bases and seven-bit percentage widths also expose FB/LD/GB tendencies;
all 27 batting fields agree with both stock/default tables. Mapped
fields in the 56-byte general payload, 16-byte LH/RH batting records, and 20-byte
pitcher records are editable. First/last names are separate fixed buffers.
The code preserves bits outside the targeted masks. Bitfield maps are listed in
[memory-card research](research/memory_card_roster.md) and defined by constants in
`src/mvp07_modding_suite/memory_save.py`.

Body type remains explicitly experimental: stock DAT bodytype is constant, so
its transform cannot be proven from stock correlations. Eye protection has
inferred derived controls; an in-game visual diff is still needed. Unknown
packed fields and unknown team metadata remain opaque. Stock ID-index mapping
uses heuristic discovery with consistency checks, not a generic expanded-save parser.

## Validation and limitations

BIG writers are reparsed, decoded member content is checked on the supplied
sample, and no-change save output is byte-identical. Mapped-field comparisons
and controlled mask writes are checked separately. These establish structural
behavior, not game compatibility. No modified ISO/save boot, gameplay, memory-card
checksum behavior, or dynasty test has been completed. Rebuilt archives can grow
because the compressor emits literals only.

The supported profiles are fixed: 152 teams, 25/30 roster slots, a 3826 populated-player
editing range within 4035 serialized records, and sample-specific table offsets. A 34-slot/extra-team save
requires explicit versioned backend changes; editing an executable count does
not change these constants or relocate save arrays automatically.

## Next work

- Runtime validation of stock edits before advertising production-safe writers.
- Confirm channel labels and add direct batting/defensive lineup controls.
- Player reassignment, undo/redo, dirty-state tracking, and field validation/enums.
- Improved RefPack compression.
- Expanded profiles only after a patched runtime/serializer is validated.

Executable hypotheses, accepted CAP removal, required assets and an ordered
experiment plan are in [executable.md](research/executable.md).
