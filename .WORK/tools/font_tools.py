"""Test build 01: OPTION labels + appended font glyphs + DRESS ruler strings.

Appends glyph 0x247 (blank space) and 0x248 (apostrophe, derived from the " glyph 0xB0)
to font.NCGR, then edits arm9 strings in place (within their existing fixed slots).
"""
import struct, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild

W = Path(__file__).resolve().parent.parent
ORIG = W / "tools-resources" / ".ROM_JPN.nds"
def build_table():
    """Original glyphs (0x000-0x246): id -> character, read from tools-resources/_glyph_table.tsv."""
    rows = [l.rstrip("\n").split("\t") for l in open(W / "tools-resources" / "_glyph_table.tsv", encoding="utf-8")][1:]
    return {int(r[0], 16): r[1] for r in rows if r[0] and int(r[0], 16) < 0x247}


T = build_table()
C2G = {v: k for k, v in T.items() if len(v) == 1}
SPACE, APOS, NL = 0x247, 0x248, 0xFFFF


def enc(s):
    out = []
    for ch in s:
        if ch == " ": out.append(SPACE)
        elif ch == "'": out.append(APOS)
        elif ch == "\n": out.append(NL)
        else: out.append(C2G[ch])
    return out


def put(arm9, off, slot_units, s):
    u = enc(s)
    if len(u) >= slot_units:
        raise ValueError(f"{s!r} needs {len(u)+1} units, slot {slot_units}")
    u += [0] * (slot_units - len(u))
    arm9[off:off + slot_units * 2] = struct.pack(f"<{slot_units}H", *u)


def glyph_tiles(g):  # 16x16 glyph -> 4 tiles row-major, 4bpp -> 2D pixel list
    px = [[0] * 16 for _ in range(16)]
    for t in range(4):
        tx, ty = (t % 2) * 8, (t // 2) * 8
        tile = g[t * 32:(t + 1) * 32]
        for i, b in enumerate(tile):
            y, x = i // 4, (i % 4) * 2
            px[ty + y][tx + x] = b & 0xF
            px[ty + y][tx + x + 1] = b >> 4
    return px


def pack_glyph(px):
    out = bytearray()
    for t in range(4):
        tx, ty = (t % 2) * 8, (t // 2) * 8
        for y in range(8):
            for x in range(0, 8, 2):
                out.append(px[ty + y][tx + x] | (px[ty + y][tx + x + 1] << 4))
    return bytes(out)


def build_font(font):
    d = bytearray(font)
    tile_off = 0x10 + 0x20
    n = struct.unpack_from("<I", d, 0x28)[0] // 128
    assert n == 583
    quote = glyph_tiles(d[tile_off + 0xB0 * 128: tile_off + 0xB1 * 128])
    # keep only the left mark of the " glyph
    cols = [x for x in range(16) if any(quote[y][x] for y in range(16))]
    mid = (min(cols) + max(cols)) // 2
    apos = [[quote[y][x] if x <= mid else 0 for x in range(16)] for y in range(16)]
    # centre it
    acols = [x for x in range(16) if any(apos[y][x] for y in range(16))]
    shift = (16 - (max(acols) - min(acols) + 1)) // 2 - min(acols)
    apos = [[apos[y][x - shift] if 0 <= x - shift < 16 else 0 for x in range(16)] for y in range(16)]
    extra = bytes(128) + pack_glyph(apos)
    d[tile_off + n * 128: tile_off + n * 128] = extra
    struct.pack_into("<I", d, 0x08, struct.unpack_from("<I", d, 0x08)[0] + len(extra))
    struct.pack_into("<I", d, 0x14, struct.unpack_from("<I", d, 0x14)[0] + len(extra))
    struct.pack_into("<I", d, 0x28, struct.unpack_from("<I", d, 0x28)[0] + len(extra))
    return bytes(d)


def main(out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rom = ORIG.read_bytes()
    ids = ndsbuild.file_ids_by_path(rom)
    fid = ids["data/font.NCGR"]
    font = build_font(ndsbuild.get_file(rom, fid))
    arm9 = bytearray((W / "extracted" / "arm9.bin").read_bytes())
    put(arm9, 0x4C438, 12, "TEXT SPEED")
    put(arm9, 0x4C450, 12, "BACKLIGHT")
    put(arm9, 0x48000, 7, "ABCDEF")
    put(arm9, 0x48290, 24, "ABCDEFGHIJKL\nM'N O12345")
    out = bytearray(ndsbuild.build(rom, {fid: font}))
    a9_off, a9_size = struct.unpack_from("<II", out, 0x20)[0], struct.unpack_from("<I", out, 0x2C)[0]
    assert len(arm9) >= a9_size
    out[a9_off:a9_off + a9_size] = arm9[:a9_size]
    out = bytes(out)
    p = out_dir / "TEST01-option-font-ruler.nds"
    p.write_bytes(out)
    print(p, len(out), hashlib.sha256(out).hexdigest().upper())


if __name__ == "__main__":
    main(sys.argv[1])

