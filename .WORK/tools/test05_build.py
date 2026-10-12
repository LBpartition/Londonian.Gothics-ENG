"""Test build 05: dress description wrapped by textfit (no manual line breaks).
TEST STRINGS ONLY - not translation text."""
import struct, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, vwf_patch, textfit
import test01_build as t1
from test03_build import put

W = Path(__file__).resolve().parent.parent


def main(out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rom = t1.ORIG.read_bytes()
    fid = ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]
    font = t1.build_font(ndsbuild.get_file(rom, fid))
    m = textfit.Metrics(font)
    box = textfit.DRESS_DESC

    # self-checks
    try:
        textfit.wrap("ABCDEFGHIJKLMNOPQRSTUVWXYZ ABCDEFGHIJKLMNOPQRSTUVWXYZ", box, m)
        raise SystemExit("FAIL: 3+ line text was accepted")
    except textfit.FitError as e:
        print("ok, overflow rejected:", e)

    text = "ABCDEFGHIJKLMNOP WI'M"
    lines = textfit.wrap(text, box, m)
    for ln in lines: print(f"  {m.width(ln, box):3d}px / {box.max_px}  {ln}")
    codes = textfit.fit(text, box, m)

    arm9 = bytearray((W / "extracted" / "arm9.bin").read_bytes())
    put(arm9, 0x4C438, 12, "TEXT SPEED")
    put(arm9, 0x4C450, 12, "BACKLIGHT")
    assert len(codes) < 24
    arm9[0x48290:0x48290 + 48] = struct.pack("<24H", *(codes + [0] * (24 - len(codes))))
    arm9 = vwf_patch.apply(bytes(arm9), font)
    out = ndsbuild.build(rom, {fid: font}, arm9=arm9, log=lambda *_: None)
    p = out_dir / "TEST05-descwrap.nds"
    p.write_bytes(out)
    print(p, hashlib.sha256(out).hexdigest().upper())


if __name__ == "__main__":
    main(sys.argv[1])
