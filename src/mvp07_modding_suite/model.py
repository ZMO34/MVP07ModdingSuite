from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def refpack_decompress(data: bytes) -> bytes:
    if len(data) < 5 or data[1] != 0xFB:
        return data
    signature = (data[0] << 8) | data[1]
    pos = 2
    if signature & 0x0100:
        pos += 3
    expected = int.from_bytes(data[pos:pos+3], "big")
    pos += 3
    out = bytearray()

    def backref(distance: int, length: int) -> None:
        if distance <= 0 or distance > len(out):
            raise ValueError(f"Invalid RefPack back-reference: {distance}")
        for _ in range(length):
            out.append(out[-distance])

    while True:
        first = data[pos]
        pos += 1
        if not (first & 0x80):
            second = data[pos]; pos += 1
            literal = first & 3
            out.extend(data[pos:pos+literal]); pos += literal
            backref(((first & 0x60) << 3) + second + 1, ((first >> 2) & 7) + 3)
        elif not (first & 0x40):
            second, third = data[pos], data[pos+1]; pos += 2
            literal = second >> 6
            out.extend(data[pos:pos+literal]); pos += literal
            backref(((second & 0x3F) << 8) + third + 1, (first & 0x3F) + 4)
        elif not (first & 0x20):
            second, third, fourth = data[pos], data[pos+1], data[pos+2]; pos += 3
            literal = first & 3
            out.extend(data[pos:pos+literal]); pos += literal
            backref(((first & 0x10) << 12) + (second << 8) + third + 1,
                    ((first & 0x0C) << 6) + fourth + 5)
        else:
            literal = (first & 0x1F) * 4 + 4
            if literal <= 0x70:
                out.extend(data[pos:pos+literal]); pos += literal
            else:
                literal = first & 3
                out.extend(data[pos:pos+literal]); pos += literal
                break
    if len(out) != expected:
        raise ValueError(f"RefPack size mismatch: expected {expected}, got {len(out)}")
    return bytes(out)


def refpack_compress_literals(data: bytes) -> bytes:
    """Conservative valid RefPack encoder using literal commands only."""
    if len(data) > 0xFFFFFF:
        raise ValueError("24-bit RefPack size limit exceeded")
    out = bytearray(b"\x10\xFB" + len(data).to_bytes(3, "big"))
    pos = 0
    while len(data) - pos >= 4:
        n = min(112, ((len(data) - pos) // 4) * 4)
        out.append(0xE0 + ((n - 4) // 4))
        out.extend(data[pos:pos+n])
        pos += n
    tail = len(data) - pos
    out.append(0xFC + tail)
    out.extend(data[pos:])
    return bytes(out)


@dataclass
class BigEntry:
    name: str
    raw: bytes


@dataclass
class BigArchive:
    entries: list[BigEntry]

    @classmethod
    def load(cls, path: Path) -> "BigArchive":
        data = path.read_bytes()
        if data[:4] != b"BIGF":
            raise ValueError("Not an EA BIGF archive")
        count = int.from_bytes(data[8:12], "big")
        pos = 16
        entries = []
        for _ in range(count):
            offset = int.from_bytes(data[pos:pos+4], "big")
            size = int.from_bytes(data[pos+4:pos+8], "big")
            pos += 8
            end = data.index(0, pos)
            name = data[pos:end].decode("latin-1")
            pos = end + 1
            entries.append(BigEntry(name, data[offset:offset+size]))
        return cls(entries)

    def get(self, name: str) -> bytes:
        for e in self.entries:
            if e.name == name:
                return e.raw
        raise KeyError(name)

    def set(self, name: str, raw: bytes) -> None:
        for e in self.entries:
            if e.name == name:
                e.raw = raw
                return
        raise KeyError(name)

    def build(self) -> bytes:
        directory_size = 16 + sum(8 + len(e.name.encode("latin-1")) + 1 for e in self.entries)
        data_start = (directory_size + 3) & ~3
        offsets = []
        cursor = data_start
        for e in self.entries:
            cursor = (cursor + 3) & ~3
            offsets.append(cursor)
            cursor += len(e.raw)
        out = bytearray(cursor)
        out[:4] = b"BIGF"
        out[4:8] = len(out).to_bytes(4, "little")
        out[8:12] = len(self.entries).to_bytes(4, "big")
        out[12:16] = directory_size.to_bytes(4, "big")
        pos = 16
        for e, offset in zip(self.entries, offsets):
            out[pos:pos+4] = offset.to_bytes(4, "big")
            out[pos+4:pos+8] = len(e.raw).to_bytes(4, "big")
            pos += 8
            name = e.name.encode("latin-1") + b"\0"
            out[pos:pos+len(name)] = name
            pos += len(name)
            out[offset:offset+len(e.raw)] = e.raw
        return bytes(out)


@dataclass
class DatTable:
    fields: dict[int, str]
    rows: list[tuple[str, dict[int, str]]]

    @classmethod
    def parse(cls, data: bytes) -> "DatTable":
        lines = data.decode("latin-1").splitlines()
        fields = {}
        for token in lines[0].split(","):
            token = token.strip()
            if not token or token == ";":
                continue
            number, name = token.split(" ", 1)
            fields[int(number)] = name
        rows = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split(",")
            key = parts[0]
            values = {}
            for token in parts[1:]:
                token = token.strip()
                if not token or token == ";":
                    continue
                number, value = token.split(" ", 1)
                values[int(number)] = value
            rows.append((key, values))
        return cls(fields, rows)

    def by_numeric_key(self) -> dict[int, dict[int, str]]:
        return {int(k, 16): v for k, v in self.rows}

    def to_bytes(self) -> bytes:
        header = ",".join(f"{i} {self.fields[i]}" for i in sorted(self.fields)) + ",;\r\n"
        lines = [header]
        for key, values in self.rows:
            body = ",".join(f"{i} {values.get(i, '')}" for i in sorted(self.fields))
            lines.append(f"{key},{body},;\r\n")
        return "".join(lines).encode("latin-1")


@dataclass
class RosterSlot:
    player_id: int
    role_flags: int

    @property
    def inferred_position_code(self) -> int | None:
        lo = self.role_flags & 0xFF
        a, b = lo & 0xF, (lo >> 4) & 0xF
        return a - 1 if a == b and 1 <= a <= 0xA else None

    @property
    def inferred_batting_order(self) -> int | None:
        hi = (self.role_flags >> 8) & 0xFF
        codes = [0x0B, 0x16, 0x21, 0x2C, 0x37, 0x42, 0x4D, 0x58, 0x63]
        return codes.index(hi) + 1 if hi in codes else None


@dataclass
class TeamRecord:
    index: int
    raw: bytearray

    def _getstr(self, offset: int, size: int) -> str:
        return bytes(self.raw[offset:offset+size]).split(b"\0", 1)[0].decode("latin-1")

    def _setstr(self, offset: int, size: int, value: str) -> None:
        b = value.encode("latin-1")
        if len(b) >= size:
            raise ValueError(f"Text must be at most {size-1} bytes")
        self.raw[offset:offset+size] = b + b"\0" * (size - len(b))

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
        slots = []
        for i in range(25):
            off = 0x0C4 + i * 8
            slots.append(RosterSlot(
                int.from_bytes(self.raw[off:off+4], "little"),
                int.from_bytes(self.raw[off+4:off+8], "little"),
            ))
        return slots

    @property
    def starter_indexes(self) -> list[int]:
        return list(self.raw[0x18C:0x18F])

    @property
    def asset_id(self) -> int:
        x = int.from_bytes(self.raw[0x0A4:0x0A8], "little")
        return (x >> 1) & 0x1FF

    @property
    def metadata_top3(self) -> int:
        x = int.from_bytes(self.raw[0x0A4:0x0A8], "little")
        return (x >> 28) & 0x7

    @property
    def metadata_bit0(self) -> int:
        return self.raw[0x0A4] & 1


@dataclass
class RosterDatabase:
    archive: BigArchive
    roster_header: bytes
    teams: list[TeamRecord]
    tables: dict[str, DatTable]
    dirty: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path) -> "RosterDatabase":
        archive = BigArchive.load(path)
        roster = refpack_decompress(archive.get("roster.bin"))
        if len(roster) != 104915:
            raise ValueError(f"Unexpected roster.bin size: {len(roster)}")
        header = roster[:491]
        teams = [TeamRecord(i, bytearray(roster[491+i*687:491+(i+1)*687])) for i in range(152)]
        tables = {}
        for name in ("attrib.dat", "rhattrib.dat", "lhattrib.dat", "pitcher.dat"):
            tables[name] = DatTable.parse(refpack_decompress(archive.get(name)))
        return cls(archive, header, teams, tables)

    def player_values(self, table_name: str, player_id: int):
        return self.tables[table_name].by_numeric_key().get(player_id)

    def save(self, path: Path) -> None:
        roster = self.roster_header + b"".join(bytes(t.raw) for t in self.teams)
        self.archive.set("roster.bin", refpack_compress_literals(roster))
        for name, table in self.tables.items():
            self.archive.set(name, refpack_compress_literals(table.to_bytes()))
        path.write_bytes(self.archive.build())
