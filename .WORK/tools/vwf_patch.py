"""Variable-width font (VWF) patch for the UI text renderers in arm9.

The two UI draw functions (0x02029F78 and 0x0202A1C4) draw each glyph as a 16x16
sprite and advance the pen by a fixed 14 px. This patch:
  * replaces `mov r1, r7` (sprite x = pen) with `bl vwf_x` (x = pen - left_margin[glyph])
  * replaces `add r7, r7, #14` (advance) with `bl vwf_adv` (pen += advance[glyph])
  * sets the built-in space code 0xFFFE advance to SPACE px
Hook code and the two byte tables live in an enlarged ITCM autoload section.
Only English glyphs get proportional metrics; kana/kanji keep left=0, adv=14.
"""
import font_patch
import struct
import keystone

ITCM_BASE = 0x01FF8000
RAM_BASE = 0x02000000
MODPARAMS = 0xB00
TABLE_N = 0x300  # encodable immediate, covers all 0x249 glyphs

SITES_X = (0x2A0E0, 0x2A324)
SITES_ADV = (0x2A104, 0x2A348)
SITES_SPACE = (0x29FEC, 0x2A230)

# glyph ids that get proportional metrics
ENGLISH = (
    list(range(0xC0, 0xCA))      # digits
    + list(range(0xCA, 0xD4))    # italic digits
    + list(range(0xD4, 0xEE))    # A-Z
    + [0xA4, 0xA5, 0xA6, 0xA7, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB2, 0xB3,
       0xBA, 0xBB, 0xEE, 0xA2, 0x23E, 0x248, 0x249, 0x24A]
    + [g for g in font_patch.NEW_GLYPHS if g > 0x24A]   # custom glyphs (_import_glyph_table.tsv)
)
BLANK_GLYPH = 0x247
PAD = {font_patch.EXCL: 1}   # extra px each side (narrow "!" is 1px wide)
TABULAR = [list(range(0xC0, 0xCA)), list(range(0xCA, 0xD4)), [0xBA, 0xBB]]


def glyph_cols(font, g):
    tile_off = 0x30
    data = font[tile_off + g * 128: tile_off + (g + 1) * 128]
    cols = set()
    for t in range(4):
        tx = (t % 2) * 8
        for i, b in enumerate(data[t * 32:(t + 1) * 32]):
            x = tx + (i % 4) * 2
            if b & 0xF: cols.add(x)
            if b >> 4: cols.add(x + 1)
    return cols


def metrics(font, gap, space):
    left = bytearray(TABLE_N)
    adv = bytearray([14]) * TABLE_N
    n = struct.unpack_from("<I", font, 0x28)[0] // 128
    for g in ENGLISH:
        if g >= n: continue
        cols = glyph_cols(font, g)
        if not cols: continue
        left[g] = min(cols)
        adv[g] = max(cols) - min(cols) + 1 + gap
        pad = PAD.get(g, 0)
        left[g] = max(0, left[g] - pad); adv[g] += 2 * pad
    # tabular groups: identical left shift and advance within each group so that
    # standalone glyphs positioned by the game (e.g. OPTION <1 2 3 4 5>) stay evenly spaced
    for grp in TABULAR:
        cs = [glyph_cols(font, g) for g in grp if g < n]
        lo = min(min(c) for c in cs if c); hi = max(max(c) for c in cs if c)
        for g in grp:
            left[g] = lo
            adv[g] = hi - lo + 1 + gap
    if BLANK_GLYPH < n:
        left[BLANK_GLYPH] = 0
        adv[BLANK_GLYPH] = space
    return bytes(left), bytes(adv)


def bl(src_ram, dst_ram):
    off = (dst_ram - (src_ram + 8)) >> 2
    return struct.pack("<I", 0xEB000000 | (off & 0xFFFFFF))


def extra_addr(arm9: bytes) -> int:
    """ITCM address where apply(extra=...) data will live."""
    al_start = struct.unpack_from("<I", arm9, MODPARAMS)[0]
    itcm_size = struct.unpack_from("<I", arm9, al_start - RAM_BASE + 4)[0]
    return ITCM_BASE + itcm_size + 0x40 + 2 * TABLE_N


# ---- dialogue typewriter (0x020297EC) compositing VWF -------------------------
# Original: one 16x16 sprite per glyph, advance 14, 40-sprite context -> 36 chars/page.
# Hook: glyph pixels are OR-ed into 16px-wide sprite "cells" in OBJ VRAM so several
# narrow glyphs share one sprite. Cells come from the game's own allocator (0x2029DC8)
# called with the blank glyph; its upload is suppressed by pre-setting the slot cache,
# the tile is cleared by CPU, and the cache entry is then marked dirty (0xFFFF).
DLG_DRAW_SITE = 0x298AC          # ldr r0,[r4,#4] .. str r0,[r4,#0x18]  (7 words)
DLG_DRAW_ORIG = (0xE5940004, 0xE5942018, 0xE594301C, 0xEB000142, 0xE5940018,
                 0xE280000E, 0xE5840018)
DLG_SPACE_SITE = 0x29890         # addeq r1, r1, #14   (code 0xFFFE = space)
DLG_WRAP_SITE = 0x298D4          # add r2, r2, #14      (auto-wrap look-ahead)
GLYPH_DRAW = 0x02029DC8
SLOT_CACHE_MAIN = 0x020561A8
FONT_PTR = 0x0205609C
OBJ_VRAM_MAIN = 0x06400000


def dialogue_asm(base, tbl_left, tbl_adv, gap):
    return f"""
    dlg:
        push {{r4-r11, lr}}
        mov r4, r0
        mov r5, r1
        ldr r11, [r4, #4]
        ldr r0, [r11, #0x10]
        cmp r0, #0
        bne fallback
        ldr r6, [r4, #0x18]
        ldr r7, [r4, #0x1c]
        cmp r5, #{TABLE_N}
        movhs r8, #0
        movhs r9, #14
        ldrlo r0, lit_left
        ldrblo r8, [r0, r5]
        ldrlo r0, lit_adv
        ldrblo r9, [r0, r5]
        add r0, r6, r9
        str r0, [r4, #0x18]
        sub r6, r6, r8
        sub r9, r9, #{gap}
        add r9, r9, r8
        cmp r9, #16
        movgt r9, #16
        adr r10, state
        ldr r0, [r11, #8]
        cmp r0, #0
        beq newcell
        ldr r0, [r10, #8]
        cmp r0, #0
        beq newcell
        ldr r0, [r10, #4]
        cmp r0, r7
        bne newcell
        ldr r0, [r10, #12]
        cmp r0, r11
        bne newcell
        ldr r0, [r10]
        add r0, r0, #16
        add r1, r6, r8
        cmp r1, r0
        blt havecell
    newcell:
        add r0, r6, r8
        bl alloc
        cmp r0, #0
        beq done
    havecell:
        ldr r0, lit_font
        ldr r0, [r0]
        ldr r0, [r0, #0x14]
        add r5, r0, r5, lsl #7
    colloop:
        cmp r8, r9
        bge done
        ldr r0, [r10]
        add r1, r6, r8
        sub r1, r1, r0
        cmp r1, #16
        blt rows
        add r0, r0, #16
        bl alloc
        cmp r0, #0
        beq done
        b colloop
    rows:
        mov r2, #0
    rowloop:
        mov r3, r2, lsr #3
        mov r3, r3, lsl #1
        add r3, r3, r8, lsr #3
        mov r3, r3, lsl #5
        and ip, r2, #7
        add r3, r3, ip, lsl #2
        and ip, r8, #7
        add r3, r3, ip, lsr #1
        ldrb r3, [r5, r3]
        tst r8, #1
        lsrne r3, r3, #4
        ands r3, r3, #15
        beq nextrow
        mov ip, r2, lsr #3
        mov ip, ip, lsl #1
        add ip, ip, r1, lsr #3
        mov ip, ip, lsl #5
        and lr, r2, #7
        add ip, ip, lr, lsl #2
        and lr, r1, #7
        add ip, ip, lr, lsr #1
        and lr, ip, #1
        mov lr, lr, lsl #3
        tst r1, #1
        addne lr, lr, #4
        mov r3, r3, lsl lr
        ldr lr, [r10, #8]
        bic ip, ip, #1
        add ip, ip, lr
        ldrh lr, [ip]
        orr lr, lr, r3
        strh lr, [ip]
    nextrow:
        add r2, r2, #1
        cmp r2, #16
        blt rowloop
        add r8, r8, #1
        b colloop
    done:
        pop {{r4-r11, pc}}
    fallback:
        ldr r2, [r4, #0x18]
        ldr r3, [r4, #0x1c]
        mov r0, r11
        ldr ip, lit_draw
        blx ip
        ldr r0, [r4, #0x18]
        add r0, r0, #14
        str r0, [r4, #0x18]
        pop {{r4-r11, pc}}

    alloc:
        push {{r0, lr}}
        ldr r1, [r11, #8]
        ldr r2, [r11, #4]
        cmp r1, r2
        bge allocfail
        ldr r3, [r11]
        add r3, r3, r1
        str r3, [r10, #16]
        ldr r1, lit_cache
        add r1, r1, r3, lsl #1
        ldr r2, lit_blank
        strh r2, [r1]
        mov r0, r11
        mov r1, r2
        ldr r2, [sp]
        mov r3, r7
        ldr ip, lit_draw
        blx ip
        pop {{r0, lr}}
        str r0, [r10]
        str r7, [r10, #4]
        str r11, [r10, #12]
        ldr r3, [r10, #16]
        ldr r1, lit_cache
        add r1, r1, r3, lsl #1
        mvn r2, #0
        strh r2, [r1]
        mov r0, #{OBJ_VRAM_MAIN}
        add r0, r0, r3, lsl #7
        str r0, [r10, #8]
        mov r1, #0
        mov r2, #128
    clr:
        subs r2, r2, #2
        strh r1, [r0, r2]
        bne clr
        bx lr
    allocfail:
        pop {{r0, lr}}
        mov r0, #0
        str r0, [r10, #8]
        bx lr

    lit_left: .word {tbl_left}
    lit_adv: .word {tbl_adv}
    lit_font: .word {FONT_PTR}
    lit_draw: .word {GLYPH_DRAW}
    lit_cache: .word {SLOT_CACHE_MAIN}
    lit_blank: .word {BLANK_GLYPH}
    state: .word 0, 0, 0, 0, 0
    """


def apply(arm9: bytes, font: bytes, gap=2, space=6, extra=b"", dialogue=False) -> bytes:
    d = bytearray(arm9)
    al_start, al_end, al_data = struct.unpack_from("<III", d, MODPARAMS)
    assert al_end - al_start == 24, "expected 2 autoload entries"
    lst = al_start - RAM_BASE
    itcm_dst, itcm_size, itcm_bss = struct.unpack_from("<III", d, lst)
    assert itcm_dst == ITCM_BASE and itcm_bss == 0
    itcm_file = al_data - RAM_BASE           # ITCM data starts here in the file
    insert_at = itcm_file + itcm_size         # end of ITCM data
    hook_base = ITCM_BASE + itcm_size

    # verify original instructions before patching
    for s in SITES_X:
        assert struct.unpack_from("<I", d, s)[0] == 0xE1A01007, hex(s)   # mov r1, r7
    for s in SITES_ADV + SITES_SPACE:
        assert struct.unpack_from("<I", d, s)[0] == 0xE287700E, hex(s)   # add r7, r7, #14

    left, adv = metrics(font, gap, space)
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_ARM)
    code_len_guess = 0x40
    tbl_left = hook_base + code_len_guess
    tbl_adv = tbl_left + TABLE_N
    src = f"""
    vwf_x:
        cmp r4, #{TABLE_N}
        movhs r1, r7
        bxhs lr
        ldr r1, lit_left
        ldrb r1, [r1, r4]
        sub r1, r7, r1
        bx lr
    vwf_adv:
        cmp r4, #{TABLE_N}
        addhs r7, r7, #14
        bxhs lr
        ldr r0, lit_adv
        ldrb r0, [r0, r4]
        add r7, r7, r0
        bx lr
    lit_left:
        .word {tbl_left}
    lit_adv:
        .word {tbl_adv}
    """
    enc, _ = ks.asm(src, hook_base)
    code = bytes(enc)
    assert len(code) <= code_len_guess, len(code)
    code += bytes(code_len_guess - len(code))
    vwf_adv_addr = hook_base + 7 * 4
    blob = code + left + adv + extra
    blob += bytes((-len(blob)) % 4)
    dlg_addr = None
    if dialogue:
        dlg_addr = hook_base + len(blob)
        enc, _ = ks.asm(dialogue_asm(dlg_addr, tbl_left, tbl_adv, gap), dlg_addr)
        blob += bytes(enc)
        blob += bytes((-len(blob)) % 4)

    d[insert_at:insert_at] = blob
    grow = len(blob)
    struct.pack_into("<I", d, lst + grow + 4, itcm_size + grow)
    struct.pack_into("<II", d, MODPARAMS, al_start + grow, al_end + grow)

    for s in SITES_X:
        d[s:s + 4] = bl(RAM_BASE + s, hook_base)
    for s in SITES_ADV:
        d[s:s + 4] = bl(RAM_BASE + s, vwf_adv_addr)
    for s in SITES_SPACE:
        struct.pack_into("<I", d, s, 0xE2877000 | space)
    if dialogue:
        assert struct.unpack_from("<7I", d, DLG_DRAW_SITE) == DLG_DRAW_ORIG
        assert struct.unpack_from("<I", d, DLG_SPACE_SITE)[0] == 0x0281100E
        assert struct.unpack_from("<I", d, DLG_WRAP_SITE)[0] == 0xE282200E
        s = DLG_DRAW_SITE
        struct.pack_into("<I", d, s, 0xE1A00004)                     # mov r0, r4
        d[s + 4:s + 8] = bl(RAM_BASE + s + 4, dlg_addr)               # bl dlg (r1 = glyph)
        for k in range(2, 7):
            struct.pack_into("<I", d, s + 4 * k, 0xE1A00000)         # nop
        struct.pack_into("<I", d, DLG_SPACE_SITE, 0x02811000 | space)
        struct.pack_into("<I", d, DLG_WRAP_SITE, 0xE2822000)          # wrap only when past box
    return bytes(d)


