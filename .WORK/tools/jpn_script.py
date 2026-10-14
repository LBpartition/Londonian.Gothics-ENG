"""Write tools-resources/.script_jpn.json: the original Japanese text, in the same order as
_import_script.json. Reference only (the build doesn't read it). Generated from the extracted
ROM by extract_rom.py, so the Japanese script itself is not stored in the repository."""
import json, os, struct, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sp_tool

W = Path(__file__).resolve().parent.parent
TR = W / "tools-resources"
EX = W / "extracted"
OUT = TR / ".script_jpn.json"


def main():
    EN = json.loads((TR / "_import_script.json").read_text(encoding="utf-8"))
    g = sp_tool.load_glyphs()
    arm9 = (EX / "arm9.bin").read_bytes()

    ge = dict(g)
    with open(TR / "_import_glyph_table.tsv", encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) > 2 and p[2] and p[2] != "<space>":
                ge[int(p[0], 16)] = p[2]

    def tbl(off, n, g=g):
        u = list(struct.unpack_from(f"<{n}H", arm9, off))
        u = u[:u.index(0)] if 0 in u else u
        return "".join("\n" if v == 0xFFFF else g.get(v, "{%03X}" % v) for v in u)

    sp = {}
    for p in sp_tool.all_files():
        d = open(p, "rb").read()
        info = sp_tool.parse(d)
        idx = {o: i for i, (o, _) in enumerate(info["strings"])}
        name = os.path.basename(p)
        rec, done = {}, set()
        for order, (f, spk, t) in enumerate(info["ops"]):
            r = {"file": name, "idx": idx[t], "off": t, "order": order, "op_at": f, "speaker": spk,
                 "jp": sp_tool.decode(info["strings"][idx[t]][1], g)}
            if t in done:
                rec[(idx[t], f)] = dict(r, op=f)   # repeated use of the same string
                continue
            done.add(t)
            rec[idx[t]] = r
        sp[name] = (rec, "".join(g.get(v, "?") for v in sp_tool.get_name(d)))

    J = {}
    J["intro"] = [{"block": e["block"], "jp": "(pre-drawn image: data/title_roll_full_16.NCGR)"} for e in EN["intro"]]
    J["dialogue"] = [sp[e["file"]][0][(e["idx"], e["op"]) if "op" in e else e["idx"]] for e in EN["dialogue"]]
    J["locations"] = [{"file": e["file"], "jp": sp[e["file"]][1]} for e in EN["locations"]]
    J["dresses"] = [{"id": k + 1, "name": tbl(0x48000 + 14 * k, 7), "desc": tbl(0x48290 + 48 * k, 24)} for k in range(23)]
    J["items"] = [{"id": i + 1, "name": tbl(0x48144 + 10 * i, 5), "desc": tbl(0x486E0 + 0x2E * i, 23)} for i in range(34)]
    fixed = {"save_prompt": "DATA1 \u306b\u30bb\u30fc\u30d6\u3057\u307e\u3059 (image: data/mode_save.NCGR)",
             "load_prompt": "DATA1 \u3092\u30ed\u30fc\u30c9\u3057\u307e\u3059 (image: data/mode_save.NCGR)"}
    yn = {"yes": (0x1A, 0x02, 0, 0), "no": (0x02, 0x02, 0x04, 0), "end": (0x24, 0x22, 0x29, 0)}
    menu = []
    for e in EN["menu"]:
        k = e["key"]
        if k in fixed:
            t = fixed[k]
        elif k in yn:
            t = "".join(g[v] for v in yn[k] if v)
        elif k == "saved":
            t = tbl(0x4BF68, 8)
        elif k.startswith("option_"):
            t = tbl(0x4C3F0 + 24 * [x["key"] for x in EN["menu"] if x["key"].startswith("option_")]            .index(k), 12, ge)
        else:
                        t = tbl(0x4B6C8 + 24 * [x["key"] for x in EN["menu"] if x["key"].startswith("debug_")].index(k), 12, ge)
        menu.append({"key": k, "jp": t})
    J["menu"] = menu
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(J, ensure_ascii=False, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
