# MVP 07 Modding Suite — beta1

This is the first public beta release of the MVP 07 Modding Suite roster editor.

The goal of beta1 is to make the already-mapped stock roster formats practical to
edit without requiring users to understand the underlying binary structures.

## Download / install

### Windows
Download **MVP07ModdingSuite-beta1-Windows-x64.zip**, extract it, and run:

`MVP07ModdingSuite-beta1.exe`

The packaged Windows build includes Python and the required runtime components.
A separate Python installation is not required for the packaged build.

### Run from source
Requirements:

- Python 3.10 or newer
- Tkinter
  - included with the standard Windows/macOS Python installers
  - some Linux distributions require `python3-tk`
- no third-party runtime Python packages

Run:

```bash
python run_editor.py
```

## Supported roster sources

beta1 can open and edit:

- `DATABASE.BIG`
- raw or RefPack-compressed `roster.bin`
- raw PS2 roster `.sav` files
- PCSX2 roster-save ZIP archives

The current editor targets the documented stock profiles:

- 152 playable teams
- 25 roster slots per team in the disc database
- 30 serialized roster slots per team in the analyzed memory-card save profile

Expanded-team / 34-player roster formats are not implemented in beta1.

## Major editor changes

### New three-pane interface

The roster editor has been redesigned around a cleaner workflow:

- searchable team browser
- searchable roster table
- tabbed player/team editor
- scrollable long attribute forms
- raw diagnostics moved into an Advanced tab
- clearer labels in place of many internal DAT field names

The interface is intended to make routine roster editing possible without exposing
the reverse-engineering details unless they are actually useful.

### Search and filtering

Team filtering searches:

- internal team key
- school/team name
- abbreviation
- city
- nickname

Roster filtering searches:

- player name
- roster slot
- position
- batting hand
- throwing hand
- player ID

Filtering is visual only and does not change serialized roster ordering.

### Undo / Redo

beta1 adds document-level undo and redo support.

Supported shortcuts:

- `Ctrl+Z` — Undo
- `Ctrl+Y` — Redo
- `Ctrl+Shift+Z` — Redo
- `Ctrl+O` — Open
- `Ctrl+S` — Save As
- `Ctrl+F` — Focus roster search

CSV imports are recorded as one undoable operation.

### Unsaved-change tracking

The editor now:

- marks the document when changes are pending
- displays an unsaved-changes indicator
- warns before closing a modified roster
- warns before opening another file over a modified roster

### Field validation

Known mapped numeric fields are validated before the backend is modified.

Examples include:

- jersey number
- height / weight raw values
- player attribute bit-width ranges
- batting values
- pitching values
- appearance values
- raw role flags

Backend-specific checks such as fixed string-buffer lengths still run when writes
are applied.

### Dropdowns and keyboard entry

Known enum-style fields use editable dropdowns where appropriate.

Examples include:

- batting hand
- throwing hand
- primary / secondary position
- pants / sock presentation
- catcher mask
- eye black
- sunglasses
- simple on/off equipment fields

Dropdowns support keyboard autocomplete. For example, selecting the batting-hand
field and pressing `R`, `L`, or `S` selects Right, Left, or Switch.

### Starting rotation editor

The old raw comma-separated rotation-index field has been replaced by a dedicated
Starting Rotation tab.

The editor now shows three starter selectors populated with player names and roster
slots.

Validation prevents:

- duplicate starter assignments
- invalid roster slots
- empty roster slots being selected as starters

The game stores exactly three starting-pitcher slot indexes in the currently
supported stock team format.

## CSV import / export

beta1 adds whole-roster CSV export and import for bulk editing in Excel,
LibreOffice, Numbers, pandas, or similar tools.

The exporter writes one row per roster slot.

Core identity / structure columns include:

- `team_index`
- `team_key`
- `team_name`
- `team_abbreviation`
- `team_city`
- `team_nickname`
- `starter_1_slot`
- `starter_2_slot`
- `starter_3_slot`
- `roster_slot`
- `player_id`
- `first_name`
- `last_name`
- `player_name`
- `role_flags`

Mapped player fields are exported with namespaces such as:

- `attrib.`
- `vs_rhp.`
- `vs_lhp.`
- `pitching.`

### Name editing fix

beta1 uses universal editable:

- `first_name`
- `last_name`

The importer automatically routes those names to the correct backend:

- generated memory-card save names for `.sav` / PCSX2 ZIP sources
- DAT-backed names for `DATABASE.BIG`

`player_name` remains a convenience/display column and is intentionally ignored
during import.

### CSV safety rules

CSV import deliberately does not use changed player IDs as movement instructions.

The `player_id` on a CSV row must still match the player occupying the specified
team/slot in the open roster. This protects against accidental player movement if
rows are sorted or copied in a spreadsheet.

Repeated team and rotation fields must also be internally consistent.

## Player editing currently available

Depending on the source backend, beta1 exposes mapped fields including:

### General / identity
- first / last name where supported
- jersey number
- batting hand
- throwing hand
- primary / secondary position
- height
- weight
- year
- home location
- speed
- fielding
- range
- throwing strength
- throwing accuracy
- bunting
- plate discipline
- baserunning
- durability
- batting stance
- swing type
- ditty
- star power
- scholarship
- attitude
- academic

### Appearance
- face morph
- bone profile
- skin tone
- eye colour
- hair colour
- sideburns
- facial hair
- cap type
- cap position
- eye black
- sunglasses style
- batting helmet
- elbow guard
- wristbands
- shin guard
- pants / socks
- catcher mask

### Batting
All 27 currently mapped batting fields are editable for each stored batting channel,
including:

- contact
- power
- nine hit-location values
- LF / CF / RF / HR percentages
- FB / LD / GB tendencies
- chase values
- take values
- miss values

### Pitching
Mapped pitcher fields include:

- delivery
- stamina
- pickoff
- fastball control / velocity
- pitches 2–5 type
- movement
- description
- control
- velocity

Unknown bits are preserved by the backend.

## Team / roster editing

beta1 supports:

- team key
- school/team name
- abbreviation
- city
- nickname
- raw roster role flags
- starting rotation indexes through the new rotation UI
- viewing mapped team metadata
- viewing the two stored batting-order channels
- viewing the two stored defensive channels
- viewing recognized pitching-role buckets

Direct graphical batting-order / defensive-lineup editing is not yet included in
beta1.

## Backend / reverse-engineering status

The project currently includes:

- BIGF archive reading/rebuilding
- EA RefPack decompression
- conservative literal-only RefPack compression
- stock `roster.bin` team parsing
- DAT table parsing/writing
- memory-card roster-save parsing
- mapped packed save-player fields
- mapped batting arrays
- mapped pitcher arrays
- roster role packing research
- starting rotation mapping
- executable fingerprint / inspection tooling
- stock-profile verification tooling

Research also documents current findings around:

- team/runtime limits
- conference structures
- team audio selectors
- stadium packages
- logos / uniform lookup behavior
- 3D/stadium archive structure
- player-pool capacity
- possible future 34-player/team expansion

These expansion topics remain research, not beta1 features.

## Validation performed

The current repository validation includes:

- stock structure checks
- unchanged-file round trips
- mapped field preservation checks
- CSV export/import tests
- name-routing tests
- enum / field-validation tests
- executable fingerprint checks
- supplied stock DATABASE.BIG / roster-save cross-file comparisons

Recent name-import validation confirmed:

- DATABASE.BIG CSV rename → save → reopen
- memory-card ZIP CSV rename → save → reopen
- raw save reopening
- unrelated-data preservation

## Important beta warning

This is a **beta**.

The binary writers are structurally validated, but modified game files have not
yet completed comprehensive PCSX2 gameplay / dynasty / save-reload testing.

Use copies of your original files.

Recommended testing sequence:

1. Open an original/copy in beta1.
2. Make a small controlled edit.
3. Save to a new output file.
4. Reopen the output in the editor.
5. Insert/rebuild it into your game setup.
6. Test loading in PCSX2.
7. Test gameplay.
8. Test save/reload.
9. Keep the original file available for comparison.

Please report any editor errors, unexpected values, game-load failures, or fields
that do not behave as labeled.

## Known limitations

- stock profiles only
- no 34-player roster expansion
- no added-team profile support
- no direct graphical batting-order editor yet
- no direct graphical defensive-alignment editor yet
- no explicit player move/swap workflow yet
- exact pitcher-hand association of the two lineup channels still needs a
  controlled unequal-channel runtime test
- some appearance labels remain inferred rather than visually proven
- literal-only RefPack output may be larger than the original compressed streams
- no full modified-game regression suite yet
- no ISO builder in this release

## Project direction after beta1

Near-term work is expected to focus on:

- real PCSX2 validation of edited stock files
- graphical lineup / defensive controls
- player movement / swapping
- additional readable enums / labels
- better compression
- broader archive / asset tooling
- eventual stadium / texture / model workflows

Executable expansion work will continue separately and will not be exposed in the
editor until the relevant formats and runtime consumers are sufficiently proven.
