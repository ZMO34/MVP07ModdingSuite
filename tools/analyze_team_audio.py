#!/usr/bin/env python3
"""Read-only DBMisc/stock-roster joins; no game assets are written or patched.

Accept DATABASE.BIG, compressed roster.bin, or its decoded stock payload.
JSON contains all team joins; --verify-stock checks the supplied vanilla profile.
School CSV entries are CAT vocabulary, not the stock school-ID name dictionary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import struct
from pathlib import Path

from extract_big import parse_bigf
from parse_roster import parse_decompressed
from refpack import decompress


def members(path: Path) -> dict[str, bytes]:
    raw, entries = parse_bigf(path)
    return {e.name: raw[e.offset:e.offset + e.size] for e in entries}


def rows(raw: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(raw.decode('latin-1'))))


def analyze(roster_path: Path, dbmisc_path: Path) -> dict:
    raw = roster_path.read_bytes()
    if raw[:4] == b'BIGF':
        raw = members(roster_path)['roster.bin']
    decoded = decompress(raw) if raw[1:2] == b'\xfb' else raw
    _, teams = parse_decompressed(decoded)
    misc = members(dbmisc_path)
    schools = {int(i): name for i, name in rows(misc['schoolnameaudio.csv'])[1:]}
    nicknames = {int(i): name for i, name in rows(misc['nicknameaudio.csv'])[1:]}
    # Abbreviations are non-unique; join by the explicit logo ID instead.
    infos = {int(r[1]): r for r in rows(misc['teaminfo.csv'])[1:]}
    uniform = misc['uniform.bin']
    count = int.from_bytes(uniform[:2], 'little')
    if len(uniform) != 2 + count * 7:
        raise ValueError('Uniform count/stride mismatch')
    keys = [tuple(uniform[2 + i*7:4 + i*7]) for i in range(count)]
    joined = []
    for team in teams:
        start = 491 + team.index * 687
        word = struct.unpack_from('<I', decoded, start + 0xa0)[0]
        school = (word >> 12) & 0x1ff
        nickname = (word >> 21) & 0x1ff
        art = (struct.unpack_from('<I', decoded, start + 0xa4)[0] >> 1) & 0x1ff
        info = infos.get(art)
        joined.append(dict(
            team_index=team.index, team_record_id=team.index + 1,
            team=team.full_name, nickname=team.nickname,
            school_audio_id=school, school_csv_name=schools.get(school),
            nickname_audio_id=nickname, nickname_csv_name=nicknames.get(nickname),
            nickname_exact_match=nicknames.get(nickname) == team.nickname,
            logo_id=art, teaminfo_logo_id=int(info[1]) if info else None,
            teaminfo_text_match=bool(info and (team.abbreviation, team.nickname, team.city) ==
                                     (info[0], info[2], info[3])),
            teaminfo_location_match=bool(info and (word & 0x3f) == int(info[4])),
            stadium_selector=(struct.unpack_from('<I', decoded, start + 0xa8)[0] >> 4) & 0x3f,
        ))
    # Exact names only: Wolf Pack (100) and Wolfpack (101) are distinct entries.
    matched_schools = [dict(team=t['team'], stock_id=t['school_audio_id'],
                            cat_id=i) for t in joined for i, n in schools.items()
                       if n == t['team']]
    return dict(
        input_sha256={roster_path.name: hashlib.sha256(roster_path.read_bytes()).hexdigest(),
                      dbmisc_path.name: hashlib.sha256(dbmisc_path.read_bytes()).hexdigest()},
        decoded_roster_sha256=hashlib.sha256(decoded).hexdigest(),
        dbmisc_members=list(misc),
        summary=dict(team_count=len(joined), nickname_exact_matches=sum(t['nickname_exact_match'] for t in joined),
                     nickname_unique_ids=len({t['nickname_audio_id'] for t in joined}),
                     nickname_extended_teams=sum(t['nickname_audio_id'] >= 201 for t in joined),
                     school_matches_logo=sum(t['school_audio_id'] == t['logo_id'] for t in joined),
                     school_csv_direct_id_hits=sum(t['school_csv_name'] is not None for t in joined),
                     teaminfo_logo_matches=sum(t['logo_id'] == t['teaminfo_logo_id'] for t in joined),
                     teaminfo_text_matches=sum(t['teaminfo_text_match'] for t in joined),
                     teaminfo_location_matches=sum(t['teaminfo_location_match'] for t in joined),
                     school_csv_count=len(schools), nickname_csv_count=len(nicknames),
                     uniform_count=count, uniform_unique_keys=len(set(keys))),
        uniform_keys=keys, school_name_overlap=matched_schools, teams=joined,
    )


def verify_stock(result: dict) -> None:
    s = result['summary']
    expected = dict(team_count=152, nickname_exact_matches=152, nickname_unique_ids=120,
                    school_matches_logo=152, school_csv_direct_id_hits=0,
                    teaminfo_logo_matches=152, teaminfo_text_matches=152,
                    teaminfo_location_matches=152, school_csv_count=160,
                    nickname_csv_count=212, uniform_count=304, uniform_unique_keys=304)
    for name, value in expected.items():
        if s[name] != value:
            raise ValueError(f'Stock check {name}: {s[name]} != {value}')
    if set(result['uniform_keys']) != {(i, v) for i in range(1, 153) for v in (0, 1)}:
        raise ValueError('Uniform keys do not match ordinal team IDs 1..152 x 0/1')
    ids = {t['school_audio_id'] for t in result['teams']}
    if ids != set(range(1, 154)) - {50}:
        raise ValueError('Unexpected stock school/audio ID namespace')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('roster', type=Path)
    p.add_argument('dbmisc', type=Path)
    p.add_argument('--verify-stock', action='store_true')
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    result = analyze(a.roster, a.dbmisc)
    if a.verify_stock:
        verify_stock(result)
    print(json.dumps(result if a.json else result['summary'], indent=2))


if __name__ == '__main__':
    main()
