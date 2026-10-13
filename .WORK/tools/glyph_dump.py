"""Export tools-resources/_glyph_table.tsv to tools-resources/GLYPHS - EDIT and IMPORT.txt,
an easy-to-edit text file with every glyph drawn as a 16x16 grid of characters,
plus GLYPHS - PREVIEW.png, a picture of every glyph (for reference only).

Original glyphs (0x000-0x246) are drawn from the game font (extracted/data/data/font.NCGR,
created by extract_rom.py). CUSTOM glyphs (0x247 onwards) are drawn from _glyph_table.tsv.
Edit the text file, then run glyph_import.py to write the changes back into _glyph_table.tsv.

Usage (from .WORK):  python tools\\glyph_dump.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from font_tools import glyph_tiles

W = Path(__file__).resolve().parents[1]
TSV = W / "tools-resources" / "_glyph_table.tsv"
TXT = W / "tools-resources" / "GLYPHS - EDIT and IMPORT.txt"
PNG = W / "tools-resources" / "GLYPHS - PREVIEW.png"
FONT = W / "extracted" / "data" / "data" / "font.NCGR"
ORIG_GLYPHS = 0x247
SIZE = 16
SHADES = ".123456789ABCDEF"
SEP = "-" * 41

HEADER = """\
GLYPHS - EDIT and IMPORT.txt
=================
Every glyph in _glyph_table.tsv, drawn as a 16 x 16 grid.
Edit this file, then run:   python tools\\glyph_import.py
(that writes your changes back into _glyph_table.tsv; then build as usual).

Each glyph is one block:

  ==== 0x24B ====          glyph id (hexadecimal)
  char: A                  what the glyph looks like (for reference only)
  en: A                    the character you type in the script to get this glyph
                           (leave empty if it is not used; type <space> for the space)
  note: CUSTOM: letter A   free text

  -----------------------------------------
  the picture: 16 rows, up to 16 characters wide
  -----------------------------------------

Picture characters:
  space    empty (transparent)   ("." also works)
  1 2 3    ink: 1 = full ink, 2 and 3 = lighter shades used to smooth edges
  4-9 A-F  other palette shades (only seen in some original Japanese glyphs)

  - The pixel grid is the full 16 x 16 cell. Where you draw it is where it appears:
    move the shape up/down to change its height on the line.
    English capitals start on row 4 (3 empty rows above) and are 11 rows tall.
  - Left/right position does not matter for dialogue: the game measures each glyph's
    inked columns and spaces letters automatically (variable width).
  - Glyphs 0x000-0x246 are the ORIGINAL game glyphs. Their pictures come from the ROM and
    are shown for reference; you can change their "en" / "note", but NOT redraw them
    (draw a new CUSTOM glyph instead).
  - CUSTOM glyphs start at 0x247 and must stay consecutive (no gaps). To add a letter,
    copy the last block, give it the next id, set "en", and draw it.
  - Highest usable id: 0x2FF.
"""


def read_rows():
    rows = []
    for l in list(open(TSV, encoding="utf-8"))[1:]:
        if not l.strip():
            continue
        c = (l.rstrip("\n").split("\t") + [""] * 6)[:6]
        rows.append(dict(zip(["id", "char", "en", "top", "pixels", "note"], c)))
    return rows


def custom_grid(r):
    grid = [["."] * SIZE for _ in range(SIZE)]
    top = int(r["top"] or 0)
    for dy, line in enumerate(r["pixels"].split("/") if r["pixels"] else []):
        for x, ch in enumerate(line):
            grid[top + dy][x] = ch
    return ["".join(g) for g in grid]


def original_grid(font, g):
    px = glyph_tiles(font[0x30 + g * 128: 0x30 + (g + 1) * 128])
    return ["".join(SHADES[v] for v in row) for row in px]


def main():
    if not FONT.exists():
        sys.exit(f"{FONT} not found - run python tools\\extract_rom.py first")
    font = FONT.read_bytes()
    out, sheet = [HEADER], []
    for r in read_rows():
        gid = int(r["id"], 16)
        grid = original_grid(font, gid) if gid < ORIG_GLYPHS else custom_grid(r)
        sheet.append((gid, r, grid))
        kind = "ORIGINAL" if gid < ORIG_GLYPHS else "CUSTOM"
        out.append(f"==== 0x{gid:03X} ==== ({kind})")
        out.append(f"char: {r['char']}")
        out.append(f"en: {r['en']}")
        out.append(f"note: {r['note']}")
        out += ["", SEP]
        out += [row.replace(".", " ").rstrip() for row in grid]
        out += ["", SEP, ""]
    TXT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {TXT} ({len(out)} lines)")
    draw_sheet(sheet)


def draw_sheet(glyphs):
    """Picture of every glyph (id, char and en labels) -> GLYPHS - PREVIEW.png."""
    from PIL import Image, ImageDraw, ImageFont

    def ttf(size):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", size)
        except OSError:
            return ImageFont.load_default()
    f_sm, f_hd = ttf(15), ttf(22)
    cols, cw, ch, top = 16, 64, 92, 120
    n = len(glyphs)
    img = Image.new("RGB", (cols * cw + 20, top + (n + cols - 1) // cols * ch + 20), "white")
    d = ImageDraw.Draw(img)
    last = glyphs[-1][0]
    d.text((10, 10), "Londonian Gothics - glyph table (GLYPHS - EDIT and IMPORT.txt / _glyph_table.tsv)", fill=0, font=f_hd)
    d.text((10, 44), f"{n} glyphs, 16x16 px. 0x000-0x{ORIG_GLYPHS - 1:03X} ORIGINAL Japanese font (grey); "
                     f"0x{ORIG_GLYPHS:03X}-0x{last:03X} CUSTOM (red).", fill=0, font=f_sm)
    d.text((10, 66), "Label under the id: the 'en' character you type in the script (blue), or the glyph's char if none (black).", fill=0, font=f_sm)
    d.text((10, 88), "Made by glyph_dump.py / glyph_import.py - do not edit; edit GLYPHS - EDIT and IMPORT.txt instead.", fill=0, font=f_sm)
    shade = {1: (0, 0, 0), 2: (110, 110, 110), 3: (190, 190, 190)}
    for k, (gid, r, grid) in enumerate(glyphs):
        x0, y0 = 10 + (k % cols) * cw, top + (k // cols) * ch
        new = gid >= ORIG_GLYPHS
        d.rectangle([x0, y0, x0 + cw - 2, y0 + ch - 2], outline=(220, 0, 0) if new else (200, 200, 200), width=2 if new else 1)
        gi = Image.new("RGB", (SIZE, SIZE), (245, 245, 235))
        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c != ".":
                    gi.putpixel((x, y), shade.get(SHADES.index(c) & 3 or 3, (0, 0, 0)))
        img.paste(gi.resize((48, 48), Image.NEAREST), (x0 + 7, y0 + 4))
        d.text((x0 + 4, y0 + 55), f"{gid:03X}", fill=(220, 0, 0) if new else (90, 90, 90), font=f_sm)
        if r["en"]:
            d.text((x0 + 4, y0 + 72), r["en"][:7], fill=(0, 70, 200), font=f_sm)
        else:
            d.text((x0 + 4, y0 + 72), r["char"][:7], fill=0, font=f_sm)
    img.save(PNG)
    print(f"wrote {PNG}")


if __name__ == "__main__":
    main()
