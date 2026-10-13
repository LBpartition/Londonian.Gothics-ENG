"""Prologue story roll (bottom screen intro): repaint data/title_roll_full_16.NCGR.

The JP text is a pre-drawn 256x688 4bpp bitmap (tiles stored linearly, 32 per row),
NOT glyph text. English = _script_en.json "intro" (guide "[00].Prologue Story Roll"), split into the same 7
blocks as the JP; each block starts on the same pixel row as the original so the
paragraph spacing/scroll timing is preserved. Tile count and palette are unchanged.
"""
import struct, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FILE = "data/title_roll_full_16.NCGR"
FONT = r"C:\Windows\Fonts\georgia.ttf"
W, H, X0, X1 = 256, 688, 8, 249
BLOCK_Y = [1, 93, 209, 324, 440, 555, 671]   # first text row of each JP block
sys.path.insert(0, str(Path(__file__).parent))
import master
BLOCKS = [master.join(e["en"]) for e in master.EN["intro"]]   # tools-resources/_script_en.json "intro"
SIZE, PITCH = 12, 16
LIGHT, DARK = (224, 200, 192), (48, 40, 32)


class FitError(Exception):
    pass


def wrap(text, font):
    if "\n" in text:   # exact lines from _script_en.json
        return [l for p in text.split("\n") for l in wrap(p, font)]
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= X1 - X0:
            cur = t
        else:
            if not cur:
                raise FitError(f"word too wide: {w}")
            lines.append(cur); cur = w
    return lines + [cur]


def layout():
    font = ImageFont.truetype(FONT, SIZE)
    out = []
    for k, (y, txt) in enumerate(zip(BLOCK_Y, BLOCKS)):
        lines = wrap(txt, font)
        end = y + (len(lines) - 1) * PITCH + 14
        limit = BLOCK_Y[k + 1] - 8 if k + 1 < len(BLOCK_Y) else H
        if end > limit:
            raise FitError(f"block {k} ends at {end} > {limit}: {lines}")
        out.append((y, lines))
    return font, out


def render(pal):
    font, blocks = layout()
    cov = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(cov)
    for y, lines in blocks:
        for i, ln in enumerate(lines):
            d.text((X0, y + i * PITCH), ln, font=font, fill=255)
    a = cov.load()
    cand = [i for i in range(3, 15)] + [1]
    idx = [[0] * W for _ in range(H)]
    for yy in range(H):
        for xx in range(W):
            t = a[xx, yy] / 255
            s = a[xx - 1, yy - 1] / 255 if xx and yy else 0
            if t < 0.08 and s < 0.25:
                continue
            base = DARK if t < 0.08 else tuple(DARK[c] + (LIGHT[c] - DARK[c]) * t for c in range(3))
            idx[yy][xx] = min(cand, key=lambda i: sum((pal[i][c] - base[c]) ** 2 for c in range(3)))
    return idx, blocks


def patch(ncgr, nclr):
    pal = []
    for i in range(16):
        v = struct.unpack_from("<H", nclr, 0x28 + i * 2)[0]
        pal.append(((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8))
    idx, blocks = render(pal)
    t = bytearray(ncgr)
    assert len(t) - 0x30 == (W // 8) * (H // 8) * 32 + (len(t) - 0x30 - (W // 8) * (H // 8) * 32)
    for yy in range(H):
        for xx in range(0, W, 2):
            o = 0x30 + ((yy // 8) * 32 + xx // 8) * 32 + (yy % 8) * 4 + (xx % 8) // 2
            t[o] = idx[yy][xx] | (idx[yy][xx + 1] << 4)
    return bytes(t), blocks


def preview(ncgr, nclr, path):
    pal = [struct.unpack_from("<H", nclr, 0x28 + i * 2)[0] for i in range(16)]
    im = Image.new("RGB", (W, H))
    px = im.load()
    for yy in range(H):
        for xx in range(W):
            b = ncgr[0x30 + ((yy // 8) * 32 + xx // 8) * 32 + (yy % 8) * 4 + (xx % 8) // 2]
            v = pal[(b >> (4 * (xx & 1))) & 15]
            px[xx, yy] = ((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8)
    im.save(path)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    import ndsbuild
    rom = Path(sys.argv[1]).read_bytes()
    ids = ndsbuild.file_ids_by_path(rom)
    g = lambda n: ndsbuild.get_file(rom, ids[n])
    new, blocks = patch(g(FILE), g("data/title_roll_full_16.NCLR"))
    for y, l in blocks:
        print(y, l)
    preview(new, g("data/title_roll_full_16.NCLR"), sys.argv[2])
