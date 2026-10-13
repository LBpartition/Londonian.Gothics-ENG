"""Export tools-resources/glyph_table.tsv to tools-resources/GLYPHS - FULL.txt,
an easy-to-edit text file with every glyph drawn as a 16x16 grid of characters.

Original glyphs (0x000-0x246) are drawn from the game font (extracted/data/data/font.NCGR,
created by extract_rom.py). CUSTOM glyphs (0x247 onwards) are drawn from glyph_table.tsv.
Edit the text file, then run glyph_import.py to write the changes back into glyph_table.tsv.

Usage (from .WORK):  python tools\\glyph_dump.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from font_tools import glyph_tiles

W = Path(__file__).resolve().parents[1]
TSV = W / "tools-resources" / "glyph_table.tsv"
TXT = W / "tools-resources" / "GLYPHS - FULL.txt"
FONT = W / "extracted" / "data" / "data" / "font.NCGR"
ORIG_GLYPHS = 0x247
SIZE = 16
SHADES = ".123456789ABCDEF"

HEADER = """\
GLYPHS - FULL.txt
=================
Every glyph in glyph_table.tsv, drawn as a 16 x 16 grid.
Edit this file, then run:   python tools\\glyph_import.py
(that writes your changes back into glyph_table.tsv; then build as usual).

Each glyph is one block:

  ==== 0x24B ====          glyph id (hexadecimal)
  char: A                  what the glyph looks like (for reference only)
  en: A                    the character you type in the script to get this glyph
                           (leave empty if it is not used; type <space> for the space)
  note: CUSTOM: letter A   free text
  16 rows of 16 characters: the picture

Picture characters:
  .        empty (transparent)
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
    out = [HEADER]
    for r in read_rows():
        gid = int(r["id"], 16)
        grid = original_grid(font, gid) if gid < ORIG_GLYPHS else custom_grid(r)
        kind = "ORIGINAL" if gid < ORIG_GLYPHS else "CUSTOM"
        out.append(f"==== 0x{gid:03X} ==== ({kind})")
        out.append(f"char: {r['char']}")
        out.append(f"en: {r['en']}")
        out.append(f"note: {r['note']}")
        out += grid
        out.append("")
    TXT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {TXT} ({len(out)} lines)")


if __name__ == "__main__":
    main()
