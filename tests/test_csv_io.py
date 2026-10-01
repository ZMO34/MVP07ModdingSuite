from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mvp07_modding_suite.csv_io import export_roster_csv, import_roster_csv


@dataclass
class RosterSlot:
    player_id: int
    role_flags: int


@dataclass
class FakeTeam:
    index: int
    key: str
    name: str
    abbreviation: str
    city: str
    nickname: str
    roster: list[RosterSlot]
    starter_indexes: list[int]
    location_id: int = 1
    conference_id: int = 1
    division_index: int = 0
    asset_id: int = 1
    metadata_top3: int = 0
    metadata_bit0: int = 0

    def set_roster_slot(self, index: int, player_id: int, role_flags: int) -> None:
        self.roster[index] = RosterSlot(player_id, role_flags)


class FakeDocument:
    source_kind = "test"
    max_roster_slots = 3

    def __init__(self):
        self.teams = [
            FakeTeam(
                0, "Alpha", "Alpha University", "ALP", "Athens", "Owls",
                [RosterSlot(0x100, 0x2C33), RosterSlot(0x101, 0x8000), RosterSlot(0, 0)],
                [1, 0, 2],
            )
        ]
        self.players = {
            0x100: {
                "save": {"first_name": "Alex", "last_name": "Smith", "player_index": "1", "packed_attributes_hex": "dead"},
                "attrib.dat": {"playerattrib_bats": "0", "playerattrib_jerseynum": "12"},
            },
            0x101: {
                "save": {"first_name": "Ben", "last_name": "Jones", "player_index": "2", "packed_attributes_hex": "beef"},
                "attrib.dat": {"playerattrib_bats": "1", "playerattrib_jerseynum": "24"},
            },
        }

    def player_display_name(self, player_id: int) -> str:
        fields = self.players[player_id]
        names = fields.get("save", fields["attrib.dat"])
        return f"{names['first_name']} {names['last_name']}"

    def player_fields(self, player_id: int):
        return self.players.get(player_id, {})

    def set_player_fields(self, player_id: int, changes):
        for table, values in changes.items():
            self.players[player_id].setdefault(table, {}).update(values)


class FakeDatabaseDocument(FakeDocument):
    source_kind = "DATABASE.BIG"

    def __init__(self):
        super().__init__()
        for fields in self.players.values():
            names = fields.pop("save")
            fields["attrib.dat"].update({name: names[name] for name in ("first_name", "last_name")})


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def write_csv(path, fieldnames, data):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


class CsvIoTests(unittest.TestCase):
    def test_export_then_import_edits(self):
        doc = FakeDocument()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.csv"
            rows = export_roster_csv(doc, path)
            self.assertEqual(rows, 3)
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                data = list(csv.DictReader(handle))
                fieldnames = list(data[0].keys())
            self.assertIn("attrib.playerattrib_bats", fieldnames)
            self.assertIn("first_name", fieldnames)
            self.assertIn("last_name", fieldnames)
            self.assertNotIn("save.first_name", fieldnames)
            self.assertNotIn("save.packed_attributes_hex", fieldnames)

            data[0]["team_name"] = "Alpha State"
            data[0]["role_flags"] = "0x2C44"
            data[0]["first_name"] = "Chris"
            data[0]["attrib.playerattrib_bats"] = "L"
            for row in data[1:]:
                row["team_name"] = "Alpha State"
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            result = import_roster_csv(doc, path)
            self.assertEqual(result.team_changes, 1)
            self.assertEqual(result.slot_changes, 1)
            self.assertEqual(result.player_changes, 1)
            self.assertEqual(doc.teams[0].name, "Alpha State")
            self.assertEqual(doc.teams[0].roster[0].role_flags, 0x2C44)
            self.assertEqual(doc.players[0x100]["save"]["first_name"], "Chris")
            self.assertEqual(doc.players[0x100]["attrib.dat"]["playerattrib_bats"], "1")

    def test_universal_export_and_unchanged_import_for_both_sources(self):
        for factory in (FakeDocument, FakeDatabaseDocument):
            with self.subTest(source=factory.__name__), tempfile.TemporaryDirectory() as tmp:
                doc = factory()
                path = Path(tmp) / "roster.csv"
                export_roster_csv(doc, path)
                fields, data = read_csv(path)
                self.assertEqual((data[0]["first_name"], data[0]["last_name"]), ("Alex", "Smith"))
                self.assertEqual((data[2]["first_name"], data[2]["last_name"]), ("", ""))
                for prefix in ("save", "attrib"):
                    for name in ("first_name", "last_name"):
                        self.assertNotIn(f"{prefix}.{name}", fields)
                self.assertEqual(import_roster_csv(doc, path).total_changes, 0)

    def test_database_name_routing_and_blank_last_name(self):
        doc = FakeDatabaseDocument()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.csv"
            export_roster_csv(doc, path)
            fields, data = read_csv(path)
            data[0].update(first_name="John", last_name="")
            write_csv(path, fields, data)
            self.assertEqual(import_roster_csv(doc, path).player_changes, 1)
            self.assertEqual(doc.players[0x100]["attrib.dat"]["first_name"], "John")
            self.assertEqual(doc.players[0x100]["attrib.dat"]["last_name"], "")
            self.assertNotIn("save", doc.players[0x100])

    def test_source_prefixed_name_columns_are_rejected(self):
        for prefix, factory in (("save", FakeDocument), ("attrib", FakeDatabaseDocument)):
            for name in ("first_name", "last_name"):
                for universal_columns in (False, True):
                    with self.subTest(prefix=prefix, name=name, mixed=universal_columns), tempfile.TemporaryDirectory() as tmp:
                        doc = factory()
                        path = Path(tmp) / "roster.csv"
                        export_roster_csv(doc, path)
                        fields, data = read_csv(path)
                        if not universal_columns:
                            fields = [f for f in fields if f not in ("first_name", "last_name")]
                        fields.append(f"{prefix}.{name}")
                        data[0][f"{prefix}.{name}"] = "John"
                        write_csv(path, fields, data)
                        with self.assertRaisesRegex(ValueError, "Export a new CSV and edit first_name and last_name"):
                            import_roster_csv(doc, path)
                        self.assertEqual(doc.player_display_name(0x100), "Alex Smith")

    def test_partial_csv_changes_only_the_present_name(self):
        doc = FakeDocument()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.csv"
            fields = ["team_index", "roster_slot", "player_id", "first_name"]
            write_csv(path, fields, [dict(team_index=1, roster_slot=1, player_id="0x100", first_name="John")])
            import_roster_csv(doc, path)
            self.assertEqual(doc.player_display_name(0x100), "John Smith")

    def test_player_name_remains_display_only(self):
        doc = FakeDocument()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.csv"
            export_roster_csv(doc, path)
            fields, data = read_csv(path)
            data[0]["player_name"] = "Not A Name Edit"
            write_csv(path, fields, data)
            self.assertEqual(import_roster_csv(doc, path).total_changes, 0)
            self.assertEqual(doc.player_display_name(0x100), "Alex Smith")

    def test_source_without_names_rejects_name_edits(self):
        doc = FakeDocument()
        for values in doc.players.values():
            values.pop("save")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.csv"
            fields = ["team_index", "roster_slot", "player_id", "first_name"]
            write_csv(path, fields, [dict(team_index=1, roster_slot=1, player_id="0x100", first_name="John")])
            with self.assertRaisesRegex(ValueError, "first_name is not editable"):
                import_roster_csv(doc, path)

    def test_import_rejects_player_reassignment(self):
        doc = FakeDocument()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roster.csv"
            export_roster_csv(doc, path)
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                data = list(csv.DictReader(handle))
                fieldnames = list(data[0].keys())
            data[0]["player_id"] = "0xDEADBEEF"
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            with self.assertRaisesRegex(ValueError, "does not match"):
                import_roster_csv(doc, path)


if __name__ == "__main__":
    unittest.main()
