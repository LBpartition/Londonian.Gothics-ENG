"""Write mtl-draft.txt: v2 localisation draft (+ FuguMT raw MT for comparison if present)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import full_build as fb, textfit, ndsbuild, test06_build as t6

W = Path(__file__).resolve().parent.parent
P = W / "phase10"; TR = W / "tools-resources"
rom = (W / "rom/JPN-original.nds").read_bytes(); ids = ndsbuild.file_ids_by_path(rom)
m = textfit.Metrics(ndsbuild.get_file(rom, ids["data/font.NCGR"]), t6.GAP, t6.SPACE)
SPK = {3: "Nabokov", 4: "Vampire", 5: "Wizard", 6: "Fairy", None: "(narration/voice)"}
spk = lambda s: SPK.get(s) or {10: "Alice", 11: "Mikhail", 12: "Lucille"}.get(s // 10, str(s))
src = [l.rstrip("\n").split("\t") for l in open(P / "mt_src.tsv", encoding="utf-8")]
rd = lambda p: dict(l.rstrip("\n").split("\t", 1) for l in open(p, encoding="utf-8-sig") if "\t" in l)
mt = rd(P / "mt_draft.tsv")
fg = rd(P / "fugumt.tsv") if (P / "fugumt.tsv").exists() else {}
ld = lambda p: {tuple(l.split("\t")[:2]) for l in open(p, encoding="utf-8")} if p.exists() else set()
appr, rej = ld(TR / "approved.tsv"), ld(TR / "rejected.tsv")
src = [r for r in src if (r[1], r[2]) not in appr]

H = lambda t: ["", "=" * 78, t, "=" * 78]
L = ["LONDONIAN GOTHICS - MACHINE TRANSLATION DRAFT",
     "",
     "These lines had no English in ShadowRisae's GameFAQs translation guide.",
     "The English below is a machine-assisted translation using the guide's terms",
     "(miasma, bordermoon, genomroid, Varuudanu, holy sword, milady, Miss, Father).",
     "Each line is listed with its original Japanese so you can check or replace it.",
     "Line IDs (e.g. sp022.sp #0) match Missing-translations-from-guide.txt.",
     "",
     "  [ ]  review box: mark Y (approve) or N (reject), or write your own line below",
     "  fit  checked against the dialogue box using the game's real font",
     "  (redraft) = you rejected the previous wording; this is a new attempt",
     "  Approved lines are removed from this file and are already in the ROM.",
     "",
     f"  Lines left to review ........................... {len(src)}",
     f"  Lines already approved ......................... {len(appr)}"]
L += H("MACHINE TRANSLATION DRAFT (grouped by script file)")
cur = None
for n, f, i, s, j in src:
    s = None if s == "None" else int(s)
    if f != cur:
        L += ["", f"--- {f} ---"]; cur = f
    try:
        textfit.fit(fb.norm(mt[n]), fb.BOX, m); fit = "ok"
    except Exception as e:
        fit = "PROBLEM: " + str(e)[:60]
    L += [f"[ ] {f} #{i}   {spk(s)}   fit:{fit}" + ("   (redraft)" if (f, i) in rej else ""), f"      JP: {j}", f"      EN: {mt[n]}"]
    if n in fg:
        L.append(f"      MT: {fg[n]}")
(W.parent / "mtl-draft.txt").write_text("\n".join(L) + "\n", encoding="utf-8-sig")
print(sum("PROBLEM" in x for x in L), "fit problems;", len(fg), "MT lines")
