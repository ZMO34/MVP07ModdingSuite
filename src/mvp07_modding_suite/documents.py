from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import zipfile

from .model import (
    BigArchive,
    DatTable,
    RosterDatabase,
    RosterSlot,
    TeamRecord,
    refpack_compress_literals,
    refpack_decompress,
)
from .memory_save import MemoryRosterSave


GLOBAL_HEADER_SIZE = 491
ISO_TEAM_RECORD_SIZE = 687
ISO_TEAM_COUNT = 152


class RosterDocument:
    source_kind = "unknown"
    supports_dat_attributes = False
    supports_player_names = False
    max_roster_slots = 0

    teams: list

    def player_fields(self, player_id: int) -> dict[str, dict[str, str]]:
        return {}

    def set_player_fields(self, player_id: int, changes: dict[str, dict[str, str]]) -> None:
        if changes:
            raise ValueError("This document type does not expose editable player attributes")

    def player_display_name(self, player_id: int) -> str:
        return f"0x{player_id:08X}"

    def save(self, path: Path) -> None:
        raise NotImplementedError


class DatabaseBigDocument(RosterDocument):
    source_kind = "DATABASE.BIG"
    supports_dat_attributes = True
    supports_player_names = True
    max_roster_slots = 25

    def __init__(self, db: RosterDatabase):
        self.db = db
        self.teams = db.teams
        self._maps = {name: table.by_numeric_key() for name, table in db.tables.items()}
        self._field_ids = {
            name: {field: number for number, field in table.fields.items()}
            for name, table in db.tables.items()
        }

    @classmethod
    def load(cls, path: Path) -> "DatabaseBigDocument":
        return cls(RosterDatabase.load(path))

    def player_fields(self, player_id: int) -> dict[str, dict[str, str]]:
        result = {}
        for table_name, rows in self._maps.items():
            values = rows.get(player_id)
            if values is None:
                continue
            fields = self.db.tables[table_name].fields
            result[table_name] = {fields[i]: value for i, value in values.items() if i in fields}
        return result

    def set_player_fields(self, player_id: int, changes: dict[str, dict[str, str]]) -> None:
        for table_name, table_changes in changes.items():
            if table_name not in self._maps:
                continue
            values = self._maps[table_name].get(player_id)
            if values is None:
                continue
            ids = self._field_ids[table_name]
            for field, value in table_changes.items():
                if field in ids:
                    values[ids[field]] = str(value)

    def player_display_name(self, player_id: int) -> str:
        values = self._maps["attrib.dat"].get(player_id)
        if values is None:
            return super().player_display_name(player_id)
        ids = self._field_ids["attrib.dat"]
        first = values.get(ids.get("first_name", -1), "")
        last = values.get(ids.get("last_name", -1), "")
        return f"{first} {last}".strip() or super().player_display_name(player_id)

    def save(self, path: Path) -> None:
        self.db.save(path)


class RosterBinDocument(RosterDocument):
    source_kind = "roster.bin"
    supports_dat_attributes = False
    supports_player_names = False
    max_roster_slots = 25

    def __init__(self, path: Path, raw_input: bytes, decompressed: bytes):
        self.path = path
        self.was_compressed = raw_input != decompressed
        self.header = decompressed[:GLOBAL_HEADER_SIZE]
        self.teams = [
            TeamRecord(
                i,
                bytearray(
                    decompressed[
                        GLOBAL_HEADER_SIZE + i * ISO_TEAM_RECORD_SIZE:
                        GLOBAL_HEADER_SIZE + (i + 1) * ISO_TEAM_RECORD_SIZE
                    ]
                ),
            )
            for i in range(ISO_TEAM_COUNT)
        ]

    @classmethod
    def load(cls, path: Path) -> "RosterBinDocument":
        raw = path.read_bytes()
        decoded = refpack_decompress(raw)
        expected = GLOBAL_HEADER_SIZE + ISO_TEAM_COUNT * ISO_TEAM_RECORD_SIZE
        if len(decoded) != expected:
            raise ValueError(f"Unexpected roster.bin size: {len(decoded)} (expected {expected})")
        return cls(path, raw, decoded)

    def save(self, path: Path) -> None:
        decoded = self.header + b"".join(bytes(team.raw) for team in self.teams)
        path.write_bytes(refpack_compress_literals(decoded) if self.was_compressed else decoded)


@dataclass
class SaveTeam:
    index: int
    save: MemoryRosterSave

    @property
    def raw(self) -> bytearray:
        return self.save.team_records[self.index]

    def _getstr(self, offset: int, size: int) -> str:
        return bytes(self.raw[offset:offset + size]).split(b"\0", 1)[0].decode("latin-1")

    def _setstr(self, offset: int, size: int, value: str) -> None:
        data = value.encode("latin-1")
        if len(data) >= size:
            raise ValueError(f"Text must be at most {size - 1} bytes")
        self.raw[offset:offset + size] = data + b"\0" * (size - len(data))

    @property
    def key(self): return self._getstr(0x000, 8)
    @key.setter
    def key(self, v): self._setstr(0x000, 8, v)
    @property
    def name(self): return self._getstr(0x008, 48)
    @name.setter
    def name(self, v): self._setstr(0x008, 48, v)
    @property
    def abbreviation(self): return self._getstr(0x038, 16)
    @abbreviation.setter
    def abbreviation(self, v): self._setstr(0x038, 16, v)
    @property
    def city(self): return self._getstr(0x048, 40)
    @city.setter
    def city(self, v): self._setstr(0x048, 40, v)
    @property
    def nickname(self): return self._getstr(0x070, 32)
    @nickname.setter
    def nickname(self, v): self._setstr(0x070, 32, v)

    @property
    def roster_count(self) -> int:
        return int.from_bytes(self.raw[0x0C0:0x0C4], "little")

    @property
    def roster(self) -> list[RosterSlot]:
        result = []
        for i in range(30):
            off = 0x0C4 + i * 8
            result.append(
                RosterSlot(
                    int.from_bytes(self.raw[off:off + 4], "little"),
                    int.from_bytes(self.raw[off + 4:off + 8], "little"),
                )
            )
        return result

    def set_roster_slot(self, index: int, player_id: int, role_flags: int) -> None:
        if not 0 <= index < 30:
            raise IndexError(index)
        off = 0x0C4 + index * 8
        self.raw[off:off + 4] = int(player_id).to_bytes(4, "little")
        self.raw[off + 4:off + 8] = int(role_flags).to_bytes(4, "little")

    @property
    def starter_indexes(self) -> list[int]:
        return list(self.raw[0x1B4:0x1B7])

    @starter_indexes.setter
    def starter_indexes(self, values: list[int]) -> None:
        if len(values) != 3 or any(not 0 <= int(x) < 30 for x in values):
            raise ValueError("Three starter indexes in the range 0..29 are required")
        self.raw[0x1B4:0x1B7] = bytes(int(x) for x in values)

    @property
    def location_id(self) -> int:
        return int.from_bytes(self.raw[0x0A0:0x0A4], "little") & 0x3F

    @property
    def conference_id(self) -> int:
        return (int.from_bytes(self.raw[0x0A0:0x0A4], "little") >> 6) & 0x1F

    @property
    def division_index(self) -> int:
        return (int.from_bytes(self.raw[0x0A0:0x0A4], "little") >> 11) & 1

    @property
    def asset_id(self) -> int:
        return (int.from_bytes(self.raw[0x0A4:0x0A8], "little") >> 1) & 0x1FF

    @property
    def metadata_top3(self) -> int:
        return (int.from_bytes(self.raw[0x0A4:0x0A8], "little") >> 28) & 7

    @property
    def metadata_bit0(self) -> int:
        return self.raw[0x0A4] & 1


class MemorySaveDocument(RosterDocument):
    source_kind = ".sav"
    supports_dat_attributes = False
    supports_player_names = True
    max_roster_slots = 30

    def __init__(self, save: MemoryRosterSave):
        self.save_file = save
        self.teams = [SaveTeam(i, save) for i in range(152)]

    @classmethod
    def load(cls, path: Path) -> "MemorySaveDocument":
        return cls(MemoryRosterSave.load(path))

    def player_display_name(self, player_id: int) -> str:
        index = self.save_file.player_id_to_index.get(player_id)
        if index is None:
            return super().player_display_name(player_id)
        name = self.save_file.player_name(index)
        return f"{name.first_name} {name.last_name}".strip() or super().player_display_name(player_id)

    def player_fields(self, player_id: int) -> dict[str, dict[str, str]]:
        index = self.save_file.player_id_to_index.get(player_id)
        if index is None:
            return {}
        name = self.save_file.player_name(index)
        return {
            "save": {
                "first_name": name.first_name,
                "last_name": name.last_name,
                "player_index": str(index),
                "packed_attributes_hex": self.save_file.player_payload(index).hex(),
            }
        }

    def set_player_fields(self, player_id: int, changes: dict[str, dict[str, str]]) -> None:
        index = self.save_file.player_id_to_index.get(player_id)
        if index is None:
            raise ValueError(f"Player ID 0x{player_id:08X} has no save player record")
        save_changes = changes.get("save", {})
        if "first_name" in save_changes or "last_name" in save_changes:
            old = self.save_file.player_name(index)
            self.save_file.set_player_name(
                index,
                save_changes.get("first_name", old.first_name),
                save_changes.get("last_name", old.last_name),
            )
        # packed_attributes_hex is intentionally read-only until individual
        # fields are proven. This guarantees unknown bits are preserved.

    def save(self, path: Path) -> None:
        self.save_file.save(path)


def open_roster_document(path: Path) -> RosterDocument:
    suffix = path.suffix.lower()

    if suffix == ".big":
        return DatabaseBigDocument.load(path)

    if suffix == ".bin":
        return RosterBinDocument.load(path)

    if suffix in {".sav", ".zip"}:
        return MemorySaveDocument.load(path)

    # Content sniffing for extensionless / extracted PS2 files.
    head = path.read_bytes()[:8]
    if head.startswith(b"BIGF"):
        return DatabaseBigDocument.load(path)
    if len(head) >= 2 and head[1] == 0xFB:
        return RosterBinDocument.load(path)

    try:
        return MemorySaveDocument.load(path)
    except Exception as exc:
        raise ValueError(f"Unsupported roster source: {path}") from exc
