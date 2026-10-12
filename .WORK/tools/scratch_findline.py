import os, struct
# アリスお嬢さま！ using glyph indices read off the font sheet
seq = [0x51, 0x78, 0x5D, 0x05, 0x113, 0x0B, 0x1F, 0xA4]
pats = {
    "u16le": b"".join(struct.pack("<H", x) for x in seq),
    "u16be": b"".join(struct.pack(">H", x) for x in seq),
    "u16le_noexcl": b"".join(struct.pack("<H", x) for x in seq[:-1]),
}
for r, _, fs in os.walk("extracted"):
    for f in fs:
        p = os.path.join(r, f)
        d = open(p, "rb").read()
        for k, b in pats.items():
            i = d.find(b)
            while i >= 0:
                print(k, p, hex(i), d[max(0, i - 16):i + len(b) + 16].hex(" "))
                i = d.find(b, i + 1)
print("done")
