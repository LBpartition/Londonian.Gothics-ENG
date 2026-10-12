"""Render the full patched glyph table (original + English additions) as a shareable PNG."""
import struct, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, font_patch as FP
from test01_build import glyph_tiles

W = Path(__file__).resolve().parent.parent
rom = (W / "rom/JPN-original.nds").read_bytes()
font = FP.patch_font(ndsbuild.get_file(rom, ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]))
n = struct.unpack_from("<I", font, 0x28)[0] // 128
lab = dict(FP._T)
names = {FP.SPACE: "space", FP.APOS: "'", FP.COMMA: ",", FP.HYPHEN: "-", FP.ASTER: "*"}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): names[FP.NARROW0 + i] = c
lab.update(names)
eng = {v for v in FP.ASCII.values()}
SC, COLS, CW, CH = 3, 16, 64, 92
f_jp = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 15)
f_hd = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 22)
rows = (n + COLS - 1) // COLS
top = 120
img = Image.new("RGB", (COLS * CW + 20, top + rows * CH + 60), (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10, 10), "Londonian Gothics - English patch glyph table (data/font.NCGR)", fill=0, font=f_hd)
d.text((10, 44), f"{n} glyphs, 16x16 px, 2bpp. 0x000-0x246 original Japanese font; 0x247-0x{n-1:03X} added by the patch (red).", fill=0, font=f_jp)
d.text((10, 66), "Blue label = glyph the English text encoder uses for that character. Codes are 16-bit glyph indices.", fill=0, font=f_jp)
d.text((10, 88), "{TAG} = special symbol/icon.", fill=0, font=f_jp)
SHADE = [(255, 255, 255), (0, 0, 0), (110, 110, 110), (190, 190, 190)]
for g in range(n):
    x0, y0 = 10 + (g % COLS) * CW, top + (g // COLS) * CH
    new = g >= FP.ORIG_GLYPHS
    d.rectangle([x0, y0, x0 + CW - 2, y0 + CH - 2], outline=(220, 0, 0) if new else (200, 200, 200), width=2 if new else 1)
    px = glyph_tiles(font[FP.TILE_OFF + g * 128: FP.TILE_OFF + (g + 1) * 128])
    gi = Image.new("RGB", (16, 16), (245, 245, 235))
    for y in range(16):
        for x in range(16):
            if px[y][x]: gi.putpixel((x, y), SHADE[px[y][x] & 3])
    img.paste(gi.resize((48, 48), Image.NEAREST), (x0 + 7, y0 + 4))
    d.text((x0 + 4, y0 + 55), f"{g:03X}", fill=(220, 0, 0) if new else (90, 90, 90), font=f_jp)
    t = lab.get(g, "?")
    d.text((x0 + 4, y0 + 72), t[:7], fill=(0, 70, 200) if g in eng else 0, font=f_jp)
out = W.parent / "Glyph-table.png"
img.save(out); print(out, n, img.size)
