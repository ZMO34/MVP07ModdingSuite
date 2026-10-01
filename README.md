# MVP 07 Modding Suite

Reverse-engineering and tooling project for **MVP 07: NCAA Baseball**.

The immediate focus is the game's database/roster formats, beginning with
`DATABASE.BIG` and its embedded `roster.bin`. The long-term goal is a Python
GUI suite that can edit rosters and other moddable game assets without requiring
manual hex editing.

## Current status

- EA `BIGF` container structure identified for the supplied `DATABASE.BIG`.
- Lossless BIG extractor implemented in `tools/extract_big.py`.
- `roster.bin` extracted and fingerprinted.
- Initial evidence indicates `roster.bin` uses bit-packed / non-byte-aligned
  fields rather than ordinary C strings.
- Companion attribute tables are being mapped alongside roster data.

See `docs/research/database_big_roster.md` for evidence and offsets.

## Research rules

- Preserve originals.
- Prefer controlled differential tests over guesses.
- Label findings CONFIRMED, LIKELY, or SPECULATIVE.
- Writers must preserve unknown bits/bytes until their meaning is established.
- Keep research concise enough that ChatGPT/Codex can quickly recover project
  state from the repository.
