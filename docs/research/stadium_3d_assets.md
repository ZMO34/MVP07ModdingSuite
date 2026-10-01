# Stadium and 3D asset research

Updated **2026-10-01** from the vanilla MVP 07: NCAA Baseball PS2 ISO
stadium folder and direct comparisons of `VENUDAY.BIG`, `VENUDUSK.BIG`, and
`VENUNITE.BIG`.

This document records only observations confirmed from supplied game files.
Interpretations that still need an in-game or format-level test are kept in a
separate section.

## Confirmed archive structure

The stadium directory contains standard EA `BIGF` archives. Internal members
are individually named resources rather than one opaque stadium blob.

The supplied folder contains:

- 23 authentic college/CWS stadium packages.
- 10 generic stadium packages: `G001DAY.BIG` through `G010DAY.BIG`.
- 2 `MIN` packages: `MIN1DAY.BIG` and `MIN2DAY.BIG`.
- 3 variants of one `VENU` package: `VENUDAY.BIG`, `VENUDUSK.BIG`,
  and `VENUNITE.BIG`.
- Shared `CSASSETS.BIG` and `LIGHTING.BIG` archives.

The ten generic stadium archives should be treated as stock resources and not
assumed expendable. Their intended use and selection behavior should be preserved
until runtime tests prove otherwise.

## Authentic stadium BIG mapping

The vanilla archive names line up with the game's 23 authentic stadiums:

| BIG | Stadium / program |
|---|---|
| `RBLTDAY.BIG` | Rosenblatt Stadium / College World Series |
| `RECKDAY.BIG` | Reckling Park / Rice |
| `CHANDAY.BIG` | Russ Chandler Stadium / Georgia Tech |
| `HAWKDAY.BIG` | Hawks Field at Haymarket Park / Nebraska |
| `ABOXDAY.BIG` | Alex Box Stadium / LSU |
| `ARODDAY.BIG` | Mark Light Field / Miami |
| `DISHDAY.BIG` | Disch-Falk Field / Texas |
| `DOUGDAY.BIG` | Doug Kingsmore Stadium / Clemson |
| `FRANDAY.BIG` | Frank Eck Stadium / Notre Dame |
| `PACKDAY.BIG` | Packard Stadium / Arizona State |
| `SWAYDAY.BIG` | Swayze Field / Ole Miss |
| `LINDDAY.BIG` | Lindsey Nelson Stadium / Tennessee |
| `FERRDAY.BIG` | Baylor Ballpark / Baylor |
| `JOHNDAY.BIG` | The Ballpark at St. John's / St. John's |
| `SUNKDAY.BIG` | Sunken Diamond / Stanford |
| `GOODDAY.BIG` | Goodwin Field / Cal State Fullerton |
| `KINDDAY.BIG` | Jerry Kindall Field at Frank Sancet Stadium / Arizona |
| `DICKDAY.BIG` | Dick Howser Stadium / Florida State |
| `DEDEDAY.BIG` | Dedeaux Field / USC |
| `CLRKDAY.BIG` | Clark-LeClair Stadium / East Carolina |
| `DVENDAY.BIG` | Davenport Field / Virginia |
| `CBUMDAY.BIG` | Baum Stadium / Arkansas |
| `DUDYDAY.BIG` | Dudy Noble Field / Mississippi State |

The mapping above is useful for cross-checking any team-to-stadium field found
elsewhere in the database or executable.

## Confirmed team-to-stadium resolution (2026-10-01)

The correct serialized/runtime team selector is `(LE_DWORD(+0xA8) >> 4) & 0x3F`.
Getter `0x6F7C30` explicitly shifts **4**, not 3, and masks 63; setter
`0x6F7C40` preserves unrelated bits. Earlier nine-bit/52-distinct-value guesses
combined several packed fields and are superseded.

On the executable SHA-256 recorded in [executable.md](executable.md), resolver
`0x197D50` indexes three 34-entry selector→resource-index tables at
`0x8F3F90`, `0x8F4018`, `0x8F40A0` for mode 0/1/2. Missing entries are `-1`;
it tries the requested mode, then the second, third and first tables in that
order. Resource indexes refer to the **38-entry** string pointer table at
`0x85A4D8`, whose size is also observed in search loop `0x427588` (38).
Selector numbers are not resource-pointer indexes.

| Selector(s) | Resolved resource stems in order |
|---|---|
| 0..5 | RBLTDAY, CHANDAY, HAWKDAY, ABOXDAY, ARODDAY, DISHDAY |
| 6..11 | DOUGDAY, FRANDAY, PACKDAY, SWAYDAY, LINDDAY, RECKDAY |
| 12..17 | FERRDAY, JOHNDAY, SUNKDAY, GOODDAY, KINDDAY, DICKDAY |
| 18..22 | DEDEDAY, CBUMDAY, CLRKDAY, DVENDAY, DUDYDAY |
| 23..32 | G001DAY through G010DAY |
| 33 | VENUDAY / VENUDUSK / VENUNITE by mode 0/1/2 |

All three modes fall back to the same DAY resource for selectors 0..32 in
these initial tables. This is static resource resolution, not proof of all
lighting or runtime overrides. MIN1DAY/MIN2DAY are present in the resource
pointer table but not these selector tables. Values 34..63 fit the field but
would index outside the 34-row tables: no support for them is established.

| Stock team | Selector | Resolved initial resource |
|---|---:|---|
| LSU | 3 | ABOXDAY.BIG |
| Georgia Tech | 1 | CHANDAY.BIG |
| Tennessee | 10 | LINDDAY.BIG |
| Arkansas | 19 | CBUMDAY.BIG |
| East Carolina | 20 | CLRKDAY.BIG |
| Georgia | 24 | G002DAY.BIG |
| Virginia | 25 | G003DAY.BIG |
| Mississippi State | 25 | G003DAY.BIG |

Virginia and Mississippi State have authentic archives/table entries but stock
team records select a generic park. Archive presence does not establish actual
stock assignment. Across 152 teams: 20 records select authentic parks and 132
select generics; there are 25 distinct selectors. Generic counts are G001=4,
G002=36, G003=50, G004=29 and G006=13. All ten generic resources remain preserved,
including ones not selected by these stock records. Runtime matchup/dynasty or
frontend overrides still need checking.

## Standard stadium contents

Normal stadium BIGs use a highly regular resource layout. A standard package
contains named model/render pairs, textures, collision/configuration data and
animation/config tables.

Observed model/render pairs include:

- `mstadium.ord/.orl`
- `mfield0.ord/.orl`, `mfield1.ord/.orl`, `mfield2.ord/.orl`
- `crowd.ord/.orl`
- `net.ord/.orl`
- `jumbo.ord/.orl`
- `cammen.ord/.orl`
- `mshadow.ord/.orl`
- `removable.ord/.orl`
- `alphablend.ord/.orl`
- `colouradd.ord/.orl`
- `background0.ord/.orl`, `background1.ord/.orl`,
  `background2.ord/.orl`
- `track.ord/.orl`
- `useraligned.ord/.orl`
- `seat.ord/.orl`
- `clouds.ord/.orl`
- `mounds.ord/.orl`
- `crowdpoly.ord/.orl`
- `3dflag.ord/.orl`

Observed texture/configuration members include:

- `field0.ssh`, `field1.ssh`, `field2.ssh`
- `crowd0.ssh`, `crowd1.ssh`, `crowd2.ssh`
- `back0.ssh`, `back1.ssh`, `back2.ssh`
- `sky0.ssh` through `sky4.ssh`, plus `skyc.ssh`
- `clay.ssh`, `dert.ssh`, `brik.ssh`
- `logo0.ssh`, `logo1.ssh`, `logo2.ssh`
- `cram.ssh`, `vram.ssh`, `vfield0.ssh` through `vfield2.ssh`
- `stadium.ifo`, `remap.ifo`, `render.ifo`
- `wall.dat`, `shadow.dat`, `coll.dat`, `crowd.dat`,
  `lflrpos.dat`
- `tanim.csv`, `ganim.csv`, `flags.csv`

This proves that stadium presentation is split across multiple resource classes;
the visible park is not stored as a single monolithic model file.

## Day / dusk / night controlled comparison

`VENUDAY.BIG`, `VENUDUSK.BIG`, and `VENUNITE.BIG` each contain the same
**98 member names**.

A byte-for-byte comparison found:

- **55 of 98 members are identical across all three variants.**
- **43 of 98 members differ in at least one variant.**

Confirmed identical examples include:

- `wall.dat`
- `field0.ssh`, `field1.ssh`, `field2.ssh`
- `clay.ssh`, `dert.ssh`, `brik.ssh`
- `back0.ssh`, `back1.ssh`, `back2.ssh`
- `background0.ord/.orl`, `background1.ord/.orl`,
  `background2.ord/.orl`
- `crowd.dat`
- `crowd0.ssh`, `crowd1.ssh`, `crowd2.ssh`
- `logo0.ssh`, `logo1.ssh`, `logo2.ssh`
- `removable.ord/.orl`
- `track.ord/.orl`
- `useraligned.ord/.orl`
- `3dflag.ord/.orl`
- `render.ifo`

Confirmed variant-dependent examples include:

- `mstadium.ord/.orl`
- `mfield0.ord/.orl`, `mfield1.ord/.orl`, `mfield2.ord/.orl`
- `mshadow.ord/.orl`
- `shadow.dat`
- sky model/render pairs
- `clouds.ord/.orl`
- `alphablend.ord/.orl`
- `crowd.ord/.orl`
- `net.ord/.orl`
- `stadium.ifo`
- `coll.dat`
- `cvwcoll.ifo`
- `tanim.csv`
- `lflrpos.dat`
- `cram.ssh`

The three `mstadium.ord` files are not the same size, so the environment
variants are not merely one identical model paired with different sky textures.
Likewise, `alphablend.ord` grows substantially in the night package.

The six `sky*.ssh` textures compared in the VENU packages are identical while
the corresponding sky ORD/ORL resources differ. Time-of-day presentation
therefore cannot be described as only swapping those SSH images.

## File-level uniqueness across stadiums

The supplied stadium set shows per-stadium differences in core configuration
resources:

- `stadium.ifo`: unique for every stadium checked.
- `coll.dat`: unique for every stadium checked.
- `lflrpos.dat`: unique for every stadium checked.
- `mstadium.ord/.orl`: unique for every stadium checked.
- `wall.dat`: overwhelmingly stadium-specific; 36 distinct versions were
  observed across 38 stadium packages in the initial inventory.

This establishes that meaningful physical/configuration data is stored per
stadium rather than all stadiums being presentation skins over one global
geometry/configuration file.

## Shared assets

`CSASSETS.BIG` is a large shared archive and contains inherited MLB-era named
resources such as city/stadium CSVs. It should be treated as shared engine asset
data, not as one stadium.

`LIGHTING.BIG` is also shared stadium infrastructure.

Neither archive should be rewritten or repurposed until its consumers are
mapped.

## Relationship to MVP 05 tooling

The NCAA 07 stadium packages use the same `.ord/.orl` naming convention seen
in MVP Baseball 2005-era stadium modding. That makes the old ORD/ORL conversion
workflow a valuable compatibility target.

What is **not yet confirmed** is direct binary compatibility with MVP 05's
`ord2o`, OEdit, or reverse conversion tools. No NCAA 07 model has yet been
successfully round-tripped through those tools and boot-tested.

Do not document "MVP 05 tools work on NCAA 07" as fact until that test succeeds.

## Mod-ready conclusions

The following are safe conclusions for tooling/research design:

1. Stadium BIGs can be enumerated and their named members extracted/replaced by
   the existing BIG/RefPack infrastructure.
2. Stadium resources are modular: model/render pairs, textures, collision,
   wall/configuration data and tables are separate members.
3. The ten generic stadium packages are independent stock resources and can be
   preserved while investigating additional real-program stadium resources.
4. The VENU day/dusk/night variants provide a controlled comparison set for
   isolating environment-dependent resources.
5. Unknown members should be preserved byte-for-byte when editing a known member.
6. A future model editor/converter should operate on extracted ORD/ORL resources
   rather than treating the BIG itself as the model format.

## Still unconfirmed

These are important but must remain hypotheses until tested:

- Exact vertex/index/material structure of ORD/ORL.
- Whether NCAA 07 ORD/ORL is directly accepted by MVP 05 `ord2o`/OEdit.
- Exact semantics of `wall.dat`, `coll.dat`, `cvwcoll.ifo`, and
  `lflrpos.dat`.
- Which file is authoritative for home-run/foul boundaries.
- World-coordinate scale.
- Whether stadium IDs can reference newly added BIG files without executable
  changes.
- Maximum number of loadable stadium resources.
- Whether `MIN1/MIN2` are minigame parks and whether `VENU` is specifically
  the created-ballpark resource set.
- Whether stock real stadiums have runtime night/dusk lighting through shared
  systems despite having only a `DAY` archive in the supplied folder.
- Whether new stadium geometry can be built from Blender/glTF and converted back
  without additional platform-specific constraints.

## Recommended next tests

These are tests, not new feature goals:

1. Extract/decompress one authentic stadium's `mstadium.ord/.orl` and test
   compatibility with the historical MVP 05 conversion tools.
2. Decode and compare `wall.dat`, `coll.dat`, `stadium.ifo`, and
   `lflrpos.dat` across known parks.
3. Make a one-member texture replacement in a copied stadium BIG and verify the
   game boots and displays it.
4. After geometry conversion is understood, make a minimal geometry edit while
   preserving every unrelated member.
5. Test the confirmed `+0xA8` selector with a one-field assignment change,
   preserving all other bits; check whether frontend/dynasty overrides affect it.

The purpose of these tests is practical mod readiness: identify the smallest
safe edit path while preserving unknown data.
