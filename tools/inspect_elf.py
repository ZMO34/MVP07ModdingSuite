#!/usr/bin/env python3
"""Read-only ELF32/MIPS inspection; never patches the user's executable.

Address xrefs are candidates from LUI + nearby ADDIU/ORI or load/store.
They are not a control-flow proof. Capstone is optional, for disassembly only.
R5900 LQ/SQ and three-operand MULT are decoded explicitly; other PS2 MMI
instructions remain raw words. This is an inspection aid, not a full EE decoder.
"""
from __future__ import annotations
import argparse
import hashlib
import re
import struct
from pathlib import Path

PROFILE_SHA256 = 'a8f01615db039a0e7fba9d5ccfe7a85728d5ec8d6fe368554777e12ef32c8642'
# Instruction fingerprints, not patches. See docs/research/executable.md.
PROFILE_WORDS = {
    0x6b1bfc: 0x2402001e,  # serialized roster count = 30
    0x6b1c8c: 0x24060120,  # serialized custom-ballpark-associated block
    0x6b1dd0: 0x240402d8,  # runtime team stride
    0x6f8a0c: 0x240302d8,
    0x6f8b78: 0x240302d8,
    0x6f805c: 0x2862001e,  # roster loop bounds / not-found sentinel
    0x6f85a4: 0x2862001e,
    0x6f8838: 0x2e02001e,
    0x6f8910: 0x2e02001e,
    0x6f8104: 0x3843001e,
    0x6f7a0c: 0x240600f0,  # clear 30 * 8 bytes
    0x19c558: 0x2862001a,  # >=26 validation branch
    0x19f684: 0x24050fc3,  # general player pool = 4035
    0x19f6c8: 0x24070fc3,
    0x19f6fc: 0x24070fc3,
    0x19f730: 0x24070fc3,
    0x1a04e4: 0x24050672,  # pitcher pool = 1650
    0x194928: 0x24050010,  # conference constructor = 16
    0x194978: 0x24050099,  # team constructor = 153 incl. sentinel
    0x19cb0c: 0x24050099,
    0x19cb50: 0x24070099,
    0x1c120c: 0x2e020099,
    0x1952e4: 0x2e420019,  # created-player initialization = 25
    0x43d6ac: 0x2842009a,  # uniform subsystem legacy <154 gate
    0x43d8bc: 0x308400ff,  # uniform lookup keys truncated to bytes
    0x43d8c4: 0x30a500ff,
    0x1be6a8: 0x00021902,  # four percentage getters and shared 7-bit mask
    0x1be6c0: 0x00021ac2,
    0x1be6d8: 0x00021c82,
    0x1be6f0: 0x00021e42,
    0x1be738: 0x3063007f,
    0x1a14fc: 0x24070004,  # generic per-table header is four bytes
    0x1be298: 0x24070054,  # general bulk transfer: capacity * 84
    0x1bef80: 0x00073900,  # batting bulk transfer: capacity * 16
    0x1b9ca0: 0x24070014,  # pitcher bulk transfer: capacity * 20
}


class Elf:
    def __init__(self, path):
        self.data = Path(path).read_bytes()
        if self.data[:6] != b'\x7fELF\x01\x01':
            raise ValueError('Expected little-endian ELF32')
        h = struct.unpack_from('<16sHHIIIIIHHHHHH', self.data)
        if h[2] != 8:
            raise ValueError('Expected MIPS ELF')
        self.entry = h[4]
        raw = [struct.unpack_from('<10I', self.data, h[6] + i*h[11]) for i in range(h[12])]
        names = self.data[raw[h[13]][4]:raw[h[13]][4]+raw[h[13]][5]]
        self.sections = []
        for s in raw:
            name = names[s[0]:].split(b'\0', 1)[0].decode('ascii', 'replace')
            self.sections.append(dict(name=name, type=s[1], flags=s[2], addr=s[3], offset=s[4], size=s[5]))

    def offset(self, va):
        for s in self.sections:
            if s['type'] != 8 and s['addr'] <= va < s['addr']+s['size']:
                return s['offset']+va-s['addr']
        raise ValueError(f'Unmapped VA {va:#x}')

    def words(self):
        for s in self.sections:
            if s['flags'] & 4:
                for i in range(0, s['size']-3, 4):
                    yield s['addr']+i, struct.unpack_from('<I', self.data, s['offset']+i)[0]

    def disasm(self, start, end):
        import capstone
        cs = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
        regs = ('zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 '
                's0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra').split()
        # Resume each word, preventing undecoded words from hiding later code.
        for va in range(start, end, 4):
            word = self.data[self.offset(va):self.offset(va)+4]
            w = int.from_bytes(word, 'little')
            op, rs, rt, rd = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
            if op in (0x1e, 0x1f):
                imm = w & 65535
                imm = imm if imm < 32768 else imm - 65536
                desc = f'{"lq" if op == 0x1e else "sq"} ${regs[rt]}, {imm:#x}(${regs[rs]})'
            elif op == 0 and (w & 63) in (0x18, 0x19):
                desc = ('multu' if w & 63 == 0x19 else 'mult') + ' '
                desc += (f'${regs[rd]}, ' if rd else '') + f'${regs[rs]}, ${regs[rt]}'
            elif op == 0x1c:
                desc = f'.word {w:#010x}  # R5900 MMI; not decoded'
            else:
                ins = next(cs.disasm(word, va), None)
                desc = ins.mnemonic + ' ' + ins.op_str if ins else f'.word {w:#010x}'
            print(f'{va:08x} {word.hex()}  {desc}')

    def xrefs(self, target):
        words = list(self.words())
        for i, (va,w) in enumerate(words):
            if w >> 26 != 15: continue
            reg = (w >> 16) & 31
            high = (w & 65535) << 16
            for v2,w2 in words[i+1:i+17]:
                if v2-va > 64: break
                op,rs,rt = w2>>26, (w2>>21)&31, (w2>>16)&31
                imm = w2 & 65535
                signed = imm if imm < 32768 else imm-65536
                if rs == reg and op in (8,9,13,24,25,32,33,35,36,37,40,41,43,55,63):
                    value = (high | imm) if op == 13 else (high+signed)&0xffffffff
                    if value == target: print(f'{va:08x} -> {v2:08x} target={target:08x} opcode={op}')
                # Stop if the base register is overwritten (conservative).
                if (op in (8,9,12,13,14,15,24,25,32,33,35,36,37,55) and rt == reg) or (op == 0 and ((w2>>11)&31) == reg): break


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf', type=Path)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('info')
    sub.add_parser('verify', help='verify the researched executable hash and instruction fingerprints')
    q = sub.add_parser('strings'); q.add_argument('pattern')
    q = sub.add_parser('disasm'); q.add_argument('start', type=lambda x:int(x,0)); q.add_argument('end', type=lambda x:int(x,0))
    q = sub.add_parser('xrefs'); q.add_argument('address', type=lambda x:int(x,0))
    q = sub.add_parser('calls'); q.add_argument('address', type=lambda x:int(x,0))
    a = p.parse_args(); e = Elf(a.elf)
    if a.command == 'verify':
        digest = hashlib.sha256(e.data).hexdigest()
        if digest != PROFILE_SHA256:
            p.exit(1, f'Unsupported executable SHA256: {digest}\n')
        for va, expected in PROFILE_WORDS.items():
            actual = struct.unpack_from('<I', e.data, e.offset(va))[0]
            if actual != expected:
                p.exit(1, f'Fingerprint mismatch at {va:#x}: {actual:#010x} != {expected:#010x}\n')
        print(f'PASS: researched SHA256 and {len(PROFILE_WORDS)} instruction fingerprints')
    elif a.command == 'info':
        print(f'SHA256 {hashlib.sha256(e.data).hexdigest()}\nentry={e.entry:#x} bytes={len(e.data)}')
        for s in e.sections: print(s)
    elif a.command == 'disasm': e.disasm(a.start, a.end)
    elif a.command == 'xrefs': e.xrefs(a.address)
    elif a.command == 'calls':
        for va,w in e.words():
            if w>>26 in (2,3) and (((va+4)&0xf0000000)|((w&0x3ffffff)<<2)) == a.address:
                print(f'{va:08x} {"jal" if w>>26 == 3 else "j"} {a.address:08x}')
    else:
        pat = re.compile(a.pattern, re.I)
        for s in e.sections:
            if s['type'] == 8: continue
            for m in re.finditer(rb'[ -~]{4,}', e.data[s['offset']:s['offset']+s['size']]):
                value=m.group().decode('ascii')
                if pat.search(value): print(f"{s['addr']+m.start():08x} {value}")


if __name__ == '__main__': main()
