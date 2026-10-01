from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv

from .ui_schema import validate_field_value


TABLE_TO_PREFIX = {
    "save": "save",
    "attrib.dat": "attrib",
    "rhattrib.dat": "vs_rhp",
    "lhattrib.dat": "vs_lhp",
    "pitcher.dat": "pitching",
}
PREFIX_TO_TABLE = {prefix: table for table, prefix in TABLE_TO_PREFIX.items()}
TABLE_ORDER = tuple(TABLE_TO_PREFIX)
TEAM_FIELDS = ("key", "name", "abbreviation", "city", "nickname")
BASE_COLUMNS = (
    "team_index",
    "team_key",
    "team_name",
    "team_abbreviation",
    "team_city",
    "team_nickname",
    "starter_1_slot",
    "starter_2_slot",
    "starter_3_slot",
    "roster_slot",
    "player_id",
    "player_name",
    "role_flags",
)


@dataclass(frozen=True)
class CsvImportResult:
    rows_read: int
    team_changes: int
    slot_changes: int
    player_changes: int

    @property
    def total_changes(self) -> int:
        return self.team_changes + self.slot_changes + self.player_changes


def export_roster_csv(doc, path: Path) -> int:
    """Export every team/slot plus every player field exposed by the backend."""
    player_columns = _discover_player_columns(doc)
    fieldnames = list(BASE_COLUMNS) + player_columns
    row_count = 0

    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for team_index, team in enumerate(doc.teams):
            starters = list(team.starter_indexes)
            for slot_index, slot in enumerate(team.roster):
                row = {
                    "team_index": team_index + 1,
                    "team_key": team.key,
                    "team_name": team.name,
                    "team_abbreviation": team.abbreviation,
                    "team_city": team.city,
                    "team_nickname": team.nickname,
                    "starter_1_slot": starters[0] + 1 if len(starters) > 0 else "",
                    "starter_2_slot": starters[1] + 1 if len(starters) > 1 else "",
                    "starter_3_slot": starters[2] + 1 if len(starters) > 2 else "",
                    "roster_slot": slot_index + 1,
                    "player_id": f"0x{slot.player_id:08X}" if slot.player_id else "0x00000000",
                    "player_name": doc.player_display_name(slot.player_id) if slot.player_id else "",
                    "role_flags": f"0x{slot.role_flags:08X}",
                }
                if slot.player_id:
                    for table, values in doc.player_fields(slot.player_id).items():
                        prefix = TABLE_TO_PREFIX.get(table)
                        if prefix is None:
                            continue
                        for field, value in values.items():
                            column = f"{prefix}.{field}"
                            if column in player_columns:
                                row[column] = value
                writer.writerow(row)
                row_count += 1
    return row_count


def import_roster_csv(doc, path: Path) -> CsvImportResult:
    """Import edits from a CSV created by export_roster_csv.

    Player IDs are deliberately treated as structural identifiers. Importing a
    spreadsheet cannot silently move/reassign a player to a different slot.
    """
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        missing = {"team_index", "roster_slot", "player_id"} - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    team_plan: dict[int, dict[str, str]] = {}
    rotation_plan: dict[int, tuple[int, int, int]] = {}
    slot_plan: list[tuple[int, int, int, int]] = []
    player_plan: dict[int, dict[str, dict[str, str]]] = {}

    for line_no, row in enumerate(rows, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue
        team_index = _parse_one_based(row.get("team_index"), len(doc.teams), "team_index", line_no)
        team = doc.teams[team_index]
        slot_index = _parse_one_based(
            row.get("roster_slot"), doc.max_roster_slots, "roster_slot", line_no
        )
        slot = team.roster[slot_index]
        csv_player_id = _parse_int(row.get("player_id", "0"), "player_id", line_no)
        if csv_player_id != slot.player_id:
            raise ValueError(
                f"Line {line_no}: player_id does not match team {team_index + 1}, "
                f"slot {slot_index + 1}. CSV import does not move players."
            )

        _merge_team_row(team_plan, team_index, row, line_no)
        rotation = _row_rotation(row, doc.max_roster_slots, line_no)
        if rotation is not None:
            previous = rotation_plan.get(team_index)
            if previous is not None and previous != rotation:
                raise ValueError(f"Line {line_no}: inconsistent starting rotation for the same team")
            rotation_plan[team_index] = rotation

        if "role_flags" in row and (row.get("role_flags") or "").strip():
            role_flags = _parse_int(row["role_flags"], "role_flags", line_no)
            if not 0 <= role_flags <= 0xFFFFFFFF:
                raise ValueError(f"Line {line_no}: role_flags must fit in an unsigned 32-bit value")
            if role_flags != slot.role_flags:
                slot_plan.append((team_index, slot_index, slot.player_id, role_flags))

        if not slot.player_id:
            continue
        current = doc.player_fields(slot.player_id)
        changes: dict[str, dict[str, str]] = {}
        for column, csv_value in row.items():
            if "." not in column or csv_value is None:
                continue
            prefix, field = column.split(".", 1)
            table = PREFIX_TO_TABLE.get(prefix)
            if table is None or table not in current or field not in current[table]:
                continue
            old = str(current[table][field])
            value = csv_value.strip()
            if value == old:
                continue
            if table != "save":
                value = validate_field_value(field, value, old)
            if value != old:
                changes.setdefault(table, {})[field] = value
        if changes:
            destination = player_plan.setdefault(slot.player_id, {})
            for table, table_changes in changes.items():
                destination.setdefault(table, {}).update(table_changes)

    team_changes = 0
    for team_index, values in team_plan.items():
        team = doc.teams[team_index]
        changed = False
        for field, value in values.items():
            if str(getattr(team, field)) != value:
                setattr(team, field, value)
                changed = True
        if team_index in rotation_plan and tuple(team.starter_indexes) != rotation_plan[team_index]:
            team.starter_indexes = list(rotation_plan[team_index])
            changed = True
        team_changes += int(changed)

    for team_index, slot_index, player_id, role_flags in slot_plan:
        doc.teams[team_index].set_roster_slot(slot_index, player_id, role_flags)

    for player_id, changes in player_plan.items():
        doc.set_player_fields(player_id, changes)

    return CsvImportResult(
        rows_read=len(rows),
        team_changes=team_changes,
        slot_changes=len(slot_plan),
        player_changes=len(player_plan),
    )


def _discover_player_columns(doc) -> list[str]:
    fields: dict[str, set[str]] = {table: set() for table in TABLE_ORDER}
    seen: set[int] = set()
    for team in doc.teams:
        for slot in team.roster:
            if not slot.player_id or slot.player_id in seen:
                continue
            seen.add(slot.player_id)
            for table, values in doc.player_fields(slot.player_id).items():
                if table not in fields:
                    continue
                if table == "save":
                    fields[table].update(name for name in values if name in {"first_name", "last_name"})
                else:
                    fields[table].update(values)
    columns: list[str] = []
    for table in TABLE_ORDER:
        prefix = TABLE_TO_PREFIX[table]
        columns.extend(f"{prefix}.{field}" for field in sorted(fields[table]))
    return columns


def _merge_team_row(plan: dict[int, dict[str, str]], team_index: int, row: dict[str, str], line_no: int) -> None:
    destination = plan.setdefault(team_index, {})
    for field in TEAM_FIELDS:
        column = f"team_{field}"
        if column not in row or row[column] is None:
            continue
        value = row[column]
        previous = destination.get(field)
        if previous is not None and previous != value:
            raise ValueError(f"Line {line_no}: inconsistent {column} for the same team")
        destination[field] = value


def _row_rotation(row: dict[str, str], max_slots: int, line_no: int) -> tuple[int, int, int] | None:
    names = ("starter_1_slot", "starter_2_slot", "starter_3_slot")
    if not all(name in row for name in names):
        return None
    values = [(row.get(name) or "").strip() for name in names]
    if not any(values):
        return None
    if not all(values):
        raise ValueError(f"Line {line_no}: starting rotation requires all three starter columns")
    parsed = tuple(
        _parse_one_based(value, max_slots, name, line_no)
        for name, value in zip(names, values)
    )
    if len(set(parsed)) != 3:
        raise ValueError(f"Line {line_no}: starting rotation must use three different roster slots")
    return parsed


def _parse_one_based(value: str | None, maximum: int, name: str, line_no: int) -> int:
    number = _parse_int(value or "", name, line_no)
    if not 1 <= number <= maximum:
        raise ValueError(f"Line {line_no}: {name} must be 1..{maximum}")
    return number - 1


def _parse_int(value: str, name: str, line_no: int) -> int:
    try:
        return int(value.strip(), 0)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Line {line_no}: invalid {name}: {value!r}") from exc
