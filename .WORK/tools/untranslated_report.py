"""Write still-Japanese report (legacy; see Missing-translations-from-guide.txt): everything the current build leaves in Japanese."""
import csv, json, struct, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import sp_tool

W = Path(__file__).resolve().parent.parent
report, out = Path(sys.argv[1]), Path(sys.argv[2])
g = sp_tool.load_glyphs()
jp = {(r["file"], r["idx"]): r for r in json.load(open(W / "phase6/jp_master.json", encoding="utf-8"))}
rows = [r for r in csv.DictReader(open(report, encoding="utf-8"), delimiter="\t") if r["status"].startswith("jp")]
by = collections.defaultdict(list)
for r in rows:
    by[r["status"][3:]].append(r)

arm9 = (W / "extracted" / "arm9.bin").read_bytes()


def dec(units):
    return sp_tool.decode(units, g)


L = ["LONDONIAN GOTHICS - UNTRANSLATED CONTENT", "=" * 40,
     f"Source build report: {report}",
     f"Script lines left in Japanese: {len(rows)} (all have no English text in ShadowRisae's guide,",
     "unless noted). English is never invented; each needs a user decision:",
     "  (a) leave Japanese  (b) user-supplied translation  (c) user-approved wording", ""]
L += ["SUMMARY BY REASON", "-" * 17]
for k, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
    L.append(f"{len(v):4}  {k}")
L.append("")

L += ["ITEMS (not in guide)", "-" * 20]
if arm9:
    for i in (30, 31, 32, 33):
        o = 0x48144 + 10 * i
        n = list(struct.unpack("<5H", arm9[o:o + 10])); n = n[:n.index(0)] if 0 in n else n
        o = 0x486E0 + 0x2E * i
        d = list(struct.unpack("<23H", arm9[o:o + 0x2E])); d = d[:d.index(0)] if 0 in d else d
        tag = "name translated as 'Holy Water'; description still JP" if i == 32 else "name + description JP"
        if not n and not d: continue   # empty unused slot
        if i in (30, 31, 32): continue  # translated, user-approved
        L.append(f"  item {i+1}: {dec(n)}  /  {dec(d)}   [{tag}]")
    if L[-1].startswith("-"): L.append("  (none - all items translated)")
L += ["", "OTHER KNOWN GAPS", "-" * 16,
      "  Speaker name boxes: not audited.",
      "  Other UI graphics/menus: not fully audited; report any JP seen on screen.", ""]

L += ["ALL UNTRANSLATED SCRIPT LINES (file / line index / reason / Japanese)", "-" * 68]
for r in sorted(rows, key=lambda r: (r["file"], int(r["idx"]))):
    j = jp.get((r["file"], int(r["idx"])), {}).get("jp", "?")
    L.append(f"{r['file']}  #{r['idx']:>3}  [{r['status'][3:]}]")
    L.append(f"    {j}")
out.write_text("\n".join(L) + "\n", encoding="utf-8-sig")
print(len(rows), "lines ->", out)
