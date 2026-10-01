# Project continuation

Read `README.md` and `docs/research/handoff.md` before changing roster or
executable behavior. The handoff links the exact-build evidence and current
format maps. Keep confirmed bytes/code evidence separate from hypotheses and
runtime-tested behavior; preserve unknown fields and original inputs.

The editor supports stock profiles only. Team/executable expansion is researched
but unimplemented. Reproduce checks with `tools/verify_stock.py` and
`tools/inspect_elf.py verify` using the matching originals named in the reports.
Do not commit game binaries, extracted assets or temporary disassembly dumps.

The current priority is practical stock modding; defer expanded rosters/teams.
Use `tools/analyze_team_audio.py` with matching DBMisc/database originals for
audio-ID joins. School/nickname selectors are in `+0xA0`, not `+0x090`.
Preserve all generic stadiums; keep new research in the existing topic reports
and link it from the handoff instead of adding duplicate status files.
