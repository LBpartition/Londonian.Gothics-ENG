"""TEST07: TEST06 build + one dialogue line (sp_home005 'Good morning, Mikhail...')
replaced with guide English via sp_tool, to probe the dialogue renderer."""
import sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, sp_tool, textfit
import test06_build as t6

W = Path(__file__).resolve().parent.parent
BOX = textfit.Box("dialogue", 166, 99, 0xFFFE)  # box x44 w170 (RAM 0x21BD56C), 3 lines/page auto
LINE = ("sp_home005.sp", 36, "Good morning, Mikhail.  What brings you here so bright and early?")


def encode(text, m):
    out = []
    for ch in text.upper():
        out.append(m.code(ch) if hasattr(m, "code") else textfit.encode_char(ch))
    return out


def main(out_dir):
    out_dir = Path(out_dir)
    tmp = out_dir / "_t06"
    import io, contextlib
    t6.DIALOGUE_VWF = True
    with contextlib.redirect_stdout(io.StringIO()):
        t6.main(tmp)
    rom = (tmp / "TEST06-NarrowFont-DressMode.nds").read_bytes()
    ids = ndsbuild.file_ids_by_path(rom)
    fid = ids["data/font.NCGR"]
    m = textfit.Metrics(ndsbuild.get_file(rom, fid), t6.GAP, t6.SPACE)
    fname, idx, text = LINE
    sid = ids["data/" + fname]
    d = ndsbuild.get_file(rom, sid)
    info = sp_tool.parse(d)
    new = [s for _, s in info["strings"]]
    new[idx] = textfit.fit(" ".join(text.split()), BOX, m)
    out = ndsbuild.build(rom, {sid: sp_tool.rebuild(d, info, new)}, log=lambda *_: None)
    p = out_dir / "TEST07-DialogueProbe.nds"
    p.write_bytes(out)
    for f in tmp.iterdir(): f.unlink()
    tmp.rmdir()
    print(p, hashlib.sha256(out).hexdigest().upper())


if __name__ == "__main__":
    main(sys.argv[1])
