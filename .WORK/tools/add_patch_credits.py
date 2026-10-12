"""Credits text on the title screen's bottom screen (engine B, OBJ only there).

Hooked at the end of the title loader (0x020227E8 `mov r0,#1`): copies 4bpp tiles to
engine-B BG VRAM 0x06204000 (char base 1, free), map rows to screen base 31 (0x0620F800,
free), a 16-colour palette to BG palette 15, sets BG3CNT_B and enables BG3 in DISPCNT_B.
BG3 is unused by the intro (which uses BG0-2), so its layer settings are not disturbed.
"""
import re, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import intro_patch

ROOT = Path(__file__).resolve().parents[2]
LINES = None          # set by full_build: list of 4 strings
TOP_ROW, PITCH = 16, 16  # tile row 16 = y 128 (lower half, over the dark emblem)


def shares():
    """% of translated text entries by source (dialogue lines, names, descriptions, locations,
    intro paragraphs, character names, menu labels); everything but MTL dialogue is ShadowRisae."""
    import master
    E = master.EN
    m = sum(1 for e in E["dialogue"] if e["source"] == "mtl")
    g = (sum(1 for e in E["dialogue"] if e["source"] == "shadowrisae") + len(E["intro"])
         + sum((e["name"] is not None) + (e["desc"] is not None) for e in E["dresses"] + E["items"])
         + len({e["en"] for e in E["locations"]}) + 7 + len(E["menu"]))
    return 100 * g / (g + m), 100 * m / (g + m)


def default_lines(rc):
    g, m = shares()
    return [f"ENG-RC{rc}", f"{round(g)}% Human translation by ShadowRisae",
            f"{round(m)}% Machine translation", "Patch by LBpartition"]


def render(lines):
    font = ImageFont.truetype(intro_patch.FONT, intro_patch.SIZE)
    h = PITCH * len(lines)
    img = Image.new("L", (256, h), 0)
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        w = font.getlength(l)
        assert w <= 248, (l, w)
        d.text(((256 - w) / 2, i * PITCH + 1), l, font=font, fill=255)
    tiles, idx, rows = [bytes(32)], {bytes(32): 0}, []
    for ty in range(h // 8):
        row = []
        for tx in range(32):
            b = bytearray()
            for y in range(8):
                for x in range(0, 8, 2):
                    p = [round(img.getpixel((tx * 8 + x + k, ty * 8 + y)) * 15 / 255) for k in (0, 1)]
                    b.append(p[0] | p[1] << 4)
            b = bytes(b)
            if b not in idx:
                idx[b] = len(tiles); tiles.append(b)
            row.append(0xF000 | idx[b])
        rows.append(row)
    pal = [0]
    for k in range(1, 16):
        r, g, b = (c * k // 15 >> 3 for c in intro_patch.LIGHT)
        pal.append(r | g << 5 | b << 10)
    tdata = b"".join(tiles)
    mdata = b"".join(struct.pack("<32H", *r) for r in rows)
    return tdata, mdata, struct.pack("<16H", *pal), img


def bl(src, dst):
    return 0xEB000000 | (((dst - (src + 8)) >> 2) & 0xFFFFFF)


def blob(addr, lines=None, call=None):
    tdata, mdata, pdata, _ = render(lines or LINES)
    m = struct.unpack(f"<{len(mdata)//2}H", mdata)                  # tiles live at index 256+ (0x06202000)
    mdata = struct.pack("<H", 256) * (32 * TOP_ROW) + struct.pack(f"<{len(m)}H", *[v + 256 for v in m])   # blank rows above
    code_n = 26
    lit = addr + code_n * 4
    lits = []

    def L(v):
        if v not in lits: lits.append(v)
        return lits.index(v)

    seq = []  # (kind, args)
    seq += [("raw", 0xE92D4010)]                                     # push {r4,lr}
    if call:
        seq += [("bl_abs", call), ("raw", 0xE1A04000)]                  # original call; mov r4, r0
    copies = [("t", 0x06202000, len(tdata)), ("m", 0x06201800, len(mdata)),
              ("p", 0x050005E0, len(pdata))]
    for key, dst, n in copies:
        seq += [("ldr", 0, ("src", key)), ("ldr", 1, dst), ("ldr", 2, n), ("bl_copy",)]
    seq += [("ldr", 0, 0x0400106C), ("raw", 0xE3A01000), ("raw", 0xE1C010B0)]   # MASTER_BRIGHT_B = 0 (menu blacks out bottom)
    seq += [("ldr", 0, 0x04001008), ("ldr", 1, 0x0300), ("raw", 0xE1C010B0),   # strh r1,[r0] BG0CNT_B (prio 0)
            ("raw", 0xE3A01000), ("ldr", 0, 0x04001010), ("raw", 0xE5801000),  # BG0 H/VOFS = 0
            ("ldr", 0, 0x04001000), ("raw", 0xE5901000), ("raw", 0xE3C11C1F), ("raw", 0xE3811C01), ("raw", 0xE5801000),  # DISPCNT_B |= BG0
            ("raw", 0xE1A00004 if call else 0xE3A00001), ("raw", 0xE8BD8010)]   # r0 = r4 / #1; pop {r4,pc}
    copy_fn = [0xE4903004, 0xE4813004, 0xE2522004, 0xCAFFFFFB, 0xE12FFF1E]
    n_main = len(seq)
    copy_addr = addr + 4 * n_main
    lit = copy_addr + 4 * len(copy_fn)
    # resolve sources after literal pool is sized
    keys = [s for s in seq if s[0] == "ldr"]
    vals = []
    for s in keys:
        v = s[2]
        if v not in vals: vals.append(v)
    data_addr = lit + 4 * len(vals)
    src = {"t": data_addr}
    src["m"] = src["t"] + len(tdata); src["p"] = src["m"] + len(mdata)
    pool = [src[v[1]] if isinstance(v, tuple) else v for v in vals]
    out = []
    for i, s in enumerate(seq):
        a = addr + 4 * i
        if s[0] == "raw": out.append(s[1])
        elif s[0] == "bl_copy": out.append(bl(a, copy_addr))
        elif s[0] == "bl_abs": out.append(bl(a, s[1]))
        else:
            la = lit + 4 * vals.index(s[2])
            out.append(0xE59F0000 | s[1] << 12 | (la - (a + 8)))
    out += copy_fn + pool
    return struct.pack(f"<{len(out)}I", *out) + tdata + mdata + pdata


if __name__ == "__main__":
    import sys
    l = default_lines(sys.argv[1] if len(sys.argv) > 1 else 1)
    t, m, p, img = render(l)
    print(l, "tiles", len(t) // 32, "blob", len(blob(0x01FFC000, l)))
    img.save(ROOT / ".WORK" / "tmp_add_patch_credits.png")
