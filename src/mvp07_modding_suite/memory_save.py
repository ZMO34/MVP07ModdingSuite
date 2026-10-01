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


@dataclass(frozen=True)
class SavePlayerName:
    index: int
    first_name: str
    last_name: str


@dataclass
class MemoryRosterSave:
    raw: bytes
    team_base: int
    player_base: int

    @classmethod
    def load(cls, path: Path) -> "MemoryRosterSave":
        raw = _load_raw_save(path)
        team_base = _find_team_base(raw)
        player_base = _find_player_base(raw, team_base + TEAM_COUNT * SAVE_TEAM_RECORD_SIZE)
        return cls(raw=raw, team_base=team_base, player_base=player_base)

    def team_record(self, index: int) -> bytes:
        if not 0 <= index < TEAM_COUNT:
            raise IndexError(index)
        start = self.team_base + index * SAVE_TEAM_RECORD_SIZE
        return self.raw[start:start + SAVE_TEAM_RECORD_SIZE]

    def player_record(self, index: int) -> bytes:
        if not 0 <= index < SAVE_PLAYER_RECORDS:
            raise IndexError(index)
        start = self.player_base + index * SAVE_PLAYER_RECORD_SIZE
        return self.raw[start:start + SAVE_PLAYER_RECORD_SIZE]

    def player_name(self, index: int) -> SavePlayerName:
        rec = self.player_record(index)
        return SavePlayerName(
            index=index,
            first_name=_cstr(rec[:SAVE_FIRST_NAME_SIZE]),
            last_name=_cstr(rec[SAVE_FIRST_NAME_SIZE:SAVE_FIRST_NAME_SIZE + SAVE_LAST_NAME_SIZE]),
        )

    def populated_player_names(self) -> list[SavePlayerName]:
        out = []
        for i in range(SAVE_PLAYER_RECORDS):
            rec = self.player_record(i)
            if not any(rec):
                break
            name = self.player_name(i)
            if name.first_name or name.last_name:
                out.append(name)
        return out


def _load_raw_save(path: Path) -> bytes:
    if path.suffix.lower() != ".zip":
        return path.read_bytes()

    with zipfile.ZipFile(path) as zf:
        candidates = [
            info for info in zf.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".sav")
        ]
        if not candidates:
            raise ValueError("ZIP contains no .sav roster file")
        if len(candidates) > 1:
            # Prefer MVP-style Rost*.sav when present.
            rost = [i for i in candidates if Path(i.filename).name.lower().startswith("rost")]
            if len(rost) == 1:
                candidates = rost
            else:
                raise ValueError("ZIP contains multiple .sav files; extract the roster save first")
        return zf.read(candidates[0])


def _find_team_base(raw: bytes) -> int:
    # The default roster's first team is Arizona State. Validate the candidate
    # using the next record (Arkansas State) exactly 727 bytes later.
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
    # Player record zero is the Default template:
    # first_name[12] = "Default", last_name[16] = "Default".
    marker = b"Default\x00"
    pos = search_from
    minimum = SAVE_PLAYER_RECORDS * SAVE_PLAYER_RECORD_SIZE
    while True:
        pos = raw.find(marker, pos)
        if pos < 0:
            raise ValueError("Could not locate 3826-record player array in save")
        if pos + minimum <= len(raw):
            first = _cstr(raw[pos:pos + SAVE_FIRST_NAME_SIZE])
            last = _cstr(raw[pos + SAVE_FIRST_NAME_SIZE:pos + SAVE_FIRST_NAME_SIZE + SAVE_LAST_NAME_SIZE])
            if first == "Default" and last == "Default":
                return pos
        pos += 1


def _cstr(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("latin-1")
