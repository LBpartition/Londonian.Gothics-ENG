"""Font additions (appended after the original 583 glyphs; originals untouched)
and the English character -> glyph code map, both read from tools-resources/_glyph_table.tsv."""
import struct
from pathlib import Path
from font_tools import glyph_tiles, pack_glyph, build_table

ORIG_GLYPHS = 583
TSV = Path(__file__).resolve().parents[1] / "tools-resources" / "_glyph_table.tsv"
# _glyph_table.tsv: id, char, en (English character typed in _script_import.json -> this glyph),
# top + pixels (CUSTOM glyphs only: rows split by "/", "." = empty, 1-3 = palette shade)
ROWS = [dict(zip(["id", "char", "en", "top", "pixels", "note"], l.rstrip("\n").split("\t")))
        for l in list(open(TSV, encoding="utf-8"))[1:] if l.strip()]
for r in ROWS:
    r["id"] = int(r["id"], 16); r["en"] = " " if r["en"] == "<space>" else r["en"]
CUSTOM = [r for r in ROWS if r["id"] >= ORIG_GLYPHS]
assert [r["id"] for r in CUSTOM] == list(range(ORIG_GLYPHS, ORIG_GLYPHS + len(CUSTOM))), "custom ids must be consecutive from 0x247"
ASCII = {r["en"]: r["id"] for r in ROWS if r["en"]}
SPACE, APOS, COMMA, HYPHEN = ASCII[" "], ASCII["'"], ASCII[","], ASCII["-"]
NARROW0, ASTER, DIGIT0, AMP, QUES, EXCL = ASCII["A"], ASCII["*"], ASCII["0"], ASCII["&"], ASCII["?"], ASCII["!"]
NEW_GLYPHS = [r["id"] for r in CUSTOM]
TILE_OFF = 0x30


def _blank():
    return [[0] * 16 for _ in range(16)]


def _from_rows(rows, top):
    px = _blank()
    for dy, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".": px[top + dy][x] = int(ch)
    return px


def patch_font(font: bytes) -> bytes:
    d = bytearray(font)
    n = struct.unpack_from("<I", d, 0x28)[0] // 128
    assert n == ORIG_GLYPHS, n
    glyphs = [_from_rows(r["pixels"].split("/") if r["pixels"] else [], int(r["top"] or 0)) for r in CUSTOM]
    extra = b"".join(pack_glyph(g) for g in glyphs)
    d[TILE_OFF + n * 128: TILE_OFF + n * 128] = extra
    for off in (0x08, 0x14, 0x28):
        struct.pack_into("<I", d, off, struct.unpack_from("<I", d, off)[0] + len(extra))
    return bytes(d)


_T = build_table()


def enc_en(s, space_code=SPACE):
    """Encode English text (uppercased). Newline -> 0xFFFF. Unknown chars raise."""
    out = []
    for ch in s.upper():
        if ch == "\n": out.append(0xFFFF)
        elif ch == " ": out.append(space_code)
        elif ch in ASCII: out.append(ASCII[ch])
        else: raise KeyError(f"no glyph for {ch!r} in {s!r}")
    return out
