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
SAVE_PLAYER_PAYLOAD_OFFSET = 28
SAVE_PLAYER_PAYLOAD_SIZE = 56


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

    def player_payload(self, index: int) -> bytes:
        rec = self.player_record(index)
        return rec[
            SAVE_PLAYER_PAYLOAD_OFFSET:
            SAVE_PLAYER_PAYLOAD_OFFSET + SAVE_PLAYER_PAYLOAD_SIZE
        ]

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
        mapping: dict[int, int] = {}

        # The save contains entries of the form:
        #   u32 player_id, u32 player_index, u32 player_index
        # They are not guaranteed to be naturally aligned, so scan bytewise.
        raw = self.raw
        limit = len(raw) - 12
        for off in range(limit):
            player_id = int.from_bytes(raw[off:off + 4], "little")
            if player_id not in roster_ids:
                continue
            a = int.from_bytes(raw[off + 4:off + 8], "little")
            b = int.from_bytes(raw[off + 8:off + 12], "little")
            if a == b and 0 <= a < SAVE_PLAYER_RECORDS:
                mapping.setdefault(player_id, a)

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
