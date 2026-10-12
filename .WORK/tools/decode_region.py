"""Decode u16 glyph-index text from a binary region.

Usage: python decode_region.py <file> <start_hex> <end_hex> [out.tsv]
Splits on 0x0000 terminators; 0xFFFF shown as {FFFF}; unknown values as {xHHHH}.
Only runs where >=60% of units are valid glyphs are printed as text.
"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from glyph_table import build

T = build()

def decode_units(units):
    out = []
    for u in units:
        if u == 0xFFFF: out.append("{FFFF}")
        elif u in T: out.append(T[u])
        else: out.append(f"{{x{u:04X}}}")
    return "".join(out)

def main():
    path, s, e = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
    out = sys.argv[4] if len(sys.argv) > 4 else None
    d = Path(path).read_bytes()[s:e]
    units = [struct.unpack_from("<H", d, i)[0] for i in range(0, len(d) - 1, 2)]
    lines, cur, cur_off = [], [], s
    for i, u in enumerate(units):
        if u == 0:
            if cur:
                valid = sum(1 for x in cur if x in T or x == 0xFFFF) / len(cur)
                lines.append((cur_off, len(cur), valid, decode_units(cur)))
            cur = []; cur_off = s + (i + 1) * 2
        else:
            if not cur: cur_off = s + i * 2
            cur.append(u)
    rows = [f"0x{o:05X}\t{n}\t{v:.2f}\t{t}" for o, n, v, t in lines if v >= 0.6]
    text = "offset\tunits\tvalid\ttext\n" + "\n".join(rows) + "\n"
    if out: Path(out).write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)

if __name__ == "__main__":
    main()
