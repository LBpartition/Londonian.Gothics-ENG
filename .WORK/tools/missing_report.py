"""Write Missing-translations-from-guide.txt (full history, sectioned)."""
import csv, json, collections
from pathlib import Path

W = Path(__file__).resolve().parent.parent
R = W.parent
OLD = R / ".WORK/phase10/fit_report_pre_diary.tsv"   # last build before diary/items fixes
NEW = sorted((R / "OUTPUTS").glob("*/fit_report.tsv"))[-1]
jp = {(r['file'], r['idx']): r['jp'] for r in json.load(open(W / 'phase6/jp_master.json', encoding='utf-8'))}


def rd(p):
    return {(r['file'], int(r['idx'])): r for r in csv.DictReader(open(p, encoding='utf-8'), delimiter='\t')
            if r['idx'].isdigit()}


old, new = rd(OLD), rd(NEW)
rows = sorted(k for k, r in old.items() if r['status'].startswith('jp'))
done = [k for k in rows if not new[k]['status'].startswith('jp')]
still = [k for k in rows if new[k]['status'].startswith('jp')]
mtl = [k for k in rows if new[k]['status'] == 'mtl']
APPR = {(l.split('\t')[0], int(l.split('\t')[1])): l.rstrip('\n').split('\t', 2)[2]
        for l in open(W / 'phase10/approved.tsv', encoding='utf-8')}

H = lambda t: ["", "=" * 78, t, "=" * 78]
L = ["LONDONIAN GOTHICS - TRANSLATIONS MISSING FROM THE GUIDE",
     "",
     "Most English text in this patch comes from ShadowRisae's GameFAQs translation guide.",
     "The lines below had no English in the guide, so the patch uses its own translation",
     "for them. They are listed here so you can check or replace them with your own.",
     "",
     f"  Section 1  Patch-written translations ............. 6",
     f"  Section 2  Machine-assisted translations .......... {len(mtl)}",
     f"  Section 3  Still in Japanese ...................... {len(still)}"]

L += H("SECTION 1 - PATCH-WRITTEN TRANSLATIONS (not from the guide)")
L += ["  Location sp132   異界  ->  Another World",
      "  OPTION menu      SE    ->  SFX",
      "  Item 31  ベルゲン / 剣の形をしたアクセサリー",
      "           ->  Bergen / A sword-shaped accessory.",
      "  Item 32  聖書 / 博士を助けるために必要なアイテム、その1",
      "           ->  Bible / One of the items necessary for rescuing the professor. (guide 1758)",
      "  Item 33  聖水 / 博士を助けるために必要なアイテム、その2",
      "           ->  Holy Water / One of the items necessary for rescuing the professor. (guide 1758)",
      "  Item 34  (empty unused slot - nothing to translate)"]

L += H("SECTION 2 - MACHINE-ASSISTED TRANSLATIONS (no English in the guide)")
L += ["  Machine-assisted translation (using the guide's terms), reviewed before inclusion."]
for k in mtl:
    L += ["", f"  {k[0]} #{k[1]}", f"    JP: {jp[k]}", f"    EN: {APPR[k]}"]

L += H("SECTION 3 - STILL IN JAPANESE (no English in the guide)")
grp = collections.defaultdict(list)
for k in still:
    grp[new[k]['status'][3:]].append(k)
for reason, ks in sorted(grp.items(), key=lambda kv: -len(kv[1])):
    L += ["", f"--- {reason} ({len(ks)}) ---"]
    for k in ks:
        L += [f"  {k[0]} #{k[1]}:  {jp[k]}"]
(R / "Missing-translations-from-guide.txt").write_text("\n".join(L) + "\n", encoding="utf-8-sig")
print(len(done), len(still))
