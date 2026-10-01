#!/usr/bin/env python3
"""Reproduce stock-profile cross-file and preservation checks on user originals.

Requires DATABASE.BIG and the default Rost1.sav/PCSX2 ZIP identified in the
research notes. Writes only into an automatically removed temporary directory.
Does not test game compatibility or expanded profiles.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import struct
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mvp07_modding_suite.memory_save import (
    BATTING_BITFIELDS, PITCHER_BITFIELDS, PLAYER_GENERAL_BITFIELDS,
    MemoryRosterSave, SAVE_LH_BATTING_BASE, SAVE_RH_BATTING_BASE,
    SAVE_PITCHER_BASE,
)
from mvp07_modding_suite.model import BigArchive, RosterDatabase, refpack_decompress
from mvp07_modding_suite.documents import RosterBinDocument


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_masks(save, label, base, size, fields, setter, getter, duplicate=None):
    """Check writes against field masks, including all adjacent bytes in the save."""
    original = bytes(save.raw)
    old_value = int.from_bytes(original[base:base+size], 'little')
    for field, (bit, width) in fields.items():
        target = getter()[field] ^ 1
        setter({field: target})
        value = int.from_bytes(save.raw[base:base+size], 'little')
        mask = ((1 << width)-1) << bit
        if duplicate and field in duplicate:
            dbit, dwidth = duplicate[field]
            mask |= ((1 << dwidth)-1) << dbit
            require((value >> dbit) & ((1 << dwidth)-1) == target,
                    f'{label}/{field}: duplicate not updated')
        require((old_value ^ value) & ~mask == 0, f'{label}/{field}: unrelated bits changed')
        require(getter()[field] == target, f'{label}/{field}: readback differs')
        require(bytes(save.raw[:base]) == original[:base] and
                bytes(save.raw[base+size:]) == original[base+size:],
                f'{label}/{field}: adjacent bytes changed')
        save.raw[:] = original
    print(f'PASS {label}: {len(fields)} field writes preserve unrelated bits/bytes')


def verify(database, save_path):
    db = RosterDatabase.load(database)
    save = MemoryRosterSave.load(save_path)
    raw = bytes(save.raw)
    roster = refpack_decompress(db.archive.get('roster.bin'))
    require(len(roster) == 104915 and struct.unpack_from('<I', roster)[0] == 153,
            'Unexpected stock roster framing')
    require(roster[4:491] == bytes(487), 'Stock sentinel differs')
    require(save.team_base == 0x20c3 and save.general_record_base == 0x2c407,
            'Unexpected save profile; do not apply absolute offsets')
    require(struct.unpack_from('<I', raw, 0x1de8)[0] == 153 and
            struct.unpack_from('<I', raw, 0x1dec+0xc0)[0] == 30,
            'Unexpected save sentinel framing')
    for team, st in zip(db.teams, save.team_records):
        require(team.raw[0x90:0xc0] == st[0x90:0xc0], f'Team {team.index}: metadata mismatch')
        for offset, size in [(0,8),(8,48),(0x38,16),(0x48,40),(0x70,32)]:
            require(team.raw[offset:offset+size].split(b'\0',1)[0] ==
                    st[offset:offset+size].split(b'\0',1)[0], 'Team visible string differs')
        require(struct.unpack_from('<I', team.raw, 0xc0)[0] == 25 and
                struct.unpack_from('<I', st, 0xc0)[0] == 30, 'Slot count differs')
        require(team.raw[0xc4:0x18c] == st[0xc4:0x18c], 'First 25 slots differ')
        require(st[0x18c:0x1b4] == bytes(40), 'Extra default slots are not empty')
        require(team.raw[0x18c:0x18f] == st[0x1b4:0x1b7], 'Rotations differ')
        require(team.raw[0x18f:] == st[0x1b7:], 'Ballpark-associated tail differs')
    print('PASS framing, sentinel, 152 team metadata/roster/rotation/tail comparisons')

    triples = {}
    for off in range(save.team_base+152*727, save.general_record_base-11):
        pid, a, b = struct.unpack_from('<III', raw, off)
        if pid and a == b and a < 3826:
            triples.setdefault(a, set()).add(pid)
    default_id = int(db.tables['attrib.dat'].rows[0][0], 16)
    require(default_id in triples.get(0, set()), 'Default general ID mapping missing')
    bunting_sentinels = Counter()
    absent_pitch5 = 0
    table_specs = [
        ('attrib.dat', PLAYER_GENERAL_BITFIELDS, save.player_id_to_index,
         save.player_general_values),
        ('lhattrib.dat', BATTING_BITFIELDS, save.player_id_to_index,
         lambda i: save.batting_values(i, 'L')),
        ('rhattrib.dat', BATTING_BITFIELDS, save.player_id_to_index,
         lambda i: save.batting_values(i, 'R')),
        ('pitcher.dat', PITCHER_BITFIELDS, save.player_id_to_pitcher_index,
         save.pitcher_values),
    ]
    for name, fields, indexes, getter in table_specs:
        t = db.tables[name]
        ids = {v:k for k,v in t.fields.items()}
        checked = 0
        for key, row in t.rows:
            pid = int(key, 16)
            if pid == default_id and name != 'pitcher.dat':
                index = 0
            else:
                require(pid in indexes, f'{name}: ID {pid:#x} missing')
                index = indexes[pid]
            values = getter(index)
            absent = name == 'pitcher.dat' and row[ids['pitchattrib_pitch5_type']] == '15'
            if absent:
                absent_pitch5 += 1
            for field in fields:
                expected = row[ids[field]]
                if name == 'attrib.dat' and field == 'playerattrib_bunting' and int(expected) < 0:
                    bunting_sentinels[int(expected)] += 1
                    expected = '0'
                if absent and field.startswith('pitchattrib_pitch5_') and expected == '-':
                    expected = '0'
                require(str(values[field]) == expected,
                        f'{name}/{key}/{field}: {values[field]} != {expected}')
            checked += 1
        print(f'PASS {name}: {checked} rows, all mapped fields (documented sentinel rules)')
    require(bunting_sentinels == {-1:14, -2:8} and absent_pitch5 == 1152,
            'Sentinel sample counts differ')
    require(all(len(triples.get(i, set())) == 1 and
                save.player_id_to_pitcher_index.get(next(iter(triples[i]))) == 1609+i-3801
                for i in range(3801,3826)), 'General/pitcher CAP reserves disagree')
    print('PASS negative bunting/absent-pitch sentinels and 25 CAP reserve joins')
    require(save.general_record_base+4035*84 == SAVE_LH_BATTING_BASE-4 and
            SAVE_LH_BATTING_BASE+4035*16 == SAVE_RH_BATTING_BASE-4,
            'Full serialized general/batting capacity framing differs')
    for base, count, capacity, size in [
        (save.general_record_base,3826,4035,84),
        (SAVE_LH_BATTING_BASE,3826,4035,16),
        (SAVE_RH_BATTING_BASE,3826,4035,16),
        (SAVE_PITCHER_BASE,1634,1650,20),
    ]:
        require(raw[base+count*size:base+capacity*size] == bytes((capacity-count)*size),
                'Unused serialized reserve differs')
    for base in (save.general_record_base,SAVE_LH_BATTING_BASE,SAVE_RH_BATTING_BASE):
        require(struct.unpack_from('<I',raw,base-4)[0] == default_id,
                'Observed per-table header differs')
    print('PASS full serialized capacities, observed table headers and zero reserves')

    with tempfile.TemporaryDirectory(prefix='mvp07-check-') as directory:
        out = Path(directory)
        save.save(out/'roundtrip.sav')
        require((out/'roundtrip.sav').read_bytes() == raw, 'No-change save differs')
        if save.zip_member:
            save.save(out/'roundtrip.zip')
            with zipfile.ZipFile(save_path) as a, zipfile.ZipFile(out/'roundtrip.zip') as b:
                require(a.namelist() == b.namelist() and
                        all(a.read(n) == b.read(n) for n in a.namelist()), 'ZIP members differ')
        db.save(out/'roundtrip.big')
        rebuilt = BigArchive.load(out/'roundtrip.big')
        for entry in db.archive.entries:
            old = refpack_decompress(BigArchive.load(database).get(entry.name))
            new = refpack_decompress(rebuilt.get(entry.name))
            require(old == new, f'BIG decoded member differs: {entry.name}')
        RosterDatabase.load(out/'roundtrip.big')
        (out/'roster.bin').write_bytes(db.archive.get('roster.bin'))
        rd = RosterBinDocument.load(out/'roster.bin')
        rd.save(out/'roster-copy.bin')
        require(refpack_decompress((out/'roster-copy.bin').read_bytes()) == roster,
                'roster.bin no-change decoded bytes differ')
    print('PASS no-change raw save, ZIP members (if ZIP supplied), BIG decoded members and roster.bin')

    check_masks(save, 'general', save.general_record_base+84, 56,
                PLAYER_GENERAL_BITFIELDS, lambda c:save.set_player_general_values(1,c),
                lambda:save.player_general_values(1))
    for side, base in [('L',SAVE_LH_BATTING_BASE), ('R',SAVE_RH_BATTING_BASE)]:
        check_masks(save, f'{side} batting', base+16, 16, BATTING_BITFIELDS,
                    lambda c:save.set_batting_values(1,side,c), lambda:save.batting_values(1,side))
    check_masks(save, 'pitcher', SAVE_PITCHER_BASE+20, 20, PITCHER_BITFIELDS,
                lambda c:save.set_pitcher_values(1,c), lambda:save.pitcher_values(1),
                duplicate={'pitchattrib_stamina':(133,7)})
    print('Stock-profile checks complete. Game compatibility and expansion remain untested.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('database', type=Path)
    p.add_argument('save', type=Path)
    a = p.parse_args()
    verify(a.database, a.save)


if __name__ == '__main__':
    main()
