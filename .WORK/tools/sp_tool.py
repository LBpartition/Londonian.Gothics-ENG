"""Londonian Gothics .sp event-script tool.

Format: "LG", u16 entry offset (+2), u16 map offset (+4), map, event bytecode,
then a pool of 0x0000-terminated u16 glyph strings at the end of the file.
Text ops: 00 <u16 ptr> (narration), 01 <spk> <u16 ptr> (speaker line).
All pointers are absolute u16 file offsets.

Usage:
  python tools/sp_tool.py verify            # parse + byte-identical rebuild of all files
  python tools/sp_tool.py dump OUT.json     # dump every string (decoded) to JSON
"""
import glob, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPDIR = os.path.join(ROOT, 'extracted', 'data', 'data')

OPLEN = {0: 3, 1: 4, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 2, 9: 2, 0xA: 6, 0xB: 10, 0xC: 1,
         0xD: 1, 0xE: 1, 0xF: 1, 0x10: 4, 0x11: 1, 0x12: 2, 0x13: 4, 0x14: 4, 0x15: 2,
         0x16: 2, 0x17: 1, 0x18: 1, 0x19: 2, 0x1A: 2, 0x1B: 2}
TERM = (0x0F, 0x10)          # scene transition: script ends
CTRL = {0xFFFF: '{NL}', 0xFFFE: '{WAIT}', 0xFD00: '{NAME}'}


def load_glyphs():
    g = {}
    with open(os.path.join(ROOT, 'phase2', 'glyph_table.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            g[int(p[0], 16)] = p[1]
    return g


def _ptr_field(d, a):
    op = d[a]
    if op == 0:
        return a + 1
    if op == 1:
        return a + 2
    return None


def parse(d):
    """Return dict with entry, pool start, ptr fields {field_off: target}, strings."""
    ent = struct.unpack_from('<H', d, 2)[0]
    seen, stack = set(), [ent]
    while stack:
        a = stack.pop()
        while a < len(d) and a not in seen:
            op = d[a]
            if op not in OPLEN:
                raise ValueError('bad opcode %02X at %X' % (op, a))
            seen.add(a)
            if op == 5:
                stack.append(struct.unpack_from('<H', d, a + 1)[0]); break
            if op in (6, 7):
                stack.append(struct.unpack_from('<H', d, a + 2)[0])
            if op in TERM:
                break
            a += OPLEN[op]
    fields, spk = {}, {}
    for a in seen:
        f = _ptr_field(d, a)
        if f is not None:
            fields[f] = struct.unpack_from('<H', d, f)[0]
            spk[f] = d[a + 1] if d[a] == 1 else None
    if not fields:
        return {'entry': ent, 'pool': None, 'fields': {}, 'strings': [], 'ops': []}
    pool = min(fields.values())
    # sweep unreached (dead) code between entry and pool for extra text pointers
    cov = set()
    for a in seen:
        cov.update(range(a, a + OPLEN[d[a]]))
    a = ent
    while a < pool:
        if a in cov:
            a += 1; continue
        b = a
        while b < pool and b not in cov and d[b] in OPLEN and b + OPLEN[d[b]] <= pool:
            f = _ptr_field(d, b)
            if f is not None:
                t = struct.unpack_from('<H', d, f)[0]
                if t >= pool:
                    fields[f] = t
                    spk[f] = d[b + 1] if d[b] == 1 else None
            b += OPLEN[d[b]]
        a = max(b, a + 1)
    strings, a = [], pool
    while a < len(d):
        s = []
        while True:
            v = struct.unpack_from('<H', d, a)[0]; a += 2
            if v == 0:
                break
            s.append(v)
        strings.append((a - 2 * len(s) - 2, s))
    if a != len(d):
        raise ValueError('pool does not end at EOF')
    starts = {o for o, _ in strings}
    bad = [hex(t) for t in fields.values() if t not in starts]
    if bad:
        raise ValueError('pointers not at string starts: %s' % bad)
    unref = [hex(o) for o, _ in strings if o not in set(fields.values())]
    # text ops in code order: (field_off, speaker or None, target)
    ops = [(f, spk[f], t)
           for f, t in sorted(fields.items())]
    if unref:
        raise ValueError('unreferenced strings: %s' % unref)
    return {'entry': ent, 'pool': pool, 'fields': fields, 'strings': strings, 'ops': ops}


def _ptr_fields_all(d, lo, hi):
    """Every absolute pointer field in the script: [(field_off, target)].
    Follows jumps (05/06/07), event handlers (0A @+3, 0B @+4; 0 = none) and text
    (00/01), then linearly sweeps unreached bytes so dead code is shifted too."""
    ent = struct.unpack_from('<H', d, 2)[0]
    out, seen, stack = {}, set(), [ent]

    def fields_of(a):
        op = d[a]
        r = []
        if op in (0, 1, 5):
            r.append(a + (2 if op == 1 else 1))
        elif op in (6, 7):
            r.append(a + 2)
        elif op == 0xA:
            r.append(a + 3)
        elif op == 0xB:
            r.append(a + 4)
        return [(f, struct.unpack_from('<H', d, f)[0]) for f in r]

    while stack:
        a = stack.pop()
        while lo <= a < hi and a not in seen:
            op = d[a]
            if op not in OPLEN:
                raise ValueError('bad opcode %02X at %X' % (op, a))
            seen.add(a)
            for f, t in fields_of(a):
                if t:
                    out[f] = t
                    if op != 0 and op != 1 and lo <= t < hi:
                        stack.append(t)
            if op == 5 or op in TERM:
                break
            a += OPLEN[op]
    cov = set()
    for a in seen:
        cov.update(range(a, a + OPLEN[d[a]]))
    a = ent
    while a < hi:
        if a in cov or d[a] not in OPLEN or a + OPLEN[d[a]] > hi:
            a += 1; continue
        for f, t in fields_of(a):
            if lo <= t < len(d) and f not in out and t:
                out[f] = t
        a += OPLEN[d[a]]
    return out


def get_name(d):
    mp = struct.unpack_from('<H', d, 4)[0]
    s = list(struct.unpack_from('<%dH' % ((mp - 0x10) // 2), d, 0x10))
    return s[:s.index(0)]


def set_name(d, codes):
    """Replace the header location name (0x10 .. map offset) and shift the rest."""
    ent, mp = struct.unpack_from('<HH', d, 2)
    slot = list(codes) + [0]
    while (len(slot) * 2 - (mp - 0x10)) % 4:
        slot.append(0)
    delta = 0x10 + len(slot) * 2 - mp
    info = parse(d)
    hi = info['pool'] if info['pool'] is not None else len(d)
    ptrs = _ptr_fields_all(d, ent, hi)
    out = bytearray(d[:0x10]) + struct.pack('<%dH' % len(slot), *slot) + d[mp:]
    struct.pack_into('<HH', out, 2, ent + delta, mp + delta)
    for f, t in ptrs.items():
        if t >= mp:
            struct.pack_into('<H', out, f + delta, t + delta)
    if len(out) > 0xFFFF:
        raise ValueError('file exceeds u16 pointer range')
    return bytes(out)


def rebuild(d, info, new_strings):
    """new_strings: list of u16 lists, same count/order as info['strings']."""
    if info['pool'] is None:
        return bytes(d)
    assert len(new_strings) == len(info['strings'])
    out = bytearray(d[:info['pool']])
    remap = {}
    for (old, _), s in zip(info['strings'], new_strings):
        remap[old] = len(out)
        out += struct.pack('<%dH' % (len(s) + 1), *s, 0)
    if len(out) > 0xFFFF:
        raise ValueError('file exceeds u16 pointer range')
    for f, t in info['fields'].items():
        struct.pack_into('<H', out, f, remap[t])
    return bytes(out)


def all_files():
    return sorted(glob.glob(os.path.join(SPDIR, 'sp*.sp')))


def decode(s, g):
    return ''.join(CTRL.get(v, g.get(v, '{%03X}' % v)) for v in s)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    g = load_glyphs()
    if cmd == 'verify':
        n = ns = 0
        for p in all_files():
            d = open(p, 'rb').read()
            info = parse(d)
            same = rebuild(d, info, [s for _, s in info['strings']])
            assert same == d, p
            # growth test: triple every string, re-parse, compare contents
            grown = [s * 3 for _, s in info['strings']]
            r = rebuild(d, info, grown)
            i2 = parse(r)
            assert [s for _, s in i2['strings']] == grown, p
            n += 1; ns += len(info['strings'])
        print('OK %d files, %d strings, identity + growth round-trip' % (n, ns))
    elif cmd == 'dump':
        out = []
        for p in all_files():
            d = open(p, 'rb').read()
            info = parse(d)
            idx = {o: i for i, (o, _) in enumerate(info['strings'])}
            done = set()
            for order, (f, sp, t) in enumerate(info['ops']):
                if t in done:
                    continue
                done.add(t)
                out.append({'file': os.path.basename(p), 'idx': idx[t], 'off': t,
                            'order': order, 'op_at': f, 'speaker': sp,
                            'jp': decode(info['strings'][idx[t]][1], g)})
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('dumped %d strings' % len(out))


if __name__ == '__main__':
    main()
