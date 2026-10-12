"""Parse a user-edited excerpt of the Full Script doc into phase10/layout_overrides.json.
Every entry whose text/line breaks differ from the current doc becomes an exact-layout override."""
import json, re, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
DOC = W.parent / "RELEASE" / "SCRIPT - FULL.txt"


def sections(txt):
    L = txt.split("\n"); out = {"INTRO": []}; cur = "INTRO"
    for k, l in enumerate(L):
        if l.startswith("=====") : continue
        if k + 1 < len(L) and L[k + 1].startswith("=====") and k and L[k - 1].startswith("====="):
            cur = l.split(" ")[0]; out[cur] = []; continue
        out.setdefault(cur, []).append(l.rstrip())
    return out


def entries(lines, head):   # list of (head, [body lines]) ; body lines are indented
    out, cur = [], None
    for l in lines:
        if head(l):
            cur = (l.strip(), []); out.append(cur)
        elif cur and l.startswith("    ") and l.strip() != "---":
            cur[1].append(l.strip())
        elif not l.strip():
            cur = None
    return out


def intro_blocks(lines):
    bl, cur = [], []
    for l in lines:
        if l.strip(): cur.append(l.strip())
        elif cur: bl.append(cur); cur = []
    if cur: bl.append(cur)
    return [b for b in bl if not b[0].startswith(("LONDONIAN", "Full Script", "Generated", "Line breaks", "*word*", "Dialogue is", "lines at", "a new"))]


def main(user_path):
    u, d = sections(Path(user_path).read_text(encoding="utf-8")), sections(DOC.read_text(encoding="utf-8"))
    ov_path = W / "phase10" / "layout_overrides.json"
    ov = json.loads(ov_path.read_text(encoding="utf-8")) if ov_path.exists() else {"intro": {}, "dress": {}, "item": {}, "dialogue": {}}
    n = 0
    ui, di = intro_blocks(u.get("INTRO", [])), intro_blocks(d["INTRO"])
    for k, (a, b) in enumerate(zip(ui, di)):
        if a != b: ov["intro"][str(k)] = "\n".join(a); n += 1
    num = lambda l: re.match(r"^\d\d\. ", l)
    for sec, key in (("DRESSES", "dress"), ("ITEMS", "item")):
        dd = dict(entries(d.get(sec, []), num))
        for h, body in entries(u.get(sec, []), num):
            if body and dd.get(h) != body: ov[key][h[4:]] = "\n".join(body); n += 1
    idx = (W / "phase10" / "doc_index.tsv").read_text(encoding="utf-8").split()
    idx = list(zip(idx[0::2], idx[1::2]))
    who = lambda l: l == "(narration)" or bool(re.match(r"^[A-Za-z?][\w ?]*:$", l))
    de, ue = entries(d["DIALOGUE"], who), entries(u.get("DIALOGUE", []), who)
    for k, ((uh, ub), (dh, db)) in enumerate(zip(ue, de)):
        assert uh == dh, (k, uh, dh, ub, db)
        if ub:   # user-reviewed entry: lock its exact layout
            ov["dialogue"]["|".join(idx[k])] = "\n".join(ub); n += 1
    ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")
    print(n, "overrides added; matched", min(len(ue), len(de)), "dialogue entries")
    for s in ov:
        for k, v in ov[s].items(): print(s, k, "|", v.replace("\n", " / "))


if __name__ == "__main__":
    main(sys.argv[1])
