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
        save = self.players[player_id]["save"]
        return f"{save['first_name']} {save['last_name']}"

    def player_fields(self, player_id: int):
        return self.players.get(player_id, {})

    def set_player_fields(self, player_id: int, changes):
        for table, values in changes.items():
            self.players[player_id].setdefault(table, {}).update(values)


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
            self.assertIn("save.first_name", fieldnames)
            self.assertNotIn("save.packed_attributes_hex", fieldnames)

            data[0]["team_name"] = "Alpha State"
            data[0]["role_flags"] = "0x2C44"
            data[0]["save.first_name"] = "Chris"
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
