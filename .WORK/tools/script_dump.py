"""Write tools-resources\\EDIT and IMPORT - SCRIPT.txt from tools-resources/_import_script.json (exact in-game lines)."""
import csv, glob, json, os, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, textfit, font_patch, intro_patch
import ui_patch as t6
import font_tools as t1
import master

W = Path(__file__).resolve().parents[1]
ROOT = W.parent
SPK = {3: "Nabokov", 4: "Vampire", 5: "Wizard", 6: "Fairy", 1: "?"}
spk = lambda s: "" if s is None else SPK.get(s) or {10: "Alice", 11: "Mikhail", 12: "Lucille"}.get(s // 10, "?")
HL = lambda s: s.replace("{H}", "{").replace("{/H}", "}")   # {red highlighted text}


def main():
    rc = master.SRC.name
    seq = master.EN["dialogue"]   # already in playthrough order
    locs = {e["file"]: e["en"] for e in master.EN["locations"]}
    rom = t1.ORIG.read_bytes()
    font = font_patch.patch_font(ndsbuild.get_file(rom, ndsbuild.file_ids_by_path(rom)["data/font.NCGR"]))
    m = textfit.Metrics(font, t6.GAP, t6.SPACE)
    W_ = lambda s, box: textfit.wrap(s, box, m)

    o = []
    hr = lambda t: o.extend(["", "=" * 60, t, "=" * 60, ""])
    o += ["LONDONIAN GOTHICS - LOLITA IN THE LABYRINTH",
          "Full Script + Descriptions (English patch)",
          f"Generated from: {rc}",
          "",
          "Line breaks are exactly as the game wraps them. Dialogue boxes show 3",
          "lines at a time; '---' marks where the game pages to the next box.",
          "{word} = shown in red in-game (keyword highlight). *word* = literal asterisks, as shown.",
          "Dialogue order is approximate: lines found in the GameFAQs guide follow the",
          "guide's playthrough order; lines not in the guide (machine translated) are",
          "placed by their position in the game's own script files, so optional, repeat",
          "and conditional dialogue may not appear exactly where it does in-game.",
          "A new --- Location --- header starts whenever the scene changes."]
    if master.NOMTL:
        o += ["", "NO MTL VERSION (translator resource): lines that were machine translated in the",
              "English patch are shown in their original Japanese. Replace them with English;",
              "everything else is ShadowRisae's translation. Import with: script_import.py --nomtl"]

    hr("TITLE SCREEN CREDITS")
    o += ["(<RC> = build number, <HUMAN> / <MTL> = % of entries by source; max 4 lines)", ""]
    o += [e["en"] for e in master.EN["credits"]]

    hr("INTRO (PROLOGUE STORY ROLL)")
    _, blocks = intro_patch.layout()
    for _, lines in blocks:
        o += lines + [""]

    hr("DRESSES (DRESS MODE)")
    g = None
    for k, n in enumerate(t6.ORDER, 1):
        o += [f"{k:02}. {n}"] + ["    " + l for l in W_(t6.dress_desc(n, g), textfit.DRESS_DESC_N)] + [""]

    hr("ITEMS")
    gi = None
    for i in range(34):
        nm = t6.item_name(i)
        ds = t6.item_desc(i, gi)
        if not nm: continue
        o += [f"{i+1:02}. {nm}"] + ["    " + l for l in (W_(ds, textfit.DRESS_DESC_N) if ds else ["(no description)"])] + [""]

    hr("LOCATION NAMES (top of map screen)")
    seen = []
    for f in sorted(locs, key=lambda f: (not f.startswith("sp_home"), f)):
        if locs[f] not in seen: seen.append(locs[f])
    o += seen

    hr("CHARACTER NAMES")
    chars = ["Alice", "Mikhail", "Lucille", "Nabokov", "Vampire", "Wizard", "Fairy"]
    o += chars

    hr("MENU TEXT (OPTION screen)")
    o += [master.MENU[k] for k in master.OPTION_KEYS]

    hr("MENU TEXT (SAVE / LOAD screens)")
    o += [master.MENU[k] for k in ("save_prompt", "load_prompt", "yes", "no", "end", "saved")]
    o += [master.MENU[k] for k in master.DEBUG_KEYS]

    hr("DIALOGUE")
    last = None
    sysmsg = {f: k for k, f in master.SYSMSG_LOC.items()}   # arm9 system messages, shown after this file's lines
    sub = {"g": [], "m": []}; sl = {"g": None, "m": None}   # per-source dialogue (GameFAQs / MTL)
    nondlg = o[:]
    for n, e in enumerate(seq):
        f, i, st = e["file"], e["idx"], e["source"]
        if f != last or e.get("scene"):
            sc = f" - {e['scene']}" if e.get("scene") else ""
            o += ["", f"--- {locs.get(f, '?')}  ({f}){sc} ---", ""]; last = f
        who = spk(e["speaker"])
        if not e["en"]:
            o += [f"{who}: (untranslated)", ""]; continue
        body = []
        for k, l in enumerate(HL(x) for x in e["en"]):
            if k and k % 3 == 0: body.append("---")
            if l.strip(): body.append(l)   # blank = page padding (forced ---)
        blk = [f"{who}:" if who else "(narration)"] + ["    " + l for l in body] + [""]
        o += blk
        s = "m" if st == "mtl" else "g"
        if sl[s] != f:
            sub[s] += ["", f"--- {locs.get(f, '?')}  ({f}) ---", ""]; sl[s] = f
        sub[s] += blk
        if f in sysmsg and (n + 1 == len(seq) or seq[n + 1]["file"] != f):
            o += ["(system message)"] + ["    " + l for l in master.MENU[sysmsg.pop(f)].split("\n")] + [""]
    o += ["", "--- SYSTEM MESSAGES (pop-up boxes, any location; {ITEM} = item/dress name, {NUM} = number) ---", ""]
    for k in master.SYSMSG:
        if k not in master.SYSMSG_LOC:
            o += ["(system message)"] + ["    " + l for l in master.MENU[k].split("\n")] + [""]
    out = master.DOC
    out.write_text("\n".join(o) + "\n", encoding="utf-8")
    print(out, len(seq), "dialogue lines")
    import add_patch_credits; print("shares %.1f%% / %.1f%%" % add_patch_credits.shares())

if __name__ == "__main__":
    main()
