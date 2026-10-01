# SLUS-21582 executable research and expansion handoff

Updated: 2026-10-01. **Static research completed; expansion patches are not implemented.**

This document is the starting point for continuing executable work. Addresses
are virtual addresses (VAs), not file offsets. Function names below are descriptive
research labels: the ELF is stripped. Observations apply to the exact build below.
No boot, gameplay, dynasty simulation, or modified-save compatibility test was
performed. A count or encoding width is evidence about that subsystem, not proof
that every other subsystem accepts the same limit.

## Inputs and reproducibility

| Input | Bytes | SHA-256 |
|---|---:|---|
| `SLUS_215.82` | 8,883,572 | `a8f01615db039a0e7fba9d5ccfe7a85728d5ec8d6fe368554777e12ef32c8642` |
| `DATABASE.BIG` | 518,251 | `35f93770a501c47b85e9e8add380aa603adbdf9eb59e807fbdb30ba0b8f0d252` |
| `BASLUS-21582R659be98.zip` | 268,468 | `bc88a0d0cc54d7257ea53c7a9ddda6978f1d4a14bae86132b99e2934a42b81b6` |
| ZIP member `BASLUS-21582R659be98/Rost1.sav` | 1,185,992 | `34dd9c930dc56eae194729b9b254451c39d721b18863a0336611e57e36415556` |

The supplied `SLUS_215(1).82` duplicate has the same hash. Original binaries,
extracted database files, and bulk disassembly are not committed. Reproduce from
these hashes; never infer that a different region/build has identical addresses.
The save was described by the user as the default roster saved after accepting
random player names. This provenance is user supplied; its byte layout is independently checked.

The executable is little-endian ELF32/MIPS, using PS2 R5900 instructions.

| Section | VA | File offset | Size |
|---|---:|---:|---:|
| `.text` | `0x100000` | `0x1000` | `0x5A6EEC` |
| `.database_codeoverlay` | `0x6A83E8` | `0x5A93E8` | `0x6A5F4` |
| `.frontend_codeoverlay` | `0x7129E0` | `0x6139E0` | `0xCDB5C` |
| `.apt_codeoverlay` | `0x7E0540` | `0x6E1540` | `0x73D64` |
| `.data` | `0x854300` | `0x755300` | `0x839D8` |
| `.rodata` | `0x8D7D00` | `0x7D8D00` | `0x9D6A8` |
| `.sdata` | `0x975580` | `0x876580` | `0x23FA` |

For these mapped sections, `file_offset = VA - 0xFF000`. Use section mapping in
`tools/inspect_elf.py` rather than applying this formula to unmapped/BSS addresses.
The single load segment starts at VA `0x100000`, file `0x1000`, with file size
`0x87797A` and memory size `0x9044A0`.

```bash
# Only disassembly needs the optional dependency; Python 3.10+.
python -m pip install capstone
python tools/inspect_elf.py /path/to/SLUS_215.82 info
python tools/inspect_elf.py /path/to/SLUS_215.82 verify
python tools/inspect_elf.py /path/to/SLUS_215.82 strings 'roster|uniform|schedule'
python tools/inspect_elf.py /path/to/SLUS_215.82 disasm 0x6b19d0 0x6b1e80
python tools/inspect_elf.py /path/to/SLUS_215.82 calls 0x6f7bc0
python tools/inspect_elf.py /path/to/SLUS_215.82 xrefs 0x93f608
```

`verify` checks the exact executable SHA-256 and 35 instruction fingerprints.
It verifies the evidence locations, not a patch or feasibility conclusion.
Capstone is not a full R5900 decoder. The helper explicitly handles LQ/SQ and
three-operand MULT/MULTU; unsupported MMI words remain raw. Address xrefs are
LUI/immediate candidates, and call searches find direct J/JAL only. Indirect
calls, branch delay slots, code/data boundaries, and register lifetimes need
manual review. Do not use a global search-and-replace of integer constants.

## Corrections that supersede earlier notes

- Runtime team objects occupy **728 bytes (`0x2D8`)**; 30-slot serialized records
  occupy **727 bytes**, not 723. The four-byte serialized roster count matters.
- The stock 491-byte prefix is **a four-byte total-record count plus a 487-byte
  empty sentinel team record**, rather than an unidentified global header.
- Count **153 includes the sentinel plus 152 playable teams**. The maximum stock
  art ID happens also to be 153; this is not the explanation of the file count.
- The serialized 288-byte tail starts at ISO `0x18F` / save `0x1B7`. Its first byte
  is not a separately serialized padding byte. Runtime padding at `0x1B3` is omitted.
- That tail is associated with **custom-ballpark data**, not four lineup arrays.
  Lineups and defensive assignments live in each roster slot's role DWORD.
- The analyzed save has **4035 serialized general records**, of which **3826**
  are populated (Default, 3800 stock players and 25 CAP reserves); the other
  209 are zero. It is not a 4096-record array. The real record begins 56 bytes
  before the first-name anchor: `[attributes][first name][last name]`.
- Executable general-player pool/table capacity is **4035**, not a proven 4096
  player-index ceiling. No absolute 12-bit player-index limit was established.

## Team serialization: confirmed

`0x6F8C00` is the roster-file loading path: references `roster.bin` at string
VA `0x93F608` (`0x6F8C18`/`0x6F8C24`) and calls the team-table serializer
`0x6B1CC0` at `0x6F8C50`. Table serialization reads/writes a DWORD count and
iterates that count (`0x6B1E50..0x6B1E7C`). On loading it allocates count times
`0x2D8` (`0x6B1DD0..0x6B1DDC`) and initializes team vtables at runtime `+0x2D4`.

The individual team serializer is `0x6B19D0`. Its call sequence gives this map:

| Runtime offset | Serialized offset | Bytes | Meaning |
|---:|---:|---:|---|
| `0x000` | `0x000` | 8 | team key |
| `0x008` | `0x008` | 48 | school/team name |
| `0x038` | `0x038` | 16 | abbreviation |
| `0x048` | `0x048` | 40 | city |
| `0x070` | `0x070` | 32 | nickname |
| `0x09C` | `0x090` | 4 | metadata DWORD, semantics unresolved |
| `0x090` | `0x094` | 12 | metadata block, semantics unresolved |
| `0x0A0` | `0x0A0` | 16 | packed metadata |
| `0x0B0` | `0x0B0` | 16 | additional metadata |
| stack temporary | `0x0C0` | 4 | serialized roster slot count |
| `0x0C0 + 8*s` | `0x0C4 + 8*s` | 4 | slot player ID |
| `0x0C4 + 8*s` | `0x0C8 + 8*s` | 4 | slot role DWORD |
| `0x1B0` | `0x0C4 + 8*n` | 3 | starting rotation slot indexes |
| `0x1B4` | `0x0C7 + 8*n` | 288 | custom-ballpark-associated block |
| `0x1B3`, `0x2D4` | omitted | — | runtime padding / team vtable |

`s` is the slot index and `n` the serialized count. Record length is
**`487 + 8*n`**: 487 for the stock empty sentinel, 687 for 25 slots, and 727
for 30 slots. This is a serialization formula, not permission to feed an
unmodified engine more than 30 slots.

`0x6B1BFC` initializes the serialized count to 30; the four-byte stream operation
at `0x6B1C10` overwrites the temporary on input. Slot traversal uses that input
count (`0x6B1C18..0x6B1C60`), but its destination is the fixed runtime array.
A count of 34 would overwrite rotation/ballpark fields without a runtime layout
change. The tail operation requests `0x120` bytes at `0x6B1C8C`.

### Sentinel and file framing

| File | Count DWORD | Sentinel start | Sentinel slots / bytes | First playable team |
|---|---:|---:|---:|---:|
| decoded stock `roster.bin` | `0x000`, value 153 | `0x004` | 0 / 487 | `0x1EB` |
| supplied `Rost1.sav` | `0x1DE8`, value 153 | `0x1DEC` | 30 / 727 | `0x20C3` |

Stock equality: `4 + 487 + 152*687 = 104915`. The stock sentinel is zero-filled;
the save sentinel has nonzero poison-looking slot bytes and must be preserved.
The editor's `GLOBAL_HEADER_SIZE = 491` remains a compatible stock profile that
preserves the count and sentinel together. It is not a generic expanded-file parser.
The save's first playable team is file-table record 1; editor index 0 excludes
that sentinel. Keep these index spaces separate from art IDs and player IDs.

## Roster limits and player pools: confirmed evidence

| VA | Raw instruction word | Observation |
|---:|---:|---|
| `0x6B1BFC` | `0x2402001E` | serialized roster count initialized to 30 |
| `0x6B1DD0` | `0x240402D8` | team allocation stride 728 |
| `0x6F8A0C` | `0x240302D8` | team-table constructor stride 728 |
| `0x6F8B78` | `0x240302D8` | team-table accessor stride 728 |
| `0x6F805C` | `0x2862001E` | player-ID lookup loop, limit 30 |
| `0x6F85A4` | `0x2862001E` | roster search/check, limit 30 |
| `0x6F8838`, `0x6F8910` | `0x2E02001E` | roster enumeration loops, limit 30 |
| `0x6F8104` | `0x3843001E` | lookup not-found sentinel compared with 30 |
| `0x6F7A0C` | `0x240600F0` | clear 240 bytes, i.e. 30 eight-byte slots |
| `0x19C558` | `0x2862001A` | validation branch distinguishes counts below 26 |
| `0x19F684` | `0x24050FC3` | general player pool capacity 4035 |
| `0x19F6C8`, `0x19F6FC`, `0x19F730` | `0x24070FC3` | general/LH/RH tables receive capacity 4035 |
| `0x1A04E4` | `0x24050672` | pitcher pool capacity 1650 |
| `0x1952E4` | `0x2E420019` | created-player initialization loop, 25 slots |

The validation call to `0x6F8800` at `0x19C54C` obtains a roster count; the
`>=26` branch assigns flag 1 at `0x19C568`. The adjacent lower bound uses 15
and distinguishes counts of at least 16. Other position/rotation checks also
exist. Thus 30 storage slots do not establish permission for 30 active players;
this validation path must be investigated/patched for 34.

General manager initialization `0x19F650` supplies 4035 to the ID pool and
attribute tables. Generic table constructor `0x1A0C38` stores the capacity at
object `+0x1C` (`0x1A0C6C`). General constructor `0x1BBC08` allocates capacity
×84 (`0x1BBC20..0x1BBC40`); batting constructor `0x1BE2D8` allocates capacity
×16 (`0x1BE300..0x1BE304`). Additional statistics/auxiliary tables receive the
same 4035 repeatedly through `0x19F904`. Capacity changes need a full manager
and consumer audit, not just editing the first pool allocation.

Pitcher manager `0x1A04B0` uses 1650 and passes the capacity to pitcher
constructor `0x1B89F8` (call argument at `0x1A0528`). The stock DAT has 1609
rows; the save has 1634 populated rows including 25 reserves and 16 zero rows,
for a full serialized capacity of 1650. Extra
pitchers may require expansion of this separate pool even before general
player capacity is exhausted.

### Create-a-Player and the requested alternative

The user explicitly accepts removing Create-a-Player/menu support in favor of
34 game-generated players/team editable through the external roster editor.
Treat that as the intended future design, not a request to preserve CAP.

Initialization allocates 25 small objects (`0x194810` loop setup), and calls
`0x197FE8` at `0x1952A8` in a loop bounded by 25 at `0x1952E4`.
`0x197FE8` constructs ID-hash input strings `%dcreated%d` (VA `0x8EFB90`) and
`%d,player%d` (VA `0x8EFBA0`) before calling `0x196398`. This directly ties a
25-slot initialization path to created players. The 25 reserve records at save
indexes 3801..3825 also join pitcher reserve indexes 1609..1633 through the
same 25 IDs. Their exact lifecycle still needs a controlled CAP save comparison. Hiding the menu does not remove allocation,
initialization, serialization, or references to the pool.

For 152 teams at 34 players: `152*34 = 5168`, plus a default record = **5169**
with CAP removed. This is 1368 additional roster players versus 3800 stock,
and exceeds the confirmed 4035 capacity by **1134**. Reclaiming 25 CAP entries
cannot solve this deficit. With CAP retained the minimum is 5194 instead.

The supplied save proves that the game materializes names for stock player
records; it does **not** prove it creates nine extra fully attributed player
records/team on demand. The safest first hypothesis is to preseed additional
IDs and complete general/batting/pitcher DAT rows, expand their roster links,
and reuse the existing name-generation path after checking how it selects
eligible rows. Genuine automatic creation of missing players also needs a
creation/registration routine, ratings generation, position balance, and ID
collision handling. That routine has not been traced completely.

## Packed save table framing and batting correction

General serializer **`0x1BE270`**, batting serializer **`0x1BEF48`**, and
pitcher serializer **`0x1B9C78`** each call generic table serializer `0x1A14F8`,
then bulk-transfer `object[+0x1C] * record_size`. The generic helper transfers
four bytes from object `+0x14` (`0x1A1514`), not a row count. It is the table's
stored ID/hash field; general/LH/RH headers equal `0xF58F3C1B` in the sample,
while the pitcher header is `0x19FC5623`. The constructor's row capacity governs
the bulk length. Do not mistake these header DWORDs for player record bytes.

| Array | Physical first record | Full serialized rows | Populated rows | End, exclusive |
|---|---:|---:|---:|---:|
| general, 84 bytes | `0x2C407` | 4035 | 3826 | `0x7F003` |
| LH batting, 16 bytes | **`0x7F007`** | 4035 | 3826 | `0x8EC37` |
| RH batting, 16 bytes | **`0x8EC3B`** | 4035 | 3826 | `0x9E86B` |
| pitcher, 20 bytes | `0xF22E3` | 1650 | 1634 | `0xFA3CB` |

The 209 general/LH/RH surplus records and 16 pitcher surplus records are zero
in this sample. General array end is exactly the LH header; LH array end is
exactly the RH header. These equalities and bulk serializers independently
confirm the full capacities. `SAVE_PLAYER_RECORDS=3826` and
`SAVE_PITCHER_RECORDS=1634` in the backend describe its populated/editable range,
not the full on-disk arrays; separate capacity constants document the latter.

Earlier batting bases `0x7F003` / `0x8EC37` were **four bytes early**. Previously
mapped fields still hit the same absolute bits because their offsets included
an extra 32 bits, but that interpretation concealed the last word of each real
record behind the next record slice. Correct physical records have contact
at bit 0, power at 7, hit tendencies at 14..31, chase/take/miss at 32..67,
LF/CF/RF/HR at **68/75/82/89, all seven bits**, and
**FB/LD/GB percentages at 96/103/110, all seven bits**. Remaining bits 117..127
are not assigned final meanings. All 27 mapped fields match both 3801-row
stock/default DAT tables exactly at these bases.

Runtime batting getter `0x1BE458` dispatches through table `0x8F3690`.
Percentage handlers start at `0x1BE694` (LF), `0x1BE6AC` (CF), `0x1BE6C4` (RF),
`0x1BE6DC` (HR), `0x1BE6F4` (FB), `0x1BE70C` (LD), and `0x1BE724` (GB).
LF/CF/RF shift record word `+8` by 4/11/18 and use the shared `0x7F` mask at
`0x1BE738`; HR shifts by 25. FB/LD/GB read word `+12` at 0/7/14 and mask seven
bits. Earlier percentage widths 6/5/6/4 were based on stock maxima rather than
field boundaries. The Default template's CF=34 exposed the five-bit error.
The inspector fingerprints shifts at `0x1BE6A8`, `0x1BE6C0`, `0x1BE6D8`,
`0x1BE6F0`, and the mask at `0x1BE738`.

This pass corrects the backend bases/bitfields and exposes FB/LD/GB percentage
editing in the GUI. These are confirmed stock-format corrections, not roster
expansion. See [save_player_format.md](save_player_format.md) for exact maps and
`tools/verify_stock.py` for reproducible cross-file, reserve and preservation checks.

## Role DWORD: getters/setters confirm the packing

Runtime slot role is at team `+0x0C4 + 8*s`; its serialized location is
`+0x0C8 + 8*s`. The 288-byte tail is unnecessary for storing these assignments.

| Bits | Encoding | Executable evidence |
|---|---|---|
| 0..3 | defense selector 0 | getter `0x6F8328`, setter `0x6F8390` |
| 4..7 | defense selector 1 | same getter/setter; selector 3 setter updates both |
| 8..14 | decimal batting pair, e.g. 44 means 4/4 | getter `0x6F8118`, setter `0x6F8168` |
| 15..17 | three-bit pitching role | getter `0x6F8448` |
| 18..20 | another three-bit field, semantics unresolved | getter `0x6F85C8` |
| 21..31 | incompletely mapped | preserve |

Batting getter extracts seven bits, divides by a divisor selected from the
DWORD table at `0x941DC0`, then takes `%10`. The divisors are **10, 1**:
selector 0 is the **tens** digit, selector 1 the **ones** digit. Setter selector
3 updates both. Frontend calls at `0x7A9EC4` and `0x7A9EE4` fetch both selectors.
Defense selector 3 getter resolves to the low nibble; setter 3 writes both.

The editor calls these A/B and also offers vs-RHP/vs-LHP aliases based on the
user's description of the game's default/secondary lineup screens. Caller
semantics establishing which engine selector corresponds to which pitcher hand
are still unverified; equal stock channels cannot prove that association.
Starter setter `0x6F8650` sets role `0x8000` at `0x6F8680` and updates the
three-byte rotation. Rotation search `0x6F8618` uses length 3 / `0xFF` sentinel.
The known stock role buckets remain 0, `0x8000` (starters), `0x10000`, `0x18000`,
and `0x28000`; exact relief labels and closer label still need UI-controlled diffs.

## Team tail: custom ballpark, not spare roster storage

Team accessor `0x6F87F0` returns `team+0x1B4`. Copy helper `0x6F87D0` passes
that area to `0x4543D0`. Frontend callers include `0x787134` and `0x787384`.
The associated constructor `0x4542A8` initializes an object of **`0x108` bytes**
(allocation at `0x194880`, object vtable `+0x104`), using defaults `0x4542E0`:

- 34 floats at `+0x08..+0x8C` set to 240.0 (`0x43700000`);
- 17 floats at `+0x90..+0xD0` initialized from six times a global float;
- 17 bytes at `+0xD4..+0xE4`;
- packed fields at `+0xF0`;
- name at `+0xF4` initialized to `Ballpark` (string VA `0x923BE0`).

Function `0x454A30` resets that same object and accesses these debug keys:

| String VA | Key | Code reference |
|---:|---|---:|
| `0x923BF0` | `debug_cbp_stadium_wall` | `0x454A64` / `0x454A70` |
| `0x923C08` | `debug_cbp_stadium_style` | `0x454A80` / `0x454A88` |
| `0x923C20` | `debug_cbp_stadium_field` | `0x454AB8` / `0x454AC0` |
| `0x923C38` | `debug_cbp_stadium_background` | `0x454AE0` / `0x454AE8` |

This establishes the custom-ballpark association. It does **not** fully map
all `0x120` serialized bytes: the object is `0x108` bytes, leaving an additional
`0x18` in the serialized block whose purpose remains unresolved. Some runtime
object content may include pointers/vtables. Preserve the complete block and
trace copy/initialization behavior before moving or synthesizing it.

## Conferences and realignment

The supplied `conf.dat` has 16 rows, IDs 1..16. Fields are `conf_fullname`,
`conf_abbr`, `conf_assetid`, `conf_schedulename`, `conf_divisionnum`,
`conf_division1name`, `conf_division2name`. Schedule keys, in row order:
`acc`, `bigeast`, `bigten`, `big12`, `bigwest`, `confusa`, `mizzval`, `mtnwest`,
`pac10`, `patriot`, `sec`, `sunbelt`, `wac`, `wcc`, `soc`, `aten`.

Team metadata at runtime/serialized `+0xA0` contains location bits 0..5,
conference bits 6..10, and division bit 11. Getters are `0x6F7BE0`,
`0x6F7BC0`, and `0x6F7BD0` respectively. Conference ID has 5-bit encoding
(0..31), but only 16 conference rows are provisioned by initialization.
The conference constructor call `0x1B4338` receives **16 at `0x194928`**.
Its parser uses the retained `conferencetable.cpp` source-path string at
`0x8F1538` (`0x1B4414`) and allocates count × `0x98` bytes (`0x1B443C..0x1B4448`).
Two conference-field setter cases at `0x1B3FE0` clamp values to 31 and 3;
these should not be assigned final schema meanings without confirming dispatch.

Membership enumeration `0x6ECF30..0x6ECF94` iterates a dynamic team count
(from `0x19B710`), reads team conference (`0x6ECF3C`) and division (`0x6ECF54`),
and appends matches subject to caller output capacity. This supports a
**data-driven realignment hypothesis**. Inspect those caller capacities too.

The executable references `database\\schedule.big` at string VA `0x921B50`.
That archive was not supplied. Conference membership changes alone do not prove
that schedule templates, dynasty scheduling, tournament brackets, standings,
conference selection screens, or automatic bids will support a changed league.
The team's single division bit represents two divisions; broader division
expansion is a distinct encoding and consumer change. Five-bit conference IDs
are representable values, not evidence of 31 working conferences.

## More teams and graphical assets

Team table initialization passes **153 at `0x194978`** to `0x6F8A08`.
Auxiliary team-ID/table initialization at `0x19CB0C` and `0x19CB50` also uses
153, and a loop at `0x1C120C` compares against 153 (consumer semantics not yet
fully identified). These coexist with the dynamic file-table count described
above. Appending a record and raising only the roster file count is insufficient.
Team statistics, selectors, schedules, dynasty tables, and save counts need auditing.

The confirmed primary art ID getter `0x6F7CD0` reads bits 1..9 of team `+0xA4`.
`0x6F7D00` reads additional nine-bit fields at bits 10..18 and 19..27. In stock
data those three IDs agree; getters `0x6F7C60` / `0x6F7C98` also read nine-bit
fields in `+0xA0` at bits 12..20 / 21..29. Matching values in stock do not
establish identical intended semantics for every copy. Their encodings can
hold up to 511, but that is not a supported-team-count guarantee. Stock IDs
skip 50 and reach 153; assigning the skipped ID is not proven safe.

Logo loading has active evidence, not just an isolated string: `0x1884E4`
calls the art ID getter and `0x1884F8` formats **`../logos/a%03d.swf`** from
string VA `0x8EDD80`. Frontend/logo archive names also exist in the executable.
The corresponding art archives were not supplied, so their actual internal
entries, texture formats, and archive rebuild acceptance remain to be examined.

### Uniform mapping has a narrower path

`uniform.bin` is referenced at VA `0x922148` and loaded by `0x43D768`:

- `0x43D7B4` reads a 16-bit entry count; later code sign-extends this count;
- `0x43D7C8..0x43D7D0` allocates count ×7 bytes;
- records are seven bytes, copied individually;
- `0x43D8B8` searches with two keys, truncated to eight bits by `0x43D8BC`
  and `0x43D8C4`, matching record bytes 0 and 1;
- the remaining five bytes are packed uniform parameters, incompletely mapped.

At `0x43D6AC`, an object field `+0xDC` must be **less than 154** to use the
lookup path; otherwise it takes fallback `0x43DA20`. Lookup keys come from
object `+0xD0` and `+0xCC`. Their complete relationship to team ID/art ID/jersey
selection is not yet proved, so 154 is a **local legacy gate**, not a global
team maximum. It must be audited for added teams, especially stock-max-plus-one.
Eight-bit keys also create a distinct width issue beyond 255 if the relevant
ID grows that far. A nine-bit logo field does not solve a byte-key uniform path.

Adding a named record does not create logos, uniforms, frontend graphics,
announcer audio, stadiums, or their mappings. An initial added-team experiment
should borrow known working assets before testing new archive entries; separately
verify logo loading, home/away uniform selection, on-field textures, menus,
and missing-asset fallback behavior. Replacing an existing team's assets is a
smaller first experiment than adding a new team identity everywhere.

## Hypotheses and next experiments

These are engineering hypotheses, not tested patches or time estimates.

| Requested change | Assessment | Required coordinated work | First useful experiment |
|---|---|---|---|
| Realign existing teams among current conferences | Highest confidence | team conference/division bits; scheduling/bracket validation | move one existing team; compare membership, standings, schedule, dynasty |
| Replace an existing team and its graphics | High relative confidence | strings, all relevant art references and archive members, uniform mapping | replace one logo and one uniform with unchanged IDs |
| Add playable teams | Plausible, broader change | dynamic serialized count plus fixed 153 consumers, player pools, selectors, stats, saves, scheduling and art | add one record with borrowed assets and unique IDs; test exhibition then dynasty |
| Add conferences | Plausible but less established | constructor capacity 16, new conf rows/art/schedule keys, membership output buffers and downstream consumers | add one conference; inspect schedule archive before a dynasty test |
| 34 players on every team | Plausible, coordinated runtime and database change | layout/strides, 30-slot loops and sentinel, 25-player validation, >=5169 general rows, pitcher/stats pools, all serializers and editor profiles | first prove >25 active with existing storage, then resize one team, then expand every team |
| Remove CAP; generate 34 editable players/team | Accepted design, generation path unresolved | remove CAP lifecycle safely; create/register complete extra rows or preseed DAT rows, extend name generation and save/editor handling | trace boot name-generation iteration and verify an additional preseeded row receives a name |

A straightforward **hypothetical** inline-layout expansion from 30 to 34 slots
adds 32 bytes/team: runtime rotation `0x1B0 -> 0x1D0`, ballpark block
`0x1B4 -> 0x1D4`, team vtable `0x2D4 -> 0x2F4`, stride `0x2D8 -> 0x2F8`
(760 bytes). Serialized 34-slot records would be `487+272 = 759` bytes.
Every allocation, accessor, copy, destructor, field displacement, stack temporary,
serializer, and loop using the old layout needs a complete audit. These numbers
are a candidate design, not approved patch operands or a complete site list.
An external roster-array redesign is another possibility but would involve even
more pointer/consumer changes. Never overwrite the ballpark block as "free" slots.

The extra 1368 players require about 158,688 bytes just for 84-byte general and
two 16-byte batting rows versus populated stock data, before names/ID lookup
structures, pitchers, statistics, and other pools. This is not a total PS2
memory budget estimate. Profile heap and overlay/save buffer limits in an emulator.
No complete ID-index packing limit, overall heap margin, or menu widget limit
has been established.

Recommended order for the next agent:

1. Run the hash/fingerprint check; import the ELF with proper PS2/R5900 support.
   Name functions from this address map; preserve originals and build a patch manifest.
2. Trace the validator and team getters in PCSX2. Establish an unmodified baseline
   for exhibition, roster editing, save/reload, and one dynasty simulation.
3. Test one existing-team conference change without adding teams; inspect
   `schedule.big` and its callers before promising conference expansion.
4. Trace boot random-name generation and CAP registration separately. Determine
   table row counts, name eligibility, ID generation, and whether any indexes
   are narrower than required for 5169 records.
5. Audit all team layout references, 30/25 limits, 4035/1650 allocations, 153
   team consumers, and 16-conference consumers by data flow, not raw constants.
6. Expand a single subsystem per experiment. Verify 26 active players first,
   then storage/serializer changes, then a full 34-player database. Recheck
   rotations, both batting/defense channels, ballpark data, substitutions, stats,
   save/reload, and dynasty-generated/recruited players.
7. Add one team using known assets, then one new art entry, then one conference.
   Scale only after each complete load/play/save cycle works.
8. Add explicit versioned profiles to the editor for expanded databases/saves.
   Existing fixed constants, sentinel skipping and ID-map scanning are stock-only;
   do not silently reinterpret expanded files as stock or migrate saves by offsets alone.

Needed artifacts for future work: `database/schedule.big`, actual logo/frontend
archives, `uniform.bin` and team texture archives, controlled saves with one CAP
player and unequal lineup channels, and emulator observations after isolated
changes. No modified ISO/executable or graphic assets were produced in this pass.

## What this pass changed

- Added the read-only ELF inspector, exact-build fingerprint verification, and
  reproducible stock-profile cross-file/preservation checks.
- Mapped team serializers, sentinel framing, runtime layout, limits, player pools,
  role getters/setters, conference construction/membership, ballpark association,
  logo path and uniform lookup evidence.
- Corrected full serialized versus populated counts, batting bases/percentage
  widths; mapped FB/LD/GB and exposed those fields in the editor. Corrected
  conflicting format notes and updated README/editor status.
- Repaired literal `\\n` corruption in the Python launcher/package initializer;
  added generated-file/source-binary ignores and removed a GitHub connectivity probe.
- Kept original inputs, opaque data, and useful research; excluded duplicate
  binaries, temporary dumps and generated caches from the repository.

Validation results and immediate unresolved work are recorded in
[handoff.md](handoff.md). This document takes precedence over older conversational
hypotheses about executable limits.
