# GUI roster editor status

Updated 2026-10-01. The unified Python/Tkinter editor operates on the currently
supported stock roster profiles. Executable expansion research does not expand
the editor's backend profiles.

## Current backends

| Source | Playable teams / slots | Names and attributes | Output |
|---|---|---|---|
| `DATABASE.BIG` | 152 / 25 | DAT-backed names, identity/general, appearance, batting and pitching fields | rebuilt BIGF with literal-only RefPack |
| raw/compressed `roster.bin` | 152 / 25 | IDs/roles/team data; no companion DAT player attributes | same raw/compressed source kind |
| `Rost*.sav` | 152 / 30 | generated names and mapped packed general/appearance, batting and pitching fields | raw save |
| PCSX2 roster-save ZIP | 152 / 30 | same save backend | ZIP with other members preserved |

## User interface

The editor now uses a three-pane layout:

- searchable team browser
- searchable roster table
- tabbed player/team editor

The roster table shows player, position, batting/throwing hand, both stored
batting-order channels, both defensive channels and the recognized pitching-role
bucket. Long attribute forms are scrollable.

Known enum-like fields use editable drop-downs where useful. Typing the first
letter selects matching choices, so handedness fields can be entered from the
keyboard (for example R/L/S). Packed numeric values remain the serialized form.

The editor tracks unsaved changes and warns before closing or replacing a dirty
document. Up to 30 document states are retained for Undo/Redo. Keyboard shortcuts
include Ctrl+O, Ctrl+S, Ctrl+Z, Ctrl+Y / Ctrl+Shift+Z and Ctrl+F.

## Search and filtering

Team search matches team key, school/team name, abbreviation, city and nickname.

Roster search filters the selected team's slots by slot number, player name,
position, batting/throwing hand and player ID. Filtering does not modify roster
order or serialized data.

## Starting rotation

The Rotation tab replaces the old comma-separated raw index entry. The three
stored starter slots are selected from player-name drop-downs and are validated
as three distinct, non-empty roster slots. Direct one-based slot-number entry is
also accepted.

This UI reflects the confirmed three-index storage. It does not change the
separate unresolved question of exact batting/defensive channel-to-pitcher-hand
selector behavior.

## Field validation and drop-downs

Mapped packed fields now use their known bit-width/range constraints before
writing. Position, handedness and several appearance/boolean fields use readable
choices. Unchanged DAT sentinel values such as absent-pitch markers are left
alone rather than being rejected by GUI validation.

The backend still remains authoritative: fixed-buffer text lengths and format-
specific restrictions are checked again when changes are applied.

## CSV import/export

The toolbar can export all teams/roster slots and exposed player fields to CSV
and import edited values back into the loaded roster.

CSV player IDs are structural guards, not movement instructions. Import refuses
rows whose player ID no longer matches the specified team/slot, so a spreadsheet
cannot silently reassign players. Team/rotation values repeated across rows must
be internally consistent. A successful CSV import is one Undo operation.

See [csv_roster_format.md](csv_roster_format.md) for the schema and workflow.

## Save-player editing

Mapped fields in the 56-byte general payload, 16-byte LH/RH batting records and
20-byte pitcher records are editable. First/last names use the save's fixed
buffers. All 27 mapped batting fields, including FB/LD/GB tendencies, are
supported. Writes preserve bits outside targeted masks.

Body type remains experimental and is not exposed as a named editable control.
Eye protection remains a derived presentation. Unknown packed fields and unknown
team metadata remain opaque.

## Validation and limitations

BIG writers are reparsed, decoded member content has been checked on the supplied
sample, and no-change save output is byte-identical in the existing verification
suite. Mapped-field mask-preservation checks are separate from GUI interaction.

CSV logic has unit coverage for export/import, enum entry and the player-ID guard.
The redesigned Tk interface has been syntax-checked but still needs ordinary
interactive testing on the user's desktop.

Most importantly, there is still no modified-game PCSX2 load/gameplay/save-reload
validation. Rebuilt archives can grow because the current compressor emits
literals only.

Supported profiles remain fixed at 152 teams, 25/30 roster slots, the documented
player capacities and the analyzed save offsets. A 34-slot or extra-team save
requires explicit backend/executable work.

## Next editor work

- Add direct graphical batting-order and defensive-alignment editing.
- Add explicit player move/swap workflows rather than using raw IDs or CSV.
- Improve field labels/enums where remaining raw values become understood.
- Validate edited outputs in PCSX2 and surface a compatibility status in the UI.
- Replace literal-only RefPack compression with a better compatible encoder when useful.
