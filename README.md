# MVP 07 Modding Suite

Reverse-engineering and tooling project for **MVP 07: NCAA Baseball**.

The immediate focus is the game's database/roster formats, beginning with
`DATABASE.BIG` and its embedded `roster.bin`. The long-term goal is a Python
GUI suite that can edit rosters and other moddable game assets without manual
hex editing.

## Current status

- EA `BIGF` container structure identified.
- Lossless BIG extractor implemented in `tools/extract_big.py`.
- EA RefPack/QFS compression positively identified and decoded.
- `roster.bin` decompresses to 104,915 bytes.
- Its top-level structure is now confirmed as a 491-byte global region followed
  by exactly 152 fixed-size 687-byte team records.
- Each team contains 25 8-byte roster slots whose little-endian player IDs join
  directly to `attrib.dat`, `rhattrib.dat`, `lhattrib.dat`, and
  `pitcher.dat`.
- Three per-team bytes have been confirmed as roster-slot indexes for the
  three-man starting rotation.
- The companion DAT files decompress to human-readable schema/data tables.

See `docs/research/database_big_roster.md` for the current binary map.

## Research rules

- Preserve originals and unknown bytes.
- Prefer deterministic cross-file evidence over guesses.
- Label fields CONFIRMED, PARTIALLY MAPPED, or UNKNOWN.
- Writers must preserve unknown data until its meaning is established.
- Keep research concise enough that ChatGPT/Codex can quickly recover project
  state from the repository.
