import os
"""TEST06: narrow A-Z, gap 1/space 4, UI line step 12, DRESS MODE names+descriptions
from tools-resources/_import_script.json, tables repointed into ITCM.
Descriptions that fail the fit gate are left in Japanese and listed."""
import re, struct, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, vwf_patch, textfit, font_patch
import font_tools as t1
import master

W = Path(__file__).resolve().parent.parent
GAP, SPACE, STEP = 1, 4, 14
DIALOGUE_VWF = False  # set by later builds (test07+)
ITEMS = False         # set by full_build
TITLE = False         # set by full_build (title bottom-screen credits)
ITEM_DESC_STRIDE = 0x80
def item_tables(arm9, m):
    g = None
    names, descs, rej = b"", b"", []
    for i in range(34):
        o = 0x48144 + 10 * i
        jn = list(struct.unpack("<5H", arm9[o:o + 10])); jn = jn[:jn.index(0)] if 0 in jn else jn
        o = 0x486E0 + 0x2E * i
        jd = list(struct.unpack("<23H", arm9[o:o + 0x2E])); jd = jd[:jd.index(0)] if 0 in jd else jd
        un, ud = jn, jd
        en = item_name(i)
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


ORDER = [e["name"] for e in master.EN["dresses"]]   # dress ids 1-22 (arm9 order)
NAME_STRIDE, DESC_STRIDE = 0x18, 0x100
_D = {e["name"]: e for e in master.EN["dresses"]}
_I = {e["id"]: e for e in master.EN["items"]}


def dress_desc(n, g=None):
    return master.join(_D[n]["desc"])


def item_name(i):
    return _I[i + 1]["name"]


def item_desc(i, g=None):
    d = _I[i + 1]["desc"]
    return master.join(d) if d else None


def main(out_dir, diag=False):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rom = t1.ORIG.read_bytes()
    fid = ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]
    font = font_patch.patch_font(ndsbuild.get_file(rom, fid))
    m = textfit.Metrics(font, GAP, SPACE)
    arm9 = bytearray((W / "extracted" / "arm9.bin").read_bytes())
    g = None

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
        import add_patch_credits
        blob = add_patch_credits.blob(desc_addr + len(descs))
        assert struct.unpack_from("<I", arm9, 0x385E8)[0] == 0xE3A00001   # mov r0,#1: main-menu phase end, after bottom brightness set to -16
        struct.pack_into("<I", arm9, 0x385E8, add_patch_credits.bl(0x020385E8, desc_addr + len(descs)))
        descs += blob
    # In-game Dress/Item description buffer (0x02058078) is only 0x50 bytes and is followed by
    # the game-state pointer 0x020580C8; long English descriptions overwrote it (freeze on close).
    # Relocate it to a 256-byte buffer in the ITCM extra area.
    descs += bytes(-(desc_addr + len(descs)) % 4)
    dbuf = desc_addr + len(descs)
    descs += bytes(256)
    # arm9 system messages (master.SYSMSG): store English in ITCM extra and repoint every literal.
    # Explicit lines only; {ITEM} (0xFD00) is measured as the widest item/dress name.
    if DIALOGUE_VWF:
        bx = textfit.Box("system", 190, 3, 0xFFFE)
        nms = [e["name"] for e in master.EN["items"] + master.EN["dresses"] if e["name"]]
        widest = max(nms, key=lambda n: m.width(n, bx))
        for key, offs in master.SYSMSG.items():
            lines = master.MENU[key].split("\n")
            jl = struct.unpack_from("<64H", arm9, offs[0]); jl = jl[:jl.index(0)]
            assert len(lines) <= max(2, jl.count(0xFFFF) + 1), (key, "too many lines")
            u = []
            for i, ln in enumerate(lines):
                w = m.width(ln.replace("{ITEM}", widest), bx)
                assert w <= bx.max_px, (key, ln, w)
                if i: u.append(0xFFFF)
                for j, part in enumerate(ln.split("{ITEM}")):
                    if j: u.append(0xFD00)
                    u += m.codes(part, bx)
            addr = desc_addr + len(descs)
            descs += struct.pack(f"<{len(u) + 1}H", *u, 0)
            descs += bytes(-(desc_addr + len(descs)) % 4)
            for o in offs:
                refs = [j for j in range(0, 0x4B000, 4) if struct.unpack_from("<I", arm9, j)[0] == 0x02000000 + o]
                assert refs, (key, hex(o))
                for j in refs: struct.pack_into("<I", arm9, j, addr)
    for o in (0x2DFE0, 0x2E040):
        assert struct.unpack_from("<I", arm9, o)[0] == 0x02058078
        struct.pack_into("<I", arm9, o, dbuf)
    # In-game Dress/Item description pen y 141 -> 138 (3px up; too close to box bottom)
    assert struct.unpack_from("<I", arm9, 0x2DF10)[0] == 0xE3A0308D
    struct.pack_into("<I", arm9, 0x2DF10, 0xE3A0308A)
    print(f"ITCM extra end {name_addr + len(names) + len(descs):#x}")
    assert name_addr + len(names) + len(descs) < 0x02000000, "extra tables overflow ITCM"
    # OPTION screen + YES/NO/END/SAVED: A-Z and 0-9 use the original full-width glyphs (0xD4.., 0xC0..),
    # FFFE = space; any other character uses its _import_glyph_table.tsv glyph.
    def fw(t):
        return [0xFFFE if c == " " else 0xD4 + ord(c) - 65 if "A" <= c <= "Z" else 0xC0 + ord(c) - 48 if "0" <= c <= "9" else 0xB9 if c == "_"
                else font_patch.ASCII[c] for c in t.upper()]
    # OPTION table: 15 fixed 24-byte slots from 0x4C3F0 (max 11 characters each)
    for i, k in enumerate(master.OPTION_KEYS):
        txt = master.MENU[k]
        u = fw(txt)
        assert len(u) < 12, txt
        struct.pack_into("<12H", arm9, 0x4C3F0 + 24 * i, *(u + [0] * (12 - len(u))))
    # save-memory test text (likely unused debug screen): two identical 11-slot tables
    for base in (0x4B6C8, 0x4C038):
        for i, k in enumerate(master.DEBUG_KEYS):
            u = fw(master.MENU[k])
            assert len(u) < 12, master.MENU[k]
            struct.pack_into("<12H", arm9, base + 24 * i, *(u + [0] * (12 - len(u))))
    # Yes/No prompts (save/load/shop etc.): 8-byte slots (max 4 characters)
    yn = {(0x1A, 0x02, 0, 0): master.MENU["yes"], (0x02, 0x02, 0x04, 0): master.MENU["no"], (0x24, 0x22, 0x29, 0): master.MENU["end"]}
    for off in range(0x4B000, 0x4C800, 8):
        t = yn.get(struct.unpack_from("<4H", arm9, off))
        if t and struct.unpack_from("<H", arm9, off - 2)[0] in (0, 0xFF):
            u = fw(t)
            assert len(u) <= 4, t
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
    u = fw(master.MENU["saved"]); assert len(u) <= 8, master.MENU["saved"]; struct.pack_into("<8H", arm9, 0x4BF68, *(u + [0] * (8 - len(u))))
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
