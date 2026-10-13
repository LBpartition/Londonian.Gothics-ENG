"""Phase 1: ROM baseline - header, NitroFS manifest, extraction, round-trip test.

Reads the header/FNT/FAT directly from bytes (independent of any library),
then cross-checks against ndspy and tests ndspy's rebuild.
"""
import csv, hashlib, json, os, struct, sys, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "tools-resources" / ".ROM_JPN.nds"
OUT = ROOT / "out" / "Extracted-ROM-Report"
EXT = ROOT / "extracted"
EXPECTED_SHA = "3DC0FAF62B3922078532B587C6823A97CA9CE0A893F55CF17F94B3B3FCD861B6"

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]

def crc16_modbus(data):
    crc = 0xFFFF
    for x in data:
        crc ^= x
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def parse_header(rom):
    h = {
        "title": rom[0:12].rstrip(b"\0").decode("ascii"),
        "game_code": rom[12:16].decode("ascii"),
        "maker_code": rom[16:18].decode("ascii"),
        "unit_code": rom[0x12],
        "device_capacity": rom[0x14],
        "rom_version": rom[0x1E],
    }
    names = ["arm9_rom_offset", "arm9_entry", "arm9_ram", "arm9_size",
             "arm7_rom_offset", "arm7_entry", "arm7_ram", "arm7_size",
             "fnt_offset", "fnt_size", "fat_offset", "fat_size",
             "arm9_ovt_offset", "arm9_ovt_size", "arm7_ovt_offset", "arm7_ovt_size"]
    for i, n in enumerate(names):
        h[n] = u32(rom, 0x20 + i * 4)
    h["banner_offset"] = u32(rom, 0x68)
    h["total_used_rom_size"] = u32(rom, 0x80)
    h["header_size"] = u32(rom, 0x84)
    h["header_crc16_stored"] = u16(rom, 0x15E)
    h["header_crc16_calc"] = crc16_modbus(rom[0:0x15E])
    h["logo_crc16_stored"] = u16(rom, 0x15C)
    return h

def parse_fnt(rom, off):
    """Return {file_id: path} by walking the FNT directory tree."""
    fnt = rom[off:]
    ndirs = u16(fnt, 6)
    paths = {}
    def walk(dir_id, prefix):
        e = (dir_id & 0xFFF) * 8
        sub_off, first_id = u32(fnt, e), u16(fnt, e + 4)
        p, fid = sub_off, first_id
        while True:
            t = fnt[p]; p += 1
            if t == 0: break
            ln = t & 0x7F
            name = fnt[p:p + ln].decode("shift_jis"); p += ln
            if t & 0x80:
                sub = u16(fnt, p); p += 2
                walk(sub, prefix + name + "/")
            else:
                paths[fid] = prefix + name; fid += 1
    walk(0xF000, "")
    return paths, ndirs

def main():
    rom = ROM.read_bytes()
    assert sha(rom) == EXPECTED_SHA, "ROM hash mismatch!"
    OUT.mkdir(parents=True, exist_ok=True); EXT.mkdir(exist_ok=True)
    h = parse_header(rom)
    paths, ndirs = parse_fnt(rom, h["fnt_offset"])
    nfiles = h["fat_size"] // 8
    fat = [(u32(rom, h["fat_offset"] + i * 8), u32(rom, h["fat_offset"] + i * 8 + 4)) for i in range(nfiles)]

    # Overlays
    overlays = []
    for i in range(h["arm9_ovt_size"] // 32):
        o = h["arm9_ovt_offset"] + i * 32
        ov = dict(zip(["ovl_id", "ram", "ram_size", "bss_size", "sinit_start", "sinit_end", "file_id", "flags"],
                      struct.unpack_from("<8I", rom, o)))
        ov["compressed"] = bool(ov["flags"] & 0x01000000)
        overlays.append(ov)
    ovl_files = {ov["file_id"]: f"overlay/overlay9_{ov['ovl_id']:04d}.bin" for ov in overlays}

    # Sorted by start for gap computation
    order = sorted(range(nfiles), key=lambda i: fat[i][0])
    next_start = {}
    for a, b in zip(order, order[1:]):
        next_start[a] = fat[b][0]
    next_start[order[-1]] = None

    rows = []
    for fid in range(nfiles):
        s, e = fat[fid]
        data = rom[s:e]
        path = paths.get(fid) or ovl_files.get(fid) or f"_unnamed/file_{fid:04d}.bin"
        dest = EXT / "data" / path if fid in paths else EXT / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        ns = next_start[fid]
        rows.append({
            "file_id": fid, "path": path, "rom_start": f"0x{s:08X}", "rom_end": f"0x{e:08X}",
            "size": e - s, "gap_to_next": (ns - e) if ns is not None else "",
            "magic_hex": data[:4].hex().upper(),
            "magic_ascii": "".join(chr(c) if 32 <= c < 127 else "." for c in data[:4]),
            "sha256": sha(data),
        })

    # System parts
    sysparts = {
        "header.bin": rom[0:0x4000],
        "arm9.bin": rom[h["arm9_rom_offset"]:h["arm9_rom_offset"] + h["arm9_size"]],
        "arm7.bin": rom[h["arm7_rom_offset"]:h["arm7_rom_offset"] + h["arm7_size"]],
        "y9.bin": rom[h["arm9_ovt_offset"]:h["arm9_ovt_offset"] + h["arm9_ovt_size"]],
        "y7.bin": rom[h["arm7_ovt_offset"]:h["arm7_ovt_offset"] + h["arm7_ovt_size"]],
        "fnt.bin": rom[h["fnt_offset"]:h["fnt_offset"] + h["fnt_size"]],
        "fat.bin": rom[h["fat_offset"]:h["fat_offset"] + h["fat_size"]],
        "banner.bin": rom[h["banner_offset"]:h["banner_offset"] + 0x840],
    }
    # ARM9 often has a 12-byte nitrocode footer after arm9_size
    footer = rom[h["arm9_rom_offset"] + h["arm9_size"]:h["arm9_rom_offset"] + h["arm9_size"] + 12]
    sysparts["arm9_footer.bin"] = footer
    for n, d in sysparts.items():
        (EXT / n).write_bytes(d)

    # Free space at end of ROM
    used_end = max(e for _, e in fat)
    tail = rom[used_end:]
    tail_ff = len(tail) - len(tail.rstrip(b"\xFF"))

    with open(OUT / "JPN_Extracted_ROM_manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    # Magic summary
    from collections import Counter
    ext_count = Counter(Path(r["path"]).suffix.lower() for r in rows)
    magic_count = Counter(r["magic_ascii"] for r in rows)

    # Cross-check with ndspy + round-trip
    import ndspy.rom
    nr = ndspy.rom.NintendoDSRom(rom)
    xcheck = {
        "ndspy_file_count": len(nr.files),
        "ndspy_files_match_raw": all(nr.files[i] == rom[fat[i][0]:fat[i][1]] for i in range(nfiles)),
        "ndspy_arm9_match": nr.arm9 == sysparts["arm9.bin"],
        "ndspy_overlay_count": len(nr.arm9OverlayTable) // 32,
    }
    rebuilt = nr.save()
    rt = {
        "rebuilt_size": len(rebuilt),
        "rebuilt_sha256": sha(rebuilt),
        "byte_identical": rebuilt == rom,
    }
    if not rt["byte_identical"]:
        n = min(len(rom), len(rebuilt))
        diffs = [i for i in range(n) if rom[i] != rebuilt[i]]
        rt["diff_count_in_common_len"] = len(diffs)
        rt["first_diffs"] = [f"0x{d:08X}" for d in diffs[:20]]
        # Are all files still byte-identical after rebuild (just moved)?
        nr2 = ndspy.rom.NintendoDSRom(rebuilt)
        rt["all_files_identical_after_rebuild"] = all(nr2.files[i] == nr.files[i] for i in range(nfiles))
        rt["arm9_identical_after_rebuild"] = nr2.arm9 == nr.arm9

    report = {
        "rom_sha256": sha(rom), "rom_crc32": f"{zlib.crc32(rom):08X}", "rom_size": len(rom),
        "header": {k: (f"0x{v:X}" if isinstance(v, int) else v) for k, v in h.items()},
        "header_crc_ok": h["header_crc16_stored"] == h["header_crc16_calc"],
        "fnt_dir_count": ndirs, "fat_file_count": nfiles, "named_files": len(paths),
        "arm9_overlays": len(overlays), "overlays": overlays,
        "arm9_footer_hex": footer.hex().upper(),
        "data_end": f"0x{used_end:X}", "tail_bytes": len(tail), "tail_all_ff": tail_ff == len(tail),
        "extensions": dict(ext_count.most_common()), "magics": dict(magic_count.most_common(30)),
        "ndspy_crosscheck": xcheck, "roundtrip": rt,
    }
    (OUT / "JPN_Extracted_ROM_Report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in ("overlays",)}, indent=2, ensure_ascii=False))
    import jpn_script
    jpn_script.main()

if __name__ == "__main__":
    main()
