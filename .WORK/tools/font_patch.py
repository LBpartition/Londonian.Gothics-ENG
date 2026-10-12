"""Font additions (appended after the original 583 glyphs; originals untouched)
and the English character -> glyph code map."""
import struct
from test01_build import glyph_tiles, pack_glyph
from glyph_table import build as build_table
import narrow_font

ORIG_GLYPHS = 583
SPACE, APOS, COMMA, HYPHEN = 0x247, 0x248, 0x249, 0x24A
NARROW0 = 0x24B  # narrow A-Z at 0x24B..0x264
ASTER = NARROW0 + 26  # 0x265 narrow asterisk (guide uses *action*)
DIGIT0 = ASTER + 1  # 0x266..0x26F narrow 0-9
AMP = DIGIT0 + 10  # 0x270 narrow &
QUES, EXCL = AMP + 1, AMP + 2  # 0x271 ?, 0x272 !
NEW_GLYPHS = [SPACE, APOS, COMMA, HYPHEN] + list(range(NARROW0, NARROW0 + 26)) + [ASTER] + list(range(DIGIT0, DIGIT0 + 10)) + [AMP, QUES, EXCL]
TILE_OFF = 0x30


def _blank():
    return [[0] * 16 for _ in range(16)]


def _from_rows(rows, top):
    px = _blank()
    for dy, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".": px[top + dy][x] = int(ch)
    return px


def _apostrophe(font):
    q = glyph_tiles(font[TILE_OFF + 0xB0 * 128: TILE_OFF + 0xB1 * 128])
    cols = [x for x in range(16) if any(q[y][x] for y in range(16))]
    mid = (min(cols) + max(cols)) // 2
    return [[q[y][x] if x <= mid else 0 for x in range(16)] for y in range(16)]


def patch_font(font: bytes) -> bytes:
    d = bytearray(font)
    n = struct.unpack_from("<I", d, 0x28)[0] // 128
    assert n == ORIG_GLYPHS, n
    glyphs = [
        _blank(),                                   # space
        _apostrophe(d),                             # '
        _from_rows(["....21", "....12", "...2.."], 13),   # ,  (period + tail)
        _from_rows(["..1111", "..3333"], 8),        # -  (mid cap height)
    ] + [_from_rows(narrow_font.N[c], 3) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] + [
        _from_rows(["..1..", "1.1.1", ".111.", "1.1.1", "..1.."], 3)] + [  # *
        _from_rows(narrow_font.D[c], 3) for c in "0123456789&?!"]
    extra = b"".join(pack_glyph(g) for g in glyphs)
    d[TILE_OFF + n * 128: TILE_OFF + n * 128] = extra
    for off in (0x08, 0x14, 0x28):
        struct.pack_into("<I", d, off, struct.unpack_from("<I", d, off)[0] + len(extra))
    return bytes(d)


_T = build_table()
_J = {v: k for k, v in _T.items() if len(v) == 1}
ASCII = {
    " ": SPACE, "'": APOS, ",": COMMA, "-": HYPHEN,
    ".": 0xAD, "!": EXCL, "?": QUES, "(": 0xA6, ")": 0xA7, ";": 0xAB, ":": 0xAC,
    '"': 0xB0, "#": 0xB1, "%": 0xB2, "&": AMP, "<": 0xBA, ">": 0xBB, "/": 0x23E,
    "\u2026": 0xEE, "\u00a3": 0xAF, "_": 0xB9, "*": ASTER,
}
for i, c in enumerate("0123456789"):
    ASCII[c] = DIGIT0 + i
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    ASCII[c] = NARROW0 + i


def enc_en(s, space_code=SPACE):
    """Encode English text (uppercased). Newline -> 0xFFFF. Unknown chars raise."""
    out = []
    for ch in s.upper():
        if ch == "\n": out.append(0xFFFF)
        elif ch == " ": out.append(space_code)
        elif ch in ASCII: out.append(ASCII[ch])
        else: raise KeyError(f"no glyph for {ch!r} in {s!r}")
    return out
