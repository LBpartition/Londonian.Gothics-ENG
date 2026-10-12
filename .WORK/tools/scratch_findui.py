import os, struct, sys
targets = {
    "メッセージスピード": [0x72, 0x87, 0x5E, 0xA1, 0x8E, 0x5D, 0x9D, 0xA1, 0x96],
    "バックライト": [0x97, 0x87, 0x58, 0x77, 0x52, 0x64],
    "ヒステュール": [0x6B, 0x5D, 0x63, 0x85, 0xA1, 0x79],
    "電撃を撃って": [0x192, 0x193, 0x2D, 0x193, 0x37, 0x13],
    "OPTION": [0xE2, 0xE3, 0xE7, 0xDC, 0xE2, 0xE1],
    "BGM": [0xD5, 0xDA, 0xE0],
    "BACK": [0xD5, 0xD4, 0xD6, 0xDE],
}
files = []
for r, _, fs in os.walk("extracted"):
    for f in fs:
        files.append(os.path.join(r, f))
data = {p: open(p, "rb").read() for p in files}
for name, seq in targets.items():
    pats = {"u16le": b"".join(struct.pack("<H", x) for x in seq)}
    if max(seq) < 256:
        pats["u8"] = bytes(seq)
    found = False
    for k, b in pats.items():
        for p, d in data.items():
            i = d.find(b)
            while i >= 0:
                found = True
                print(f"{name} {k} {p} {hex(i)}")
                i = d.find(b, i + 1)
    if not found:
        print(f"{name}: NOT FOUND")
