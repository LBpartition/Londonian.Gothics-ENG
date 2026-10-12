"""Render a labelled review sheet: game glyph (pixel font) next to the transcribed character."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
from render_font import load_tiles, load_palette, glyph_img
from glyph_table import build, UNSURE

def main(out):
    tiles, pal, table = load_tiles(), load_palette(), build()
    jp = ImageFont.truetype(r"C:\Windows\Fonts\msgothic.ttc", 26)
    small = ImageFont.truetype(r"C:\Windows\Fonts\msgothic.ttc", 14)
    cols, cw, ch = 16, 112, 70
    n = len(table)
    rows = (n + cols - 1) // cols
    head = 40
    sheet = Image.new("RGB", (cols * cw, rows * ch + head), (20, 20, 40))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), "Londonian Gothics font (data/font.NCGR) - 583 glyphs. Left: game glyph 2x. Right: transcribed char. "
                   "Yellow = hex ID, red = unsure. Row label = high digits.", font=small, fill=(255, 255, 255))
    for g in range(n):
        x, y = (g % cols) * cw, (g // cols) * ch + head
        d.rectangle([x, y, x + cw - 1, y + ch - 1], outline=(60, 60, 90))
        d.text((x + 4, y + 2), f"0x{g:03X}", font=small, fill=(255, 80, 80) if g in UNSURE else (255, 220, 0))
        sheet.paste(glyph_img(tiles, g, 2, 2, pal).resize((32, 32), Image.NEAREST), (x + 6, y + 22))
        c = table[g]
        if c.startswith("{"):
            d.text((x + 46, y + 30), c, font=small, fill=(150, 220, 255))
        else:
            d.text((x + 52, y + 24), c, font=jp, fill=(150, 220, 255))
    sheet.save(out)
    print(out, sheet.size)

if __name__ == "__main__":
    main(sys.argv[1])
