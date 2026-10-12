"""Harvest review marks from ../mtl-draft.txt.
[Y] -> phase10/approved.tsv (file, idx, en); [N] -> phase10/rejected.tsv (for redraft).
A user-written line under an entry (not JP:/EN:) replaces the EN text when marked Y."""
import re
from pathlib import Path
W = Path(__file__).resolve().parent.parent
P = W / "phase10"
def load(p):
    return {tuple(l.split("\t")[:2]): l.rstrip("\n").split("\t", 2)[2] for l in open(p, encoding="utf-8")} if p.exists() else {}
appr, rej = load(P / "approved.tsv"), load(P / "rejected.tsv")
cur = None; blocks = []
for l in (W.parent / "mtl-draft.txt").read_text(encoding="utf-8-sig").split("\n"):
    m = re.match(r"^\[(.)\] (\S+) #(\d+)", l)
    if m: cur = [m.group(1).upper(), m.group(2), m.group(3), None, []]; blocks.append(cur); continue
    s = l.strip()
    if cur and s and not s.startswith(("---", "=")):
        if s.startswith("EN:"): cur[3] = s[3:].strip()
        elif not s.startswith(("JP:", "MT:", "(")): cur[4].append(s)
import sys
sys.path.insert(0, str(Path(__file__).parent))
import full_build as fb, textfit, ndsbuild, test06_build as t6
rom = (W / "rom/JPN-original.nds").read_bytes()
m = textfit.Metrics(ndsbuild.get_file(rom, ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]), t6.GAP, t6.SPACE)
bad = []
ny = nn = 0
for mk, f, i, en, own in blocks:
    k = (f, i)
    if mk == "Y":
        txt = own[0] if own else en
        try:
            textfit.fit(fb.norm(txt), fb.BOX, m)
        except Exception as ex:
            bad.append(f"{f} #{i}: {txt}  -> {ex}"); continue
        appr[k] = txt; rej.pop(k, None); ny += 1
    elif mk == "N": rej[k] = en; nn += 1
for name, d in (("approved.tsv", appr), ("rejected.tsv", rej)):
    (P / name).write_text("".join(f"{f}\t{i}\t{e}\n" for (f, i), e in sorted(d.items())), encoding="utf-8")
for b in bad: print("NOT APPROVED (does not fit / bad character):", b)
print("approved now", len(appr), "(+%d)" % ny, "rejected", len(rej))
