# MVP 07 PS2 roster-save player format

Date: 2026-10-01
Region/build analyzed: SLUS-21582
Source save SHA-256: 34dd9c930dc56eae194729b9b254451c39d721b18863a0336611e57e36415556

This document supersedes earlier notes that described the 56-byte general-player
payload as unknown/read-only.

## Evidence convention

- CONFIRMED: exact equality against the stock DAT value across every usable stock row.
- DERIVED: deterministic interpretation built from confirmed packed fields.
- STRONG INFERENCE: structure fits the binary and shared-engine UI, but stock data
  lacks enough variation to prove the user-facing label/transform.
- UNKNOWN: preserve unchanged.

## General player records

The save has 3,826 fixed 84-byte player records.

Physical layout:

```
record +0x00   56 bytes   packed general attributes
record +0x38   12 bytes   first-name buffer
record +0x44   16 bytes   last-name buffer
```

The first-name buffer for record 0 begins at save offset `0x2C43F`, so the
actual record-array base is `0x2C407`.

Rows:
- 0: Default template
- 1..3800: stock players in attrib.dat row order
- 3801..3825: 25 Create-a-Player reserve records

### Confirmed general-player bitfields

Bit offsets are relative to the start of the 56-byte packed block and use
little-endian bit numbering.

| attrib.dat field | bit | width |
|---|---:|---:|
| height | 0 | 6 |
| weight | 6 | 8 |
| primaryposition | 14 | 4 |
| secondaryposition | 18 | 4 |
| homelocation | 23 | 6 |
| year | 44 | 2 |
| bats | 47 | 2 |
| throws | 49 | 1 |
| jerseynum | 50 | 7 |
| ditty | 57 | 3 |
| starpower | 60 | 3 |
| scholarshiptenths | 64 | 4 |
| attitude | 72 | 2 |
| academic | 74 | 2 |
| swingtype | 76 | 1 |
| battingstance | 77 | 6 |
| speed | 83 | 7 |
| throwstrength | 90 | 4 |
| throwaccuracy | 96 | 4 |
| bunting | 100 | 4 |
| fielding | 104 | 4 |
| range | 108 | 4 |
| durability | 112 | 4 |
| platediscipline | 116 | 4 |
| stealing_aggressive | 120 | 4 |
| baserunning | 124 | 4 |
| skintone | 160 | 3 |
| eyecolour | 163 | 3 |
| haircolour | 166 | 3 |
| sideburns | 169 | 3 |
| facialhair | 172 | 4 |
| captype | 176 | 2 |
| capposition | 178 | 2 |
| eyeprotection | 180 | 3 |
| battinghelmet | 183 | 2 |
| catchermask | 185 | 1 |
| elbowguard | 186 | 1 |
| shinguard | 187 | 1 |
| wristbandleftarm | 192 | 2 |
| wristbandrightarm | 194 | 2 |
| socks | 196 | 2 |
| boneprofile | 224 | 5 |
| facemorphindex | 232 | 4 |

The save clamps negative stock bunting sentinel values to zero. For nonnegative
stock values the packed bunting nibble matches attrib.dat exactly.

### Appearance interpretation

`playerattrib_socks` is the three-value pants/sock-height presentation field.
The shared MVP Create/Edit Player UI labels the three choices Low / Regular /
High. The NCAA stock file uses raw values 0, 1, 2. The bitfield itself is
CONFIRMED; the exact raw-to-label ordering is HIGH CONFIDENCE and should be
presented as 0=Low, 1=Regular, 2=High unless a visual test disproves it.

`playerattrib_catchermask` is one bit. The shared MVP player editor exposes
Catcher Mask 1/2, so the natural zero-based interpretation is:
- 0 = Mask 1
- 1 = Mask 2
The bitfield is CONFIRMED; the UI-name mapping is HIGH CONFIDENCE.

`playerattrib_eyeprotection` is exactly three bits with stock values 0..7.
The NCAA UI is known to distinguish sunglasses style and eye-black state. The
binary width is exactly sufficient for 4 sunglasses states × 2 eye-black
states. Current editor decomposition:
- bit 180 / raw bit0 = eye black off/on
- bits 181..182 / raw bits1..2 = sunglasses style 0..3
This is a STRONG INFERENCE and is exposed separately in the GUI, while the raw
three-bit value remains preserved in the backend.

Other directly writable appearance fields include skin tone, eye colour, hair
colour, sideburns, facial hair, cap type, cap position, batting helmet,
elbow guard, shin guard, left/right wristband style, bone profile, and face
morph index.

### General fields not yet fully named

- attrib.dat wristbandcolour is 0 for every stock player, so a varying bitfield
  cannot be proven from stock data. Bits 188..191 are the strongest candidate.
- attrib.dat bodytype is 1 for every stock player. Bits 229..231 are value 2 in
  every stock save record and are the strongest body-type candidate, probably
  with an encoding offset. Do not make it writable as a named body type until a
  created-player save with non-default body type is available.
- attrib.dat audioid is 0 for every NCAA stock player, so the exact packed field
  cannot be isolated statistically. Bits 29..43 are zero in all stock records
  and are a plausible allocation, but remain UNKNOWN.
- attrib.dat hidden is 0 for every stock player and cannot be isolated.
- bits 128..159 contain a stock constant whose semantics are not yet named.

## Batting tables

Two 16-byte arrays indexed by player-record index:
- vs LHP: `0x7F003`
- vs RHP: `0x8EC37`

Confirmed writable fields:
- contact 32:7
- power 39:7
- 9-zone hit tendencies 46..63, 2 bits each
- chase/take/miss tendencies 64..99, 4 bits each
- LF pct 100:6
- CF pct 107:5
- RF pct 114:6
- HR pct 121:4

The low 32 bits are almost certainly the 9-zone hot/cold map plus control bits;
their exact 9-cell packing is the next batting target.

## Pitcher table

The save equivalent of `pitcher.dat` is CONFIRMED.

Base: `0xF22E3`
Record size: 20 bytes / 160 bits
Stock rows: 1609 (Default + 1608 stock pitcher rows)
Total capacity: 1634 rows = 1609 stock + 25 CAP reserve

The save also contains an explicit player-ID -> pitcher-index table. The 25 CAP
player IDs map to pitcher rows 1609..1633, proving that each of the 25 CAP slots
has reserved pitcher storage.

### Confirmed pitcher bitfields

| pitcher.dat field | bit | width |
|---|---:|---:|
| stamina | 0 | 7 |
| pickoff | 7 | 4 |
| fastball_control | 13 | 7 |
| fastball_velocity | 20 | 7 |
| pitch2_type | 27 | 4 |
| pitch2_movement | 32 | 4 |
| pitch2_description | 36 | 3 |
| pitch2_control | 39 | 7 |
| pitch2_velocity | 46 | 7 |
| pitch3_type | 53 | 4 |
| pitch3_movement | 57 | 4 |
| pitch3_description | 61 | 3 |
| pitch3_control | 64 | 7 |
| pitch3_velocity | 71 | 7 |
| pitch4_type | 78 | 4 |
| pitch4_movement | 82 | 4 |
| pitch4_description | 86 | 3 |
| pitch4_control | 89 | 7 |
| pitch4_velocity | 96 | 7 |
| pitch5_type | 103 | 4 |
| pitch5_movement | 107 | 4 |
| pitch5_description | 111 | 3 |
| pitch5_control | 114 | 7 |
| pitch5_velocity | 121 | 7 |
| pitcher_delivery | 128 | 5 |

Stamina is duplicated at bits 133..139 and is identical to bits 0..6 for every
stock pitcher. The writer updates both copies.

Stock fastball movement and fastball description are zero in every NCAA
pitcher.dat row and are not independently represented by an identifiable
varying field. The writer therefore rejects attempts to set either to nonzero.

This layout reproduces every mapped pitcher.dat value for all 1,609 stock rows
with zero mismatches.

## Roster lineup semantics

The two lineup channels in each roster-slot role DWORD are now named:
- channel A = default / vs RHP
- channel B = secondary / vs LHP

Thus:
- low nibble: defensive position vs RHP
- high nibble of low byte: defensive position vs LHP
- 7-bit decimal-pair field at bits 8..14: tens digit batting order vs RHP,
  ones digit batting order vs LHP

Pitching rotation remains the separate three roster-slot indexes stored in the
team record.
