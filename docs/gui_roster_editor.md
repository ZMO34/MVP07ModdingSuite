# GUI roster editor status

Initial editor architecture added 2026-10-01.

## Current capabilities

- Open `DATABASE.BIG` directly.
- Parse BIGF and RefPack/QFS members.
- Browse all 152 team records and all 25 roster slots per team.
- Resolve each roster player ID into `attrib.dat`, `rhattrib.dat`, `lhattrib.dat`, and `pitcher.dat`.
- Edit confirmed team text fields.
- Edit an initial set of player identity/general, batting, and pitching fields.
- Display inferred batting-order values when the stock role flag matches a confirmed common pattern.
- Display the confirmed team asset ID while leaving unresolved metadata explicitly unlabeled.
- Save a rebuilt `DATABASE.BIG` using conservative literal-only RefPack compression.
- Re-open the saved archive immediately as a structural verification step.

## Important limitation

The save path is structurally verified by our parser but has **not yet been game-tested in an ISO**. Keep it marked experimental until an ISO boot/gameplay test confirms EA's runtime accepts the larger literal-only RefPack streams.

## Next GUI work

- Add validation/ranges and friendly enum names.
- Add explicit lineup/rotation editing after the role bitfield is fully decoded.
- Add roster reassignment/player movement tools.
- Add undo/redo and change tracking.
- Add a faster RefPack compressor so rebuilt archives stay close to stock size.
