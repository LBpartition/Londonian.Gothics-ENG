"""Phase 2: render data/font.NCGR as a labelled glyph sheet.

NCGR (RGCN) CHAR section: 4bpp tiles, 32 bytes per 8x8 tile, 1D mapping.
Usage: python render_font.py <glyph_w_tiles> <glyph_h_tiles> <out.png> [cols] [scale]
Glyph N = tiles [N*w*h, (N+1)*w*h) laid out row-major inside the glyph.
"""
import struct, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "extracted" / "data" / "data"

def load_tiles():
    d = (FONT / "font.NCGR").read_bytes()
    sec = 16
    size, off = struct.unpack_from("<II", d, sec + 0x18)
    data = d[sec + 8 + off: sec + 8 + off + size] if False else d[sec + 0x20: sec + 0x20 + size]
    return [data[i:i + 32] for i in range(0, len(data), 32)]

def load_palette():
    d = (FONT / "font.NCLR").read_bytes()
    sec = 16
    poff = struct.unpack_from("<I", d, sec + 0x14)[0]
    raw = d[sec + 8 + poff:]
    pal = []
    for i in range(0, len(raw) - 1, 2):
        c = struct.unpack_from("<H", raw, i)[0]
        pal.append(((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31))
    return pal

def tile_img(t, pal):
    im = Image.new("RGB", (8, 8))
    px = im.load()
    for y in range(8):
        for x in range(8):
            b = t[y * 4 + x // 2]
            v = (b >> 4) if x & 1 else (b & 15)
            px[x, y] = pal[v] if v else (40, 40, 40)
    return im

def glyph_img(tiles, idx, gw, gh, pal):
    im = Image.new("RGB", (gw * 8, gh * 8), (40, 40, 40))
    base = idx * gw * gh
    for ty in range(gh):
        for tx in range(gw):
            k = base + ty * gw + tx
            if k < len(tiles):
                im.paste(tile_img(tiles[k], pal), (tx * 8, ty * 8))
    return im

def main():
    gw, gh, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    cols = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    first = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    count = int(sys.argv[6]) if len(sys.argv) > 6 else None
    tiles = load_tiles()
    pal = load_palette()
    n = len(tiles) // (gw * gh)
    ids = list(range(first, n if count is None else min(n, first + count)))
    cw, ch = gw * 8 + 4, gh * 8 + 10
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (0, 0, 60))
    dr = ImageDraw.Draw(sheet)
    for i, g in enumerate(ids):
        x, y = (i % cols) * cw, (i // cols) * ch
        sheet.paste(glyph_img(tiles, g, gw, gh, pal), (x + 2, y + 9))
        dr.text((x + 2, y - 1), f"{g:X}", fill=(255, 255, 0))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(out)
    print(f"tiles={len(tiles)} glyphs={n} rendered={len(ids)} -> {out}")

if __name__ == "__main__":
    main()
