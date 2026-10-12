"""Test build 03: VWF in the UI renderers. Usage: test03_build.py <out_dir> [gap] [space]"""
import struct, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, vwf_patch
import test01_build as t1

W = Path(__file__).resolve().parent.parent


def enc_ui(s):
    return [0xFFFE if ch == " " else u for ch, u in zip(s, t1.enc(s))]


def put(arm9, off, slot, s):
    u = enc_ui(s)
    assert len(u) < slot, (s, len(u), slot)
    u += [0] * (slot - len(u))
    arm9[off:off + slot * 2] = struct.pack(f"<{slot}H", *u)


def main(out_dir, gap=2, space=6):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rom = t1.ORIG.read_bytes()
    fid = ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]
    font = t1.build_font(ndsbuild.get_file(rom, fid))
    arm9 = bytearray((W / "extracted" / "arm9.bin").read_bytes())
    put(arm9, 0x4C438, 12, "TEXT SPEED")
    put(arm9, 0x4C450, 12, "BACKLIGHT")
    put(arm9, 0x48000, 7, "WILLIM")
    put(arm9, 0x48290, 24, "ABCDEFGHIJKLMNOP\nWI'M 1")
    arm9 = vwf_patch.apply(bytes(arm9), font, gap=gap, space=space)
    out = ndsbuild.build(rom, {fid: font}, arm9=arm9)
    p = out_dir / f"TEST03-vwf-gap{gap}-space{space}.nds"
    p.write_bytes(out)
    print(p, hashlib.sha256(out).hexdigest().upper())


if __name__ == "__main__":
    main(sys.argv[1], *(int(x) for x in sys.argv[2:]))


