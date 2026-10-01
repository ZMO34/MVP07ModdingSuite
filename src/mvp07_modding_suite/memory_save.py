from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import zipfile


TEAM_COUNT = 152
SAVE_TEAM_RECORD_SIZE = 727
SAVE_ROSTER_SLOTS = 30
SAVE_PLAYER_RECORD_SIZE = 84
SAVE_PLAYER_RECORDS = 3826
SAVE_FIRST_NAME_SIZE = 12
SAVE_LAST_NAME_SIZE = 16
SAVE_PLAYER_ATTRIBUTE_SIZE = 56

# A save-player record is physically [56 bytes packed attributes][28 bytes names].
# _find_player_base() returns the start of the Default first-name buffer, so the
# actual fixed-record base is 56 bytes earlier.
PLAYER_GENERAL_BITFIELDS = {
    "playerattrib_height": (0, 6),
    "playerattrib_weight": (6, 8),
    "playerattrib_primaryposition": (14, 4),
    "playerattrib_secondaryposition": (18, 4),
    "playerattrib_homelocation": (23, 6),
    "playerattrib_year": (44, 2),
    "playerattrib_bats": (47, 2),
    "playerattrib_throws": (49, 1),
    "playerattrib_jerseynum": (50, 7),
    "playerattrib_ditty": (57, 3),
    "playerattrib_starpower": (60, 3),
    "playerattrib_scholarshiptenths": (64, 4),
    "playerattrib_attitude": (72, 2),
    "playerattrib_academic": (74, 2),
    "playerattrib_swingtype": (76, 1),
    "playerattrib_battingstance": (77, 6),
    "playerattrib_speed": (83, 7),
    "playerattrib_throwstrength": (90, 4),
    "playerattrib_throwaccuracy": (96, 4),
    "playerattrib_fielding": (104, 4),
    "playerattrib_range": (108, 4),
    "playerattrib_durability": (112, 4),
    "playerattrib_platediscipline": (116, 4),
    "playerattrib_stealing_aggressive": (120, 4),
    "playerattrib_baserunning": (124, 4),
    "playerattrib_skintone": (160, 3),
    "playerattrib_eyecolour": (163, 3),
    "playerattrib_haircolour": (166, 3),
    "playerattrib_sideburns": (169, 3),
    "playerattrib_facialhair": (172, 4),
    "playerattrib_captype": (176, 2),
    "playerattrib_capposition": (178, 2),
    "playerattrib_eyeprotection": (180, 3),
    "playerattrib_battinghelmet": (183, 2),
    "playerattrib_catchermask": (185, 1),
    "playerattrib_elbowguard": (186, 1),
    "playerattrib_shinguard": (187, 1),
    "playerattrib_wristbandleftarm": (192, 2),
    "playerattrib_wristbandrightarm": (194, 2),
    "playerattrib_socks": (196, 2),
    "playerattrib_boneprofile": (224, 5),
    "playerattrib_facemorphindex": (232, 4),
}

# The stock NCAA database has bodytype=1 for every player, so this field cannot
# be proven by stock-row correlation alone. Bits 229..231 are the only compact
# varying-capable gap between bone profile and face morph and contain value 2
# for all stock records. Shared-engine CAP UI uses a 3-choice body type. Keep it
# explicitly experimental until a created-player save proves the transform.
EXPERIMENTAL_BODYTYPE_BITS = (229, 3)

# SLUS-21582 packed pitcher table: 1609 stock pitcher.dat rows, 20 bytes each.
SAVE_PITCHER_BASE = 0xF22E3
SAVE_PITCHER_RECORD_SIZE = 20
SAVE_PITCHER_RECORDS = 1609

PITCHER_BITFIELDS = {
    "pitchattrib_stamina": (0, 7),
    "pitchattrib_pickoff": (7, 4),
    "pitchattrib_fastball_control": (13, 7),
    "pitchattrib_fastball_velocity": (20, 7),
    "pitchattrib_pitch2_type": (27, 4),
    "pitchattrib_pitch2_movement": (32, 4),
    "pitchattrib_pitch2_description": (36, 3),
    "pitchattrib_pitch2_control": (39, 7),
    "pitchattrib_pitch2_velocity": (46, 7),
    "pitchattrib_pitch3_type": (53, 4),
    "pitchattrib_pitch3_movement": (57, 4),
    "pitchattrib_pitch3_description": (61, 3),
    "pitchattrib_pitch3_control": (64, 7),
    "pitchattrib_pitch3_velocity": (71, 7),
    "pitchattrib_pitch4_type": (78, 4),
    "pitchattrib_pitch4_movement": (82, 4),
    "pitchattrib_pitch4_description": (86, 3),
    "pitchattrib_pitch4_control": (89, 7),
    "pitchattrib_pitch4_velocity": (96, 7),
    "pitchattrib_pitch5_type": (103, 4),
    "pitchattrib_pitch5_movement": (107, 4),
    "pitchattrib_pitch5_description": (111, 3),
    "pitchattrib_pitch5_control": (114, 7),
    "pitchattrib_pitch5_velocity": (121, 7),
    "pitchattrib_pitcher_delivery": (128, 5),
}

# SLUS-21582 MVP 07 roster-save batting tables.
# These are fixed-size runtime arrays indexed by save player index.
SAVE_LH_BATTING_BASE = 0x7F003
SAVE_RH_BATTING_BASE = 0x8EC37
SAVE_BATTING_RECORD_SIZE = 16

BATTING_BITFIELDS = {
    "lrattrib_contact": (32, 7),
    "lrattrib_power": (39, 7),
    "lrattrib_hit_ul": (46, 2),
    "lrattrib_hit_cl": (48, 2),
    "lrattrib_hit_ll": (50, 2),
    "lrattrib_hit_um": (52, 2),
    "lrattrib_hit_cm": (54, 2),
    "lrattrib_hit_lm": (56, 2),
    "lrattrib_hit_ur": (58, 2),
    "lrattrib_hit_cr": (60, 2),
    "lrattrib_hit_lr": (62, 2),
    "lrattrib_chasefb": (64, 4),
    "lrattrib_chaseslowbreak": (68, 4),
    "lrattrib_chasehardbreak": (72, 4),
    "lrattrib_takefb": (76, 4),
    "lrattrib_takeslowbreak": (80, 4),
    "lrattrib_takehardbreak": (84, 4),
    "lrattrib_missfb": (88, 4),
    "lrattrib_missslowbreak": (92, 4),
    "lrattrib_misshardbreak": (96, 4),
    "lrattrib_lf_pct": (100, 6),
    "lrattrib_cf_pct": (107, 5),
    "lrattrib_rf_pct": (114, 6),
    "lrattrib_hr_pct": (121, 4),
}


@dataclass(frozen=True)
class SavePlayerName:
    index: int
    first_name: str
    last_name: str


class MemoryRosterSave:
    def __init__(
        self,
        raw: bytes,
        team_base: int,
        player_base: int,
        source_path: Path | None = None,
        zip_member: str | None = None,
    ):
        self.raw = bytearray(raw)
        self.team_base = team_base
        self.player_base = player_base
        self.source_path = source_path
        self.zip_member = zip_member
        self.team_records = [
            bytearray(
                raw[
                    team_base + i * SAVE_TEAM_RECORD_SIZE:
                    team_base + (i + 1) * SAVE_TEAM_RECORD_SIZE
                ]
            )
            for i in range(TEAM_COUNT)
        ]
        self.player_id_to_index = self._build_player_id_index()
        self.player_id_to_pitcher_index = self._build_pitcher_id_index()

    @classmethod
    def load(cls, path: Path) -> "MemoryRosterSave":
        raw, member = _load_raw_save(path)
        team_base = _find_team_base(raw)
        player_base = _find_player_base(raw, team_base + TEAM_COUNT * SAVE_TEAM_RECORD_SIZE)
        return cls(raw, team_base, player_base, source_path=path, zip_member=member)

    def team_record(self, index: int) -> bytes:
        if not 0 <= index < TEAM_COUNT:
            raise IndexError(index)
        return bytes(self.team_records[index])

    def player_record(self, index: int) -> bytes:
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        start = self.player_base + index * SAVE_PLAYER_RECORD_SIZE
        return bytes(self.raw[start:start + SAVE_PLAYER_RECORD_SIZE])

    @property
    def general_record_base(self) -> int:
        return self.player_base - SAVE_PLAYER_ATTRIBUTE_SIZE

    def player_payload(self, index: int) -> bytes:
        """Return the player's 56-byte packed general-attribute payload."""
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        start = self.general_record_base + index * SAVE_PLAYER_RECORD_SIZE
        return bytes(self.raw[start:start + SAVE_PLAYER_ATTRIBUTE_SIZE])

    def player_general_values(self, index: int) -> dict[str, int]:
        value = int.from_bytes(self.player_payload(index), "little")
        result = {}
        for field, (bit, width) in PLAYER_GENERAL_BITFIELDS.items():
            result[field] = (value >> bit) & ((1 << width) - 1)

        # Useful derived presentation of the packed eye-protection code.
        eye = result["playerattrib_eyeprotection"]
        result["derived_eyeblack"] = eye & 1
        result["derived_sunglasses_style"] = eye >> 1
        return result

    def set_player_general_values(self, index: int, changes: dict[str, int]) -> None:
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        start = self.general_record_base + index * SAVE_PLAYER_RECORD_SIZE
        raw = bytes(self.raw[start:start + SAVE_PLAYER_ATTRIBUTE_SIZE])
        value = int.from_bytes(raw, "little")

        # Allow either the raw 3-bit eye-protection value or the two derived
        # controls. The latter decomposition is strongly inferred, not yet
        # visual-diff confirmed.
        normalized = dict(changes)
        if "derived_eyeblack" in normalized or "derived_sunglasses_style" in normalized:
            current_eye = (value >> 180) & 0x7
            eyeblack = int(normalized.pop("derived_eyeblack", current_eye & 1))
            glasses = int(normalized.pop("derived_sunglasses_style", current_eye >> 1))
            if not 0 <= eyeblack <= 1 or not 0 <= glasses <= 3:
                raise ValueError("eyeblack must be 0/1 and sunglasses style 0..3")
            normalized["playerattrib_eyeprotection"] = (glasses << 1) | eyeblack

        for field, raw_value in normalized.items():
            if field not in PLAYER_GENERAL_BITFIELDS:
                continue
            bit, width = PLAYER_GENERAL_BITFIELDS[field]
            field_value = int(raw_value)
            if not 0 <= field_value < (1 << width):
                raise ValueError(f"{field} must fit in {width} bits")
            mask = ((1 << width) - 1) << bit
            value = (value & ~mask) | (field_value << bit)

        self.raw[start:start + SAVE_PLAYER_ATTRIBUTE_SIZE] = value.to_bytes(
            SAVE_PLAYER_ATTRIBUTE_SIZE, "little"
        )

    def pitcher_record(self, pitcher_index: int) -> bytes:
        if not 0 <= pitcher_index < SAVE_PITCHER_RECORDS:
            raise IndexError(pitcher_index)
        start = SAVE_PITCHER_BASE + pitcher_index * SAVE_PITCHER_RECORD_SIZE
        return bytes(self.raw[start:start + SAVE_PITCHER_RECORD_SIZE])

    def pitcher_values(self, pitcher_index: int) -> dict[str, int]:
        value = int.from_bytes(self.pitcher_record(pitcher_index), "little")
        result = {
            field: (value >> bit) & ((1 << width) - 1)
            for field, (bit, width) in PITCHER_BITFIELDS.items()
        }
        # Fastball movement/description are omitted from this runtime packing;
        # both are zero for every stock NCAA pitcher.dat row.
        result["pitchattrib_fastball_movement"] = 0
        result["pitchattrib_fastball_description"] = 0
        return result

    def set_pitcher_values(self, pitcher_index: int, changes: dict[str, int]) -> None:
        if not 0 <= pitcher_index < SAVE_PITCHER_RECORDS:
            raise IndexError(pitcher_index)
        start = SAVE_PITCHER_BASE + pitcher_index * SAVE_PITCHER_RECORD_SIZE
        value = int.from_bytes(
            self.raw[start:start + SAVE_PITCHER_RECORD_SIZE], "little"
        )

        for field, raw_value in changes.items():
            if field in {"pitchattrib_fastball_movement", "pitchattrib_fastball_description"}:
                if int(raw_value) != 0:
                    raise ValueError(f"{field} is not independently stored in MVP 07 saves")
                continue
            if field not in PITCHER_BITFIELDS:
                continue
            bit, width = PITCHER_BITFIELDS[field]
            field_value = int(raw_value)
            if not 0 <= field_value < (1 << width):
                raise ValueError(f"{field} must fit in {width} bits")
            mask = ((1 << width) - 1) << bit
            value = (value & ~mask) | (field_value << bit)

        # Stamina is duplicated at bits 133..139 in every stock record.
        if "pitchattrib_stamina" in changes:
            stamina = int(changes["pitchattrib_stamina"])
            dup_mask = ((1 << 7) - 1) << 133
            value = (value & ~dup_mask) | (stamina << 133)

        self.raw[start:start + SAVE_PITCHER_RECORD_SIZE] = value.to_bytes(
            SAVE_PITCHER_RECORD_SIZE, "little"
        )

    def batting_record(self, index: int, side: str) -> bytes:
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        side_key = side.lower()
        if side_key in {"l", "lh", "vs_lhp"}:
            base = SAVE_LH_BATTING_BASE
        elif side_key in {"r", "rh", "vs_rhp"}:
            base = SAVE_RH_BATTING_BASE
        else:
            raise ValueError("side must be L/LH/vs_lhp or R/RH/vs_rhp")
        start = base + index * SAVE_BATTING_RECORD_SIZE
        return bytes(self.raw[start:start + SAVE_BATTING_RECORD_SIZE])

    def batting_values(self, index: int, side: str) -> dict[str, int]:
        value = int.from_bytes(self.batting_record(index, side), "little")
        result = {}
        for field, (bit, width) in BATTING_BITFIELDS.items():
            result[field] = (value >> bit) & ((1 << width) - 1)
        return result

    def set_batting_values(self, index: int, side: str, changes: dict[str, int]) -> None:
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        side_key = side.lower()
        if side_key in {"l", "lh", "vs_lhp"}:
            base = SAVE_LH_BATTING_BASE
        elif side_key in {"r", "rh", "vs_rhp"}:
            base = SAVE_RH_BATTING_BASE
        else:
            raise ValueError("side must be L/LH/vs_lhp or R/RH/vs_rhp")
        start = base + index * SAVE_BATTING_RECORD_SIZE
        value = int.from_bytes(self.raw[start:start + SAVE_BATTING_RECORD_SIZE], "little")
        for field, raw_value in changes.items():
            if field not in BATTING_BITFIELDS:
                continue
            bit, width = BATTING_BITFIELDS[field]
            field_value = int(raw_value)
            if not 0 <= field_value < (1 << width):
                raise ValueError(f"{field} must fit in {width} bits")
            mask = ((1 << width) - 1) << bit
            value = (value & ~mask) | (field_value << bit)
        self.raw[start:start + SAVE_BATTING_RECORD_SIZE] = value.to_bytes(
            SAVE_BATTING_RECORD_SIZE, "little"
        )

    def player_name(self, index: int) -> SavePlayerName:
        rec = self.player_record(index)
        return SavePlayerName(
            index=index,
            first_name=_cstr(rec[:SAVE_FIRST_NAME_SIZE]),
            last_name=_cstr(
                rec[
                    SAVE_FIRST_NAME_SIZE:
                    SAVE_FIRST_NAME_SIZE + SAVE_LAST_NAME_SIZE
                ]
            ),
        )

    def set_player_name(self, index: int, first_name: str, last_name: str) -> None:
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        first = first_name.encode("latin-1")
        last = last_name.encode("latin-1")
        if len(first) >= SAVE_FIRST_NAME_SIZE:
            raise ValueError(f"First name must be at most {SAVE_FIRST_NAME_SIZE - 1} bytes")
        if len(last) >= SAVE_LAST_NAME_SIZE:
            raise ValueError(f"Last name must be at most {SAVE_LAST_NAME_SIZE - 1} bytes")
        start = self.player_base + index * SAVE_PLAYER_RECORD_SIZE
        self.raw[start:start + SAVE_FIRST_NAME_SIZE] = (
            first + b"\0" * (SAVE_FIRST_NAME_SIZE - len(first))
        )
        lo = start + SAVE_FIRST_NAME_SIZE
        self.raw[lo:lo + SAVE_LAST_NAME_SIZE] = (
            last + b"\0" * (SAVE_LAST_NAME_SIZE - len(last))
        )

    def populated_player_names(self) -> list[SavePlayerName]:
        out = []
        for i in range(SAVE_PLAYER_RECORDS):
            rec = self.player_record(i)
            if not any(rec):
                continue
            name = self.player_name(i)
            if name.first_name or name.last_name:
                out.append(name)
        return out

    def _roster_player_ids(self) -> set[int]:
        ids = set()
        for record in self.team_records:
            for slot in range(SAVE_ROSTER_SLOTS):
                off = 0x0C4 + slot * 8
                player_id = int.from_bytes(record[off:off + 4], "little")
                if player_id:
                    ids.add(player_id)
        return ids

    def _build_player_id_index(self) -> dict[int, int]:
        roster_ids = self._roster_player_ids()

        # Stock SLUS-21582 roster saves contain a compact ID->row lookup region
        # before the packed player array. Entries are:
        #   u32 player_id, u32 player_index, u32 player_index
        # Search only that pre-player region and select a bijective mapping;
        # scanning the entire save produces false-positive index-0 triples.
        start = max(0, self.team_base + TEAM_COUNT * SAVE_TEAM_RECORD_SIZE)
        end = self.player_base
        candidates: dict[int, set[int]] = {}
        raw = self.raw
        for off in range(start, max(start, end - 11)):
            player_id = int.from_bytes(raw[off:off + 4], "little")
            if player_id not in roster_ids:
                continue
            a = int.from_bytes(raw[off + 4:off + 8], "little")
            b = int.from_bytes(raw[off + 8:off + 12], "little")
            if a == b and 1 <= a <= 3800:
                candidates.setdefault(player_id, set()).add(a)

        # Prefer the unique candidate for each stock ID. If multiple candidates
        # survive, row indices are globally unique, so greedily reject collisions.
        mapping: dict[int, int] = {}
        used: set[int] = set()
        for player_id, indexes in sorted(candidates.items(), key=lambda item: len(item[1])):
            for index in sorted(indexes):
                if index not in used:
                    mapping[player_id] = index
                    used.add(index)
                    break

        return mapping

    def _build_pitcher_id_index(self) -> dict[int, int]:
        """Find the save's explicit player-ID -> pitcher.dat-row mapping.

        The lookup region immediately before the packed pitcher array contains
        triples [u32 player_id][u32 pitcher_index][u32 same_index]. Scanning
        this bounded region yields exactly one entry for every stock pitcher
        index 1..1608. Index 0 (Default) also appears, along with a few
        byte-shift false positives, so prefer the high-valued ID candidate.
        """
        mapping: dict[int, int] = {}
        start = max(0, SAVE_PITCHER_BASE - 0x6000)
        end = SAVE_PITCHER_BASE
        by_index: dict[int, list[tuple[int, int]]] = {}
        for off in range(start, max(start, end - 11)):
            player_id = int.from_bytes(self.raw[off:off + 4], "little")
            a = int.from_bytes(self.raw[off + 4:off + 8], "little")
            b = int.from_bytes(self.raw[off + 8:off + 12], "little")
            if player_id and a == b and 0 <= a < SAVE_PITCHER_RECORDS:
                by_index.setdefault(a, []).append((off, player_id))

        for index, candidates in by_index.items():
            # For nonzero rows there is one legitimate candidate. Row zero can
            # produce shifted all-zero false positives; the real Default ID is
            # the large 32-bit candidate.
            _, player_id = max(candidates, key=lambda item: item[1])
            mapping[player_id] = index
        return mapping

    def _sync_teams(self) -> None:
        for i, record in enumerate(self.team_records):
            start = self.team_base + i * SAVE_TEAM_RECORD_SIZE
            self.raw[start:start + SAVE_TEAM_RECORD_SIZE] = record

    def save(self, path: Path) -> None:
        self._sync_teams()

        if path.suffix.lower() == ".zip":
            if self.source_path is None or self.source_path.suffix.lower() != ".zip":
                raise ValueError("ZIP output requires a ZIP source so companion files can be preserved")
            if not self.zip_member:
                raise ValueError("Could not identify the roster .sav member in the source ZIP")

            with zipfile.ZipFile(self.source_path, "r") as source:
                infos = source.infolist()
                contents = {
                    info.filename: (bytes(self.raw) if info.filename == self.zip_member else source.read(info.filename))
                    for info in infos
                    if not info.is_dir()
                }

            with zipfile.ZipFile(path, "w") as target:
                for info in infos:
                    if info.is_dir():
                        target.writestr(info, b"")
                    else:
                        target.writestr(info, contents[info.filename])
            return

        path.write_bytes(self.raw)


def _load_raw_save(path: Path) -> tuple[bytes, str | None]:
    if path.suffix.lower() != ".zip":
        return path.read_bytes(), None

    with zipfile.ZipFile(path) as zf:
        candidates = [
            info for info in zf.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".sav")
        ]
        if not candidates:
            raise ValueError("ZIP contains no .sav roster file")
        if len(candidates) > 1:
            rost = [
                info for info in candidates
                if Path(info.filename).name.lower().startswith("rost")
            ]
            if len(rost) == 1:
                candidates = rost
            else:
                raise ValueError("ZIP contains multiple .sav files; extract the roster save first")
        return zf.read(candidates[0]), candidates[0].filename


def _find_team_base(raw: bytes) -> int:
    marker = b"ArizSt\x00\x00"
    pos = 0
    while True:
        pos = raw.find(marker, pos)
        if pos < 0:
            raise ValueError("Could not locate 152-team roster block in save")
        next_pos = pos + SAVE_TEAM_RECORD_SIZE
        if raw[next_pos:next_pos + 8].startswith(b"ArkSt\x00"):
            return pos
        pos += 1


def _find_player_base(raw: bytes, search_from: int) -> int:
    marker = b"Default\x00"
    pos = search_from
    minimum = SAVE_PLAYER_RECORDS * SAVE_PLAYER_RECORD_SIZE
    while True:
        pos = raw.find(marker, pos)
        if pos < 0:
            raise ValueError("Could not locate 3826-record player array in save")
        if pos + minimum <= len(raw):
            first = _cstr(raw[pos:pos + SAVE_FIRST_NAME_SIZE])
            last = _cstr(
                raw[
                    pos + SAVE_FIRST_NAME_SIZE:
                    pos + SAVE_FIRST_NAME_SIZE + SAVE_LAST_NAME_SIZE
                ]
            )
            if first == "Default" and last == "Default":
                return pos
        pos += 1


def _cstr(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("latin-1")
