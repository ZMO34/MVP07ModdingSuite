# Agent handoff: stock modding and research

Updated **2026-10-01**. Repository: `ZMO34/MVP07ModdingSuite`, branch `main`.
Start here to continue without relying on previous chat history.

## Current user objective and priorities

Build practical modding capability for the stock game first. Continue deepening
roster/asset knowledge where it unlocks useful edits; complete reverse engineering
is not required. Team/roster expansion is deferred. The earlier 34-player/CAP
tradeoff below remains a long-term hypothesis, not the immediate task.

The eventual Python GUI is a general BigGUI-style file/asset viewer plus roster
editor: BIG browsing/replacement, textures, models, audio, and an ISO workspace.
The user rebuilds test ISOs manually; their working PowerISO process is the
baseline. Integrated extraction/edit/rebuild is future work. Preserve G001–G010
for Create-a-Team and add future real-program stadium assets separately.
Keep evidence rich but navigation compact: this handoff is the entry point,
with detailed evidence in the existing topic reports. Do not create duplicate
status/hypothesis/master reports for each conversation.

## Read order and evidence ownership

1. [Executable research](executable.md): exact input hashes, ELF mapping, named
   address inventory, serializers, layouts, hard limits, asset paths, hypotheses,
   missing artifacts and staged runtime experiments. This is the executable source of truth.
2. [Disc database format](database_big_roster.md): BIGF/RefPack directory and
   stock team/sentinel/role/metadata maps, DBMisc inventory and audio-ID joins.
3. [Memory save](memory_card_roster.md): physical array framing, populated versus
   serialized counts, ID joins, strings and profile caveats.
4. [Player fields](save_player_format.md): exact general, batting and pitcher
   bit maps plus confidence levels for appearance interpretations.
5. [Editor status](../gui_roster_editor.md): supported backends, implemented
   fields, fixed-profile assumptions and runtime testing gaps.

Use the executable SHA-256 in the report to relocate addresses in other builds.
The supplied executable duplicates were identical. The game originals, extracted
DATs, save ZIP and disassembly dumps are excluded from Git. A future agent needs
matching local inputs or user-provided originals; documentation is sufficient to
reproduce the research but does not include copyrighted game data.

## Most consequential confirmed findings

- Team table framing includes a sentinel: count 153 = sentinel + 152 playable
  teams. Stock prefix =4+487; save count/sentinel/first playable offsets are
  `0x1DE8`/`0x1DEC`/`0x20C3`.
- Runtime team stride 728; serialized length `487+ 8*n` gives 687 (25) and
  727 (30). Metadata DWORD ordering differs between runtime and serialization.
- Fixed runtime storage/search loops use 30. A validation branch distinguishes
  counts >=26. Increasing only a serialized count would overwrite later fields.
- The tail at runtime `+0x1B4` / stock `+0x18F` / save `+0x1B7` belongs to
  custom-ballpark data; it is not a lineup array or safe spare storage.
- General/LH/RH full allocated **and serialized** arrays have 4035 rows; 3826
  are populated (Default + 3800 stock + 25 CAP), followed by 209 zero rows.
  Pitcher array has 1650 full rows, 1634 populated, then 16 zero rows.
- Correct batting physical bases are `0x7F007` / `0x8EC3B`, four bytes after
  former anchors. All percentage fields are seven bits; FB/LD/GB are recovered.
  Existing previously mapped fields keep the same absolute positions after
  both base and relative-bit corrections.
- General records are attributes-first at `0x2C407`; `player_base` in the current
  API is the name anchor `0x2C43F`. Keep those coordinate systems distinct.
- CAP initialization explicitly loops 25 created-player IDs. All 25 reserve IDs
  join general indexes 3801..3825 to pitcher indexes 1609..1633.
- 34×152 +Default =5169 general rows with CAP removed, exceeding 4035 by 1134.
  Removing CAP alone is insufficient. Actual creation of nine extra fully
  attributed players/team has not been traced; name generation alone is not enough.
- Team serialization can iterate a dynamic count, but initialization and other
  consumers contain153. Conference IDs are five bits, while the constructor
  provisions16. Membership enumeration uses metadata; schedules remain unverified.
- Logo paths format `../logos/a%03d.swf` from art ID. Uniform mapping uses
  seven-byte entries, byte-sized keys, and a local `<154` lookup gate.
  Those encoding/gate facts do not establish a global supported team maximum.

## Implemented changes in this pass

- Added `tools/inspect_elf.py`: ELF info, string search, direct call search,
  candidate address xrefs, partial R5900-aware disassembly, and exact-build
  verification of **62 instruction fingerprints**. It is read-only.
- Added `tools/verify_stock.py`: supplied-profile cross-file, table framing,
  reserve joins, decoded/no-change round trips and independent mask-preservation checks.
- Corrected batting bases, seven-bit percentage widths, and added FB/LD/GB
  mappings in `memory_save.py`; exposed the three recovered fields in the GUI.
  Added explicit full-capacity constants without exposing unpopulated reserves.
- Corrected documentation/API comments on sentinel framing, packed attributes,
  lineup hand-label uncertainty, array counts and bases. Preserved newer upstream
  `save_player_format.md` research and reconciled its conflicting claims.
- Fixed literal backslash-n syntax corruption in `run_editor.py` and package
  `__init__.py`. Added a normal guarded launcher.
- Removed `.github/chatgpt-write-test.txt`, a connectivity probe. Added ignores
  for Python caches, local inputs/extracted outputs and game binaries. Useful
  research stays in the repository; duplicate binaries/dumps/caches are excluded.

## Validation performed

Run on the exact supplied inputs; all checks passed:

```bash
python -m compileall -q src tools run_editor.py
python tools/inspect_elf.py /path/to/SLUS_215.82 verify
python tools/verify_stock.py /path/to/DATABASE.BIG /path/to/BASLUS-21582R659be98.zip
```

The stock verification covers:

- count/sentinel framing; all 152 visible team strings, metadata, first 25 slots,
  five empty save slots, rotation indexes and ballpark-associated tails;
- **3801** general and **3801 per side** batting rows, all mapped fields;
- **1609** pitcher rows, including Default;
- documented sentinels:14 bunting `-1` + 8 bunting `-2` -> 0; 1152 absent fifth pitches
  have `-` DAT parameters ->packed zero;
- 25 CAP general-to-pitcher ID joins; full serialized capacities/table headers
  and 209/16 zero reserve records;
- raw save byte identity, all ZIP member-content identity, all BIG decoded-member
  identity, stock `roster.bin` decoded identity and successful reopening;
- **122 field-write checks**: 43 general, 27 LH, 27 RH, 25 pitcher; readback and
  unchanged unrelated bits/adjacent bytes, including duplicated pitcher stamina.

Source/import checks are not a GUI interaction test. The GUI has not been
interactively tested in this execution environment. There is no modified-game
boot/gameplay/save-reload/dynasty test, expansion patch, new-team texture,
complete scheduling-archive map or proven save checksum procedure.

## Stadium / 3D research added

The vanilla stadium folder has now been inventoried and documented separately.
Confirmed findings include 23 authentic stadium BIGs, ten preserved generic BIGs,
modular ORD/ORL + SSH + DAT/IFO/CSV resources, and a controlled comparison of
VENUDAY/VENUDUSK/VENUNITE showing 55 identical and 43 variant-dependent members.
Direct MVP 05 ord2o/OEdit compatibility remains untested and must not be treated
as confirmed. See [stadium_3d_assets.md](stadium_3d_assets.md).

## Recent-chat reconciliation (2026-10-01)

Coverage: the supplied DBMisc thread, retrieved recent project-chat excerpts,
and current `main` at `cf3a8e5` were reconciled. Retrieval returns relevant
excerpts rather than full transcripts; this is not an exhaustive message-by-
message archive. Direct game bytes/code override conflicting earlier guesses.

| Discussion | Preserved finding / resulting update |
|---|---|
| MVP Modding Suite Main | Python general editor vision; single-PC workflow; GitHub is the canonical handoff. Current executable/editor work supersedes the original scaffold plan. |
| Roster Bin Reversing | Disc/save backends and role/player research retained; latest UI/CSV/rotation/Undo/Redo capabilities already present at `cf3a8e5` preserved. Height/weight physical conversion remains unresolved. |
| Analyze PS2 Executable | Expansion deprioritized; corrected stadium bits 4..9 and table resolution added to reports; broad BIG/ISO workflow captured without claiming it is built. |
| 3D Model Modding | Existing inventory and VENU comparison retained; all generics preserved; actual stock assignment distinguished from authentic archive presence. Practical modding takes priority over complete format reversal. |
| DBMisc analysis | Nine-member inventory rechecked; exact audio selectors solved; non-playable school choices retained as CAT vocabulary. Earlier `+0x090` audio guess and `+0xA0` graphics labels corrected. |
| Refine Research Prompt (Sept 25) | Fewer research files, rich cumulative evidence, near-autonomous roster focus and user-performed ISO testing retained through this compact handoff. |

No speculative calendar estimate is made a delivery commitment. Archive/model
conversion, asset linking and executable expansion depend on controlled tests.

## New direct results and verification

- School audio: `+0xA0` bits 12..20, getter/setter `0x6F7C60/0x6F7C70`.
- Nickname audio: `+0xA0` bits 21..29, getter/setter `0x6F7C98/0x6F7CA8`;
  152/152 exact CSV matches, 120 unique IDs, 18 stock teams with extended IDs.
- CAT CSV IDs flow through decimal conversion to 68-byte ID/string rows and
  those same setters. Stock school calls use 1..153 except 50; CAT school
  vocabulary uses 201..360. Equality to stock art IDs does not make the audio
  field a graphics selector. `+0x090` remains unresolved indexed-byte data.
- `teaminfo.csv` joins all 152 records by logo ID, matching text and location.
  Abbreviations are not unique. Uniform keys are ordinal IDs 1..152 × 0/1,
  which differ from school/logo IDs past the omitted art ID 50.
- Stadium getter is shift 4/mask 63; 34 selector entries resolve through a
  separate 38-resource table. 20 stock teams initially select authentic parks,
  132 generics. Virginia/Mississippi State select G003; reassignment/overrides
  are untested.
- `+0xAC` has eight three-bit accessor fields, not two nine-bit references.
  Presentation/color semantics remain unresolved.
- Added read-only `tools/analyze_team_audio.py`; no game binaries, patches,
  full extracted dictionaries, or redundant reports were committed.

Reproduction commands (matching originals required):

```bash
python -m compileall -q src tools run_editor.py
python -m unittest discover -s tests -v
python tools/inspect_elf.py /path/to/SLUS_215.82 verify
python tools/analyze_team_audio.py /path/to/DATABASE.BIG /path/to/DBMISC.BIG --verify-stock --json
python tools/verify_stock.py /path/to/DATABASE.BIG /path/to/BASLUS-21582R659be98.zip
```

The DBMisc checks also pass for compressed and decoded raw `roster.bin`.
The supplied disc/save stock checks and 122 preservation checks were rerun;
62 executable fingerprints replace the historical 35-check total. Audio
playback, modified-file gameplay, GUI interaction and expansion remain untested.

## CSV naming correction (2026-10-01)

New exports use editable universal `first_name` and `last_name` columns for
both DATABASE.BIG and memory-card sources. `player_name` remains display-only.
Old source-prefixed name columns are rejected at the user's request; no legacy
name compatibility is retained. Names route to the active backend's name
storage; raw roster.bin alone cannot store player names. See
[CSV format](../csv_roster_format.md) for blank/missing-cell behavior.
Regression tests cover both sources, no-op imports, clearing a name part,
partial name edits, rejected old/mixed schemas and the player-ID guard.
Full CSV export/import and rename/save/reopen were verified against the supplied
DATABASE.BIG and PCSX2 ZIP; the latter also passed raw .sav reopening. Unrelated
fields/members and original files remain preserved. Game/GUI testing is pending.

## Immediate next work

1. User tests ordinary edited stock files through boot/load/gameplay/save/reload.
2. Separately test one school call (CAT ID 226) and one nickname (213) on an
   existing team while preserving art/location/conference and unrelated bits.
   Trace audio project/event banks if a call is silent or wrong.
3. Validate lineup-hand labels, relief roles, appearance enum choices, displayed
   height/weight conversions, `+0x090` byte selectors, color/presentation fields,
   uniform payloads and custom-ballpark trailing 24 bytes where useful for edits.
4. Test a one-field stadium reassignment and a one-member texture replacement;
   check normal games and dynasty/frontend overrides. Preserve generics.
5. Develop the general BIG browser/replacement workflow, followed by proven
   texture/model and ISO workflows. Additional asset files still need known
   consumer paths; adding bytes to an archive/ISO does not register a new asset.
6. Revisit expanded rosters/teams/conferences only after the stock path is proven.

Do not resume from superseded claims: 723-byte team serialization, unknown
491-byte global header, 4096-player save array, 3826 as full serialized capacity,
old batting bases, four lineup arrays in the ballpark tail, five graphics refs
(the two at `+0xA0` are audio), `+0x090` as school/nickname selector, nine-bit
stadium ID or shift-by-3, two nine-bit `+0xAC` refs, or nine-bit encoding as
proof of a globally working team/asset maximum.
