"""Import tools-resources/GLYPHS - EDIT and IMPORT.txt (made by glyph_dump.py) back into
tools-resources/_glyph_table.tsv. See the header of GLYPHS - EDIT and IMPORT.txt for the format.

Usage (from .WORK):  python tools\\glyph_import.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from glyph_dump import TSV, TXT, FONT, ORIG_GLYPHS, SIZE, SHADES, read_rows, original_grid, draw_sheet

MAX_ID = 0x2FF
HEAD = re.compile(r"^==== 0x([0-9A-Fa-f]+) ====")


def fail(msg):
    sys.exit(f"ERROR: {msg}")


def parse():
    lines = TXT.read_text(encoding="utf-8-sig").split("\n")
    blocks, i = [], 0
    while i < len(lines):
        m = HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        gid, ln = int(m.group(1), 16), i + 1
        body = lines[i + 1: i + 4]
        if len(body) < 3:
            fail(f"glyph 0x{gid:03X} (line {ln}): block is incomplete")
        fields = {}
        for k, l in zip(("char", "en", "note"), body[:3]):
            if not l.startswith(k + ":"):
                fail(f"glyph 0x{gid:03X} (line {ln}): expected '{k}:' line, found {l!r}")
            fields[k] = l[len(k) + 1:].removeprefix(" ")
        seps = [j for j in range(i + 4, min(len(lines), i + 4 + SIZE + 8)) if _is_sep(lines[j])][:2]
        if len(seps) < 2:
            fail(f"glyph 0x{gid:03X} (line {ln}): picture must be between two '-----' lines")
        grid = [l.rstrip().replace(" ", ".") for l in lines[seps[0] + 1: seps[1]]]
        while grid and not grid[-1].strip("."):
            grid.pop()          # blank lines before the closing ----- line
        if len(grid) > SIZE:
            fail(f"glyph 0x{gid:03X}: picture is taller than {SIZE} rows")
        for y, row in enumerate(grid):
            if len(row) > SIZE:
                fail(f"glyph 0x{gid:03X} picture row {y + 1}: wider than {SIZE} characters")
            bad = set(row.upper()) - set(SHADES)
            if bad:
                fail(f"glyph 0x{gid:03X} picture row {y + 1}: unknown character(s) {''.join(sorted(bad))!r} "
                     f"(use space or 1-9 / A-F)")
        grid = [row.upper().ljust(SIZE, ".") for row in grid] + ["." * SIZE] * (SIZE - len(grid))
        blocks.append((gid, fields, grid))
        i = seps[1] + 1
    return blocks


def _is_sep(line):
    s = line.strip()
    return len(s) >= 3 and set(s) == {"-"}


def compact(grid):
    """16x16 grid -> (top, pixels) in _glyph_table.tsv form."""
    ink = [y for y, row in enumerate(grid) if row.strip(".")]
    if not ink:
        return "0", ""
    width = max(len(row.rstrip(".")) for row in grid)
    return str(ink[0]), "/".join(row[:width] for row in grid[ink[0]: ink[-1] + 1])


def main():
    if not FONT.exists():
        sys.exit(f"{FONT} not found - run python tools\\extract_rom.py first")
    font = FONT.read_bytes()
    old = {int(r["id"], 16): r for r in read_rows()}
    blocks = parse()
    ids = [b[0] for b in blocks]
    if len(set(ids)) != len(ids):
        fail("duplicate glyph id(s): " + ", ".join(f"0x{g:03X}" for g in sorted({g for g in ids if ids.count(g) > 1})))
    if [g for g in sorted(ids) if g < ORIG_GLYPHS] != list(range(ORIG_GLYPHS)):
        fail("original glyphs 0x000-0x246 must all stay in the file")
    custom = sorted(g for g in ids if g >= ORIG_GLYPHS)
    if custom != list(range(ORIG_GLYPHS, ORIG_GLYPHS + len(custom))):
        fail("CUSTOM glyph ids must be consecutive from 0x247 (no gaps)")
    if custom and custom[-1] > MAX_ID:
        fail(f"glyph id 0x{custom[-1]:03X} is above the limit 0x{MAX_ID:03X}")

    rows, en_seen, changed = [], {}, 0
    for gid, f, grid in sorted(blocks):
        if f["en"]:
            key = " " if f["en"] == "<space>" else f["en"]
            if len(key) != 1:
                fail(f"glyph 0x{gid:03X}: 'en' must be one character (or <space>), found {f['en']!r}")
            if key in en_seen:
                fail(f"'en' character {f['en']!r} is used by both 0x{en_seen[key]:03X} and 0x{gid:03X}")
            en_seen[key] = gid
        if gid < ORIG_GLYPHS:
            if grid != original_grid(font, gid):
                fail(f"glyph 0x{gid:03X} is an ORIGINAL glyph and cannot be redrawn - "
                     f"add a CUSTOM glyph instead (or undo the picture change)")
            top, pixels = "", ""
        else:
            top, pixels = compact(grid)
        row = {"id": f"0x{gid:03X}", "char": f["char"], "en": f["en"], "top": top, "pixels": pixels, "note": f["note"]}
        o = old.get(gid)
        same_pic = o and (gid < ORIG_GLYPHS or compact(_grid_of(o)) == (top, pixels))
        if not (o and same_pic and all(o[k] == row[k] for k in ("char", "en", "note"))):
            changed += 1
            print(f"  changed 0x{gid:03X}  en={row['en']!r}")
        elif o:
            row["top"], row["pixels"] = o["top"], o["pixels"]   # keep the exact original text
        rows.append(row)
    for g in sorted(set(old) - set(ids)):
        changed += 1
        print(f"  removed 0x{g:03X}")
    hdr = open(TSV, encoding="utf-8").readline().rstrip("\n")
    TSV.write_text(hdr + "\n" + "".join(
        "\t".join(r[k] for k in ("id", "char", "en", "top", "pixels", "note")) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {TSV}: {len(rows)} glyphs, {changed} changed")
    draw_sheet([(gid, f, grid) for gid, f, grid in sorted(blocks)])


def _grid_of(r):
    from glyph_dump import custom_grid
    return custom_grid(r)


if __name__ == "__main__":
    main()
