# Roster CSV import/export

Updated 2026-10-01.

The roster editor can export the currently loaded stock-profile roster source to
a UTF-8 CSV and import edits back into that same loaded roster.

## Scope

CSV is intended for bulk editing in Excel, LibreOffice, Numbers, pandas, or
similar tools. It exposes only fields already supported by the roster backends.

The exporter writes one row per roster slot, including empty slots. Human-facing
team and slot numbers are one-based. Player IDs and role flags are hexadecimal.

Core columns:

| Column | Meaning |
|---|---|
| team_index | 1-based playable team index |
| team_key | internal team key |
| team_name | school/team name |
| team_abbreviation | team abbreviation |
| team_city | city |
| team_nickname | nickname |
| starter_1_slot..starter_3_slot | 1-based starting-pitcher roster slots |
| roster_slot | 1-based roster slot |
| player_id | structural player ID; not reassigned by CSV import |
| first_name | editable first name; automatically routed to the loaded roster's name storage |
| last_name | editable last name; automatically routed to the loaded roster's name storage |
| player_name | convenience/display column; ignored on import |
| role_flags | raw 32-bit roster-role word |

To rename a player, edit `first_name` and `last_name`. For example:

```csv
team_index,roster_slot,player_id,first_name,last_name
1,1,0x12345678,John,Smith
```

Use the actual exported team/slot/player ID. Names automatically update generated names
for a memory-card `.sav` or PCSX2 ZIP, or the DAT names for `DATABASE.BIG`. Exports contain
only the universal name columns, so there are no duplicate editable name fields.
`player_name` is regenerated for display on export and remains ignored on import.

Old source-prefixed name columns (`save.first_name`, `save.last_name`,
`attrib.first_name`, `attrib.last_name`) are rejected. Re-export older CSVs
from the updated editor before editing names. An empty universal name cell
clears that name part; an omitted column leaves it unchanged.
Raw `roster.bin` has no player-name data: its universal name cells
are blank, and entering names for populated players raises an explanatory error.
Memory-card names retain their Latin-1 buffer limits: 11 bytes for first name,
15 bytes for last name.

Other mapped player fields use namespace prefixes:

- `attrib.` for general/appearance attributes
- `vs_rhp.` for the default / user-described vs-RHP batting channel
- `vs_lhp.` for the secondary / user-described vs-LHP batting channel
- `pitching.` for mapped pitcher fields

Read-only diagnostics such as packed save hex and save row indexes are not
exported as editable CSV columns.

## Safety behavior

CSV import deliberately does **not** move players. The `player_id` in each row
must still match the player in the specified team/slot. This prevents a sorted,
copied, or partially edited spreadsheet from accidentally reassigning roster
identities.

Team data and the three starter slots are repeated across that team's rows.
Import rejects inconsistent repeated values. Rotation slots must be three
different valid roster slots.

Mapped numeric fields use the same validation as the GUI. Unknown binary fields
remain untouched by the backend.

CSV import participates in editor undo/redo as one operation.

## Recommended workflow

1. Open the source roster in the editor.
2. Export CSV.
3. Keep `team_index`, `roster_slot`, and `player_id` intact.
4. Edit `first_name` / `last_name` to rename players, plus other supported fields.
5. Import the CSV into the still-open matching roster source.
6. Review changes and save to a new game file.
7. Validate the resulting game file in PCSX2 before treating edits as production-safe.
