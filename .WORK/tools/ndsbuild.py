"""Layout-preserving NDS ROM builder.

- Unchanged files stay at their exact original offsets (byte-identical when no edits).
- A changed file is written in place if it fits before the next file's start
  (remainder padded with 0xFF); otherwise it is appended at the end of used data
  (0x200-aligned) and its FAT entry updated.
- Header total-used-size (0x80) and header CRC16 (0x15E) are recomputed.
- If data exceeds the current ROM capacity, the ROM is expanded (device capacity
  byte 0x14 bumped, padded with 0xFF), e.g. 64 MB -> 128 MB.
"""
import struct
from pathlib import Path

ALIGN = 0x200

def u32(b, o): return struct.unpack_from("<I", b, o)[0]

def crc16_modbus(data):
    crc = 0xFFFF
    for x in data:
        crc ^= x
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def read_fat(rom):
    off, size = u32(rom, 0x48), u32(rom, 0x4C)
    return [(u32(rom, off + i * 8), u32(rom, off + i * 8 + 4)) for i in range(size // 8)]

def get_file(rom, fid):
    s, e = read_fat(rom)[fid]
    return bytes(rom[s:e])

def file_ids_by_path(rom):
    """Map NitroFS path -> file id (parses FNT)."""
    fnt_off = u32(rom, 0x40)
    fnt = rom[fnt_off:]
    out = {}
    def walk(dir_id, prefix):
        e = (dir_id & 0xFFF) * 8
        p, fid = u32(fnt, e), struct.unpack_from("<H", fnt, e + 4)[0]
        while True:
            t = fnt[p]; p += 1
            if t == 0: break
            ln = t & 0x7F
            name = bytes(fnt[p:p + ln]).decode("shift_jis"); p += ln
            if t & 0x80:
                sub = struct.unpack_from("<H", fnt, p)[0]; p += 2
                walk(sub, prefix + name + "/")
            else:
                out[prefix + name] = fid; fid += 1
    walk(0xF000, "")
    return out

def build(orig: bytes, replacements: dict, force_relocate: set = frozenset(), log=print, arm9: bytes = None) -> bytes:
    rom = bytearray(orig)
    fat = read_fat(rom)
    fat_off = u32(rom, 0x48)
    starts = sorted(s for s, _ in fat)
    # Hard upper bound for in-place growth: next file start (or end of used data region)
    used_end = max(e for _, e in fat)
    def next_start_after(s):
        for x in starts:
            if x > s: return x
        return used_end  # last file: don't eat into tail implicitly
    # append after EVERYTHING in use (arm7 may already live past the last file)
    true_end = max(used_end, u32(rom, 0x30) + u32(rom, 0x3C),
                   u32(rom, 0x20) + u32(rom, 0x2C) + 12, u32(rom, 0x80))
    append_at = (true_end + ALIGN - 1) // ALIGN * ALIGN

    for fid, data in sorted(replacements.items()):
        s, e = fat[fid]
        limit = next_start_after(s)
        if fid not in force_relocate and s + len(data) <= limit:
            rom[s:limit] = data + b"\xFF" * (limit - s - len(data))
            fat[fid] = (s, s + len(data))
            log(f"file {fid}: in place @0x{s:X} size {e - s} -> {len(data)}")
        else:
            # blank the old location
            rom[s:e] = b"\xFF" * (e - s)
            ns = append_at
            ne = ns + len(data)
            if ne > len(rom):
                rom.extend(b"\xFF" * (ne - len(rom)))
            rom[ns:ne] = data
            fat[fid] = (ns, ne)
            append_at = (ne + ALIGN - 1) // ALIGN * ALIGN
            log(f"file {fid}: relocated 0x{s:X} -> 0x{ns:X} size {e - s} -> {len(data)}")

    extra_end = 0
    if arm9 is not None:
        a9_off, a9_size = u32(rom, 0x20), u32(rom, 0x2C)
        footer = bytes(rom[a9_off + a9_size:a9_off + a9_size + 12])
        assert footer[:4] == bytes.fromhex("2106C0DE"), "arm9 footer missing"
        a7_off, a7_size = u32(rom, 0x30), u32(rom, 0x3C)
        blob = arm9 + footer
        if a9_off + len(blob) > a7_off:
            arm7_data = bytes(rom[a7_off:a7_off + a7_size])
            rom[a7_off:a7_off + a7_size] = b"\xFF" * a7_size
            ns = append_at
            if ns + a7_size > len(rom):
                rom.extend(b"\xFF" * (ns + a7_size - len(rom)))
            rom[ns:ns + a7_size] = arm7_data
            struct.pack_into("<I", rom, 0x30, ns)
            append_at = (ns + a7_size + ALIGN - 1) // ALIGN * ALIGN
            extra_end = ns + a7_size
            log(f"arm7 relocated 0x{a7_off:X} -> 0x{ns:X}")
            limit = ns if ns > a9_off else len(rom)
        else:
            limit = a7_off
        assert a9_off + len(blob) <= limit
        old_end = a9_off + a9_size + 12
        rom[a9_off:a9_off + len(blob)] = blob
        if old_end > a9_off + len(blob):
            rom[a9_off + len(blob):old_end] = b"\xFF" * (old_end - a9_off - len(blob))
        struct.pack_into("<I", rom, 0x2C, len(arm9))
        log(f"arm9 size 0x{a9_size:X} -> 0x{len(arm9):X}")

    for i, (s, e) in enumerate(fat):
        struct.pack_into("<II", rom, fat_off + i * 8, s, e)

    new_used = max(max(e for _, e in fat), u32(orig, 0x80), extra_end)
    struct.pack_into("<I", rom, 0x80, new_used)
    reg = sorted([(s, e, f"file{i}") for i, (s, e) in enumerate(fat) if e > s] +
                 [(u32(rom, 0x20), u32(rom, 0x20) + u32(rom, 0x2C) + 12, "arm9"),
                  (u32(rom, 0x30), u32(rom, 0x30) + u32(rom, 0x3C), "arm7")])
    for x, y in zip(reg, reg[1:]):
        assert x[1] <= y[0], f"ROM region overlap: {x} / {y}"

    cap = rom[0x14]
    size = 0x20000 << cap
    while len(rom) > size:
        cap += 1; size = 0x20000 << cap
    if cap != rom[0x14]:
        log(f"ROM expanded: capacity byte 0x{rom[0x14]:X} -> 0x{cap:X} ({size // 2**20} MB)")
        rom[0x14] = cap
    if len(rom) < size:
        rom.extend(b"\xFF" * (size - len(rom)))

    struct.pack_into("<H", rom, 0x15E, crc16_modbus(rom[:0x15E]))
    return bytes(rom)

if __name__ == "__main__":
    import hashlib, sys
    src = Path(sys.argv[1]).read_bytes()
    out = build(src, {})
    print("no-op rebuild identical:", out == src, hashlib.sha256(out).hexdigest().upper())
