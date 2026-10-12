"""Translate the baked prompts in mode_save.NCGR (save/load slot 1 header).
JP "DATA1 にセーブします" / "DATA1 をロードします": tiles 22-30/38-46 (save), 102-110/118-126 (load)."""
import struct
from collections import Counter
from PIL import Image, ImageFont, ImageDraw
import intro_patch

FILE = "data/mode_save.NCGR"
PROMPTS = {"save": (22, 38, 21, 37, "SAVE ?"), "load": (102, 118, 101, 117, "LOAD ?")}
NT = 9
CENTER = 22  # px from tile 0 (screen x 96) -> midway between YES and NO


def _char(d):
    o = d.find(b"RAHC")
    size, = struct.unpack_from("<I", d, o + 4)
    return o + 0x20, struct.unpack_from("<I", d, o + 0x18)[0]


def tile(d, base, i):
    return bytearray(d[base + 64 * i: base + 64 * i + 64])


def patch(d, size=None):
    d = bytearray(d)
    base, _ = _char(d)
    font = ImageFont.truetype(r"C:\Windows\Fonts\georgiai.ttf", size or 10)
    for key, (t0, b0, tb, bb, txt) in PROMPTS.items():
        old = [tile(d, base, t0 + k) for k in range(NT)] + [tile(d, base, b0 + k) for k in range(NT)]
        bgt, bgb = tile(d, base, tb), tile(d, base, bb)
        bgpix = Counter(bgt + bgb)
        diff = Counter(b for t in old for b in t)
        for k, v in bgpix.items(): diff[k] -= v * NT
        ink = [k for k, v in diff.most_common() if v > 0]
        dat = Counter(b for k in range(1, 6) for b in tile(d, base, t0 - k) + tile(d, base, b0 - k))
        for k, v in bgpix.items(): dat[k] -= v * 5
        fg = dat.most_common(1)[0][0]
        img = Image.new("L", (NT * 8, 16), 0)
        dr = ImageDraw.Draw(img)
        w = font.getlength(txt)
        assert w <= NT * 8 - 2, (txt, w)
        dr.text((round(CENTER - w / 2), 2), txt, font=font, fill=255)
        for k in range(NT):
            for half, (ti, bg) in enumerate(((t0, bgt), (b0, bgb))):
                t = bytearray(bg)
                for y in range(8):
                    for x in range(8):
                        if img.getpixel((k * 8 + x, half * 8 + y)) > 70:
                            t[y * 8 + x] = fg
                o = base + 64 * (ti + k)
                d[o:o + 64] = t
    return bytes(d)