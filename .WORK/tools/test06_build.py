import os
"""TEST06: narrow A-Z, gap 1/space 4, UI line step 12, DRESS MODE names+descriptions
from the GameFAQs guide (ShadowRisae), tables repointed into ITCM.
Descriptions that fail the fit gate are left in Japanese and listed."""
import re, struct, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, vwf_patch, textfit, font_patch
import test01_build as t1
import layout

W = Path(__file__).resolve().parent.parent
GAP, SPACE, STEP = 1, 4, 14
DIALOGUE_VWF = False  # set by later builds (test07+)
ITEMS = False         # set by full_build
TITLE = False         # set by full_build (title bottom-screen credits)
ITEM_DESC_STRIDE = 0x80
# ids 1-30 in arm9 order == guide lines 303-332 (romanized names match the JP katakana)
ITEM_ORDER = ["awizu", "akubaru", "rewiza", "dareifu", "wariyagu", "roadesu", "tyuunu", "rudorin",
              "gurasuto", "irumari", "kuahha", "lisufa", "borodi", "fomoru", "tuuka", "aigizu",
              "osubiya", "nyukusu", "zoriano", "reshiefu", "seitse", "masaeru", "oreusu", "yeun",
              "seruti", "sarissa", "eushu", "maanesu", "tareosu", "radokuya"]
ITEM_EXTRA_NAMES = {31: "Holy Sword", 32: "Bible", 33: "Holy Water"}   # 31: guide "holy sword" (was MTL "Bergen"); guide 1758 "-Bible"; 1702 "Obtained holy water"
# guide 1758 (Bible shop text); JP descs of 32/33 are identical apart from "part 1"/"part 2"
ITEM_EXTRA_DESCS = {31: "A holy sword-shaped accessory.",   # user-approved
                    32: "One of the items necessary for rescuing the professor.",
                    33: "One of the items necessary for rescuing the professor."}


def guide_items():
    L = (W / "ref_guide.txt").read_text(encoding="utf-8").split("\n")
    out = {}
    for ln in L[295:340]:
        mm = re.match(r"^-(\w+)\s*: (.*?)(?:\s*\([^)]*\))?\s*$", ln)
        if mm: out[mm.group(1)] = mm.group(2).strip()
    return out


def item_tables(arm9, m):
    g = guide_items(); assert set(ITEM_ORDER) <= set(g), set(ITEM_ORDER) - set(g)
    names, descs, rej = b"", b"", []
    for i in range(34):
        o = 0x48144 + 10 * i
        jn = list(struct.unpack("<5H", arm9[o:o + 10])); jn = jn[:jn.index(0)] if 0 in jn else jn
        o = 0x486E0 + 0x2E * i
        jd = list(struct.unpack("<23H", arm9[o:o + 0x2E])); jd = jd[:jd.index(0)] if 0 in jd else jd
        un, ud = jn, jd
        en = ITEM_ORDER[i].capitalize() if i < 30 else ITEM_EXTRA_NAMES.get(i + 1)
        if en:
            un = textfit.fit(en, textfit.DRESS_NAME_N, m)
        dtxt = item_desc(i, g)
        if dtxt:
            try:
                ud = textfit.fit(dtxt, textfit.DRESS_DESC_N, m)
            except textfit.FitError as e:
                rej.append((f"item {i+1}", str(e)))
        assert len(un) < NAME_STRIDE // 2 and len(ud) < ITEM_DESC_STRIDE // 2
        names += struct.pack(f"<{NAME_STRIDE//2}H", *(un + [0] * (NAME_STRIDE // 2 - len(un))))
        descs += struct.pack(f"<{ITEM_DESC_STRIDE//2}H", *(ud + [0] * (ITEM_DESC_STRIDE // 2 - len(ud))))
    return names, descs, rej


ORDER = ["Hystulle", "Tranquille", "Stradia", "Domudia", "Riffcowl", "Dewlit", "Ferminio",
         "Blizzariel", "Proteus", "Cannelle", "Twincavia", "Survey", "Manaclis", "Epinephre",
         "Litense", "Iscarpe", "Argus", "Satiend", "Shrake", "Scuart", "Torpedone", "Bekiradin"]
NAME_STRIDE, DESC_STRIDE = 0x18, 0x100
# Guide text with words removed only (no new wording) so it fits 3 lines.
TRIM = {
    "Scuart": "Knock back enemy a random distance in a straight line via bazooka.",
    "Dewlit": "Knock back enemy a random distance over walls via bazooka.",
    "Litense": "Jump over 1 square of distance.",
    "Iscarpe": "Auto-warp somewhere on map upon enemy touch instead of dying. Drains all DP.",
}


def guide_dresses():
    L = (W / "ref_guide.txt").read_text(encoding="utf-8").split("\n")[233:264]
    it = re.findall(r'^\d\d\. (\w+)\s*: (.*?)(?=\n\s*\n|\n\d\d\.|\Z)', "\n".join(L), re.S | re.M)
    return {n: " ".join(d.split()) for n, d in it}


def dress_desc(n, g):
    return layout.OV["dress"].get(n) or TRIM.get(n, g[n])


def item_name(i):
    return ITEM_ORDER[i].capitalize() if i < 30 else ITEM_EXTRA_NAMES.get(i + 1)


def item_desc(i, g):
    nm = item_name(i)
    return layout.OV["item"].get(nm) or (g[ITEM_ORDER[i]] if i < 30 else ITEM_EXTRA_DESCS.get(i + 1))


def main(out_dir, diag=False):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rom = t1.ORIG.read_bytes()
    fid = ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]
    font = font_patch.patch_font(ndsbuild.get_file(rom, fid))
    m = textfit.Metrics(font, GAP, SPACE)
    arm9 = bytearray((W / "extracted" / "arm9.bin").read_bytes())
    g = guide_dresses(); assert sorted(g) == sorted(ORDER), set(g) ^ set(ORDER)

    names, descs, rejected = b"", b"", []
    for k, n in enumerate(ORDER):
        u = textfit.fit(n, textfit.DRESS_NAME_N, m)
        assert len(u) < NAME_STRIDE // 2
        names += struct.pack(f"<{NAME_STRIDE//2}H", *(u + [0] * (NAME_STRIDE // 2 - len(u))))
        try:
            u = textfit.fit(dress_desc(n, g), textfit.DRESS_DESC_N, m)
        except textfit.FitError as e:
            rejected.append((n, str(e)))
            o = 0x48290 + 0x30 * k
            u = list(struct.unpack("<24H", arm9[o:o + 48]))
            u = u[:u.index(0)] if 0 in u else u
        assert len(u) < DESC_STRIDE // 2, (n, len(u))
        descs += struct.pack(f"<{DESC_STRIDE//2}H", *(u + [0] * (DESC_STRIDE // 2 - len(u))))

    # k=22: locked-dress entry ("?" name + its description); not in the guide -> keep original
    o = 0x48000 + 14 * 22
    names += arm9[o:o + 14] + bytes(NAME_STRIDE - 14)
    o = 0x48290 + 48 * 22
    descs += arm9[o:o + 48] + bytes(DESC_STRIDE - 48)

    base = vwf_patch.extra_addr(bytes(arm9))
    name_addr, desc_addr = base, base + len(names)
    if ITEMS:
        inames, idescs, irej = item_tables(arm9, m)
        rejected += irej
        iname_addr = desc_addr + len(descs)
        idesc_addr = iname_addr + len(inames)
        assert struct.unpack_from("<I", arm9, 0x2E450)[0] == 0xB3A0000A
        struct.pack_into("<I", arm9, 0x2E450, 0xB3A00000 | NAME_STRIDE)
        struct.pack_into("<I", arm9, 0x2E478, iname_addr)
        assert struct.unpack_from("<I", arm9, 0x2E408)[0] == 0xB3A0002E
        struct.pack_into("<I", arm9, 0x2E408, 0xB3A00000 | ITEM_DESC_STRIDE)
        struct.pack_into("<I", arm9, 0x2E430, idesc_addr)
        descs += inames + idescs
    if TITLE:
        import title_text
        blob = title_text.blob(desc_addr + len(descs))
        assert struct.unpack_from("<I", arm9, 0x385E8)[0] == 0xE3A00001   # mov r0,#1: main-menu phase end, after bottom brightness set to -16
        struct.pack_into("<I", arm9, 0x385E8, title_text.bl(0x020385E8, desc_addr + len(descs)))
        descs += blob
    # In-game Dress/Item description buffer (0x02058078) is only 0x50 bytes and is followed by
    # the game-state pointer 0x020580C8; long English descriptions overwrote it (freeze on close).
    # Relocate it to a 256-byte buffer in the ITCM extra area.
    descs += bytes(-(desc_addr + len(descs)) % 4)
    dbuf = desc_addr + len(descs)
    descs += bytes(256)
    for o in (0x2DFE0, 0x2E040):
        assert struct.unpack_from("<I", arm9, o)[0] == 0x02058078
        struct.pack_into("<I", arm9, o, dbuf)
    # In-game Dress/Item description pen y 141 -> 138 (3px up; too close to box bottom)
    assert struct.unpack_from("<I", arm9, 0x2DF10)[0] == 0xE3A0308D
    struct.pack_into("<I", arm9, 0x2DF10, 0xE3A0308A)
    print(f"ITCM extra end {name_addr + len(names) + len(descs):#x}")
    assert name_addr + len(names) + len(descs) < 0x02000000, "extra tables overflow ITCM"
    # OPTION screen: guide line 83/85 "Text Speed", "Backlight"; original full-width caps
    # (A=0xD4.., like BGM/SE/BACK), FFFE = space; fixed 24-byte slots.
    for off, txt in ((0x4C420, "SFX"), (0x4C438, "TEXT SPEED"), (0x4C450, "BACKLIGHT")):
        u = [0xFFFE if c == " " else 0xD4 + ord(c) - 65 for c in txt]
        assert len(u) < 12
        struct.pack_into("<12H", arm9, off, *(u + [0] * (12 - len(u))))
    # Yes/No prompts (save/load/shop etc.): 8-byte slots, full-width caps
    fw = lambda t: [0xD4 + ord(c) - 65 for c in t]
    yn = {(0x1A, 0x02, 0, 0): "YES", (0x02, 0x02, 0x04, 0): "NO", (0x24, 0x22, 0x29, 0): "END"}
    for off in range(0x4B000, 0x4C800, 8):
        t = yn.get(struct.unpack_from("<4H", arm9, off))
        if t and struct.unpack_from("<H", arm9, off - 2)[0] in (0, 0xFF):
            u = fw(t)
            struct.pack_into("<4H", arm9, off, *(u + [0] * (4 - len(u))))
    # Save/Load YES/NO: NO x 0x70 -> 0x7C (English YES is wider than hai)
    for o, w in ((0x3E7E0, 0xE3A05070), (0x37510, 0xE3A02070), (0x37554, 0xE3A02070),
                 (0x37660, 0xE3A02070), (0x376A0, 0xE3A02070),
                 (0x373D8, 0xE3A02070), (0x37418, 0xE3A02070)):
        assert struct.unpack_from("<I", arm9, o)[0] == w, hex(o)
        struct.pack_into("<I", arm9, o, (w & ~0xFF) | 0x7C)
    for o in (0x37520, 0x37560):   # "mov r3, r2" (y = x) -> mov r3, #0x70
        assert struct.unpack_from("<I", arm9, o)[0] == 0xE1A03002
        struct.pack_into("<I", arm9, o, 0xE3A03070)
    assert struct.unpack_from("<8H", arm9, 0x4BF68) == (0x5E, 0xA1, 0x99, 0x0C, 0x1F, 0x0C, 0x10, 0)
    u = fw("SAVED"); struct.pack_into("<8H", arm9, 0x4BF68, *(u + [0] * (8 - len(u))))
    # repoint dress tables (getName / getDesc ids 0x23..0x3A)
    struct.pack_into("<I", arm9, 0x2E47C, name_addr)
    assert struct.unpack_from("<I", arm9, 0x2E468)[0] == 0xB3A0000E
    struct.pack_into("<I", arm9, 0x2E468, 0xB3A00000 | NAME_STRIDE)
    struct.pack_into("<I", arm9, 0x2E434, desc_addr)
    assert struct.unpack_from("<I", arm9, 0x2E420)[0] == 0xB3A00030
    struct.pack_into("<I", arm9, 0x2E420, 0xB3A00C01)          # mov r0, #0x100
    # UI renderer line step 18 -> 12
    for s in (0x29FF8, 0x2A23C):
        assert struct.unpack_from("<I", arm9, s)[0] == 0xE2888012
        struct.pack_into("<I", arm9, s, 0xE2888000 | STEP)
    # DRESS MODE description pen (0x32,0x90) -> (44,141)
    assert struct.unpack_from("<II", arm9, 0x3F6A0) == (0xE3A02032, 0xE3A03090)
    struct.pack_into("<II", arm9, 0x3F6A0, 0xE3A02000 | 44, 0xE3A03000 | 138)

    # DRESS MODE bottom-screen text context: 80 -> 128 sprites (OAM 67..127 unused, measured)
    assert struct.unpack_from("<I", arm9, 0x3FC24)[0] == 0xE3A02050
    struct.pack_into("<I", arm9, 0x3FC24, 0xE3A02080)
    if diag:
        # DIAGNOSTIC ONLY: show all list names regardless of unlock state
        assert struct.unpack_from("<I", arm9, 0x3F570)[0] >> 24 == 0x1A
        struct.pack_into("<I", arm9, 0x3F570, 0xE1A00000)
        for s in (0x3F678, 0x3F67C, 0x3F680):  # description unlock check
            struct.pack_into("<I", arm9, s, 0xE1A00000)

    arm9 = vwf_patch.apply(bytes(arm9), font, gap=GAP, space=SPACE, extra=names + descs, dialogue=DIALOGUE_VWF)
    out = ndsbuild.build(rom, {fid: font}, arm9=arm9, log=lambda *_: None)
    p = out_dir / ("DIAG06-AllNamesShown.nds" if diag else "TEST06-NarrowFont-DressMode.nds")
    p.write_bytes(out)
    print(p, hashlib.sha256(out).hexdigest().upper())
    print("fit-gate rejected (left Japanese):")
    for n, e in rejected: print("  ", n, "|", e)


if __name__ == "__main__":
    main(sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "diag")
