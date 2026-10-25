"""_import_script.json / .script_jpn.json loader. _import_script.json is the ONLY English text input of the build.
Multi-line fields are lists of exact in-game lines; {H}...{/H} = red keyword highlight."""
import json, os, re, sys
from pathlib import Path
TR = Path(__file__).resolve().parents[1] / "tools-resources"
# --nomtl (or LG_NOMTL=1): translator resource. Machine-translated entries are replaced by the original
# Japanese, using _import_script_nomtl.json and "EDIT and IMPORT - SCRIPT - No MTL.txt" instead.
if "--nomtl" in sys.argv:
    sys.argv.remove("--nomtl"); os.environ["LG_NOMTL"] = "1"
NOMTL = os.environ.get("LG_NOMTL") == "1"
SRC = TR / ("_import_script_nomtl.json" if NOMTL else "_import_script.json")
DOC = TR / ("EDIT and IMPORT - SCRIPT - No MTL.txt" if NOMTL else "EDIT and IMPORT - SCRIPT.txt")
has_jp = lambda s: bool(re.search(r"[\u3001-\u303f\u3040-\u30ff\u3400-\u9fff\uff01-\uff9f]", s if isinstance(s, str) else "".join(s or [])))
JP = json.load(open(TR / ".script_jpn.json", encoding="utf-8")) if (TR / ".script_jpn.json").exists() else None
if NOMTL and not SRC.exists():
    # first run: copy the main script, swapping every MTL entry for its Japanese original (source "jp")
    assert JP, "run jpn_script.py first (needs .script_jpn.json)"
    _E = json.load(open(TR / "_import_script.json", encoding="utf-8"))
    for e, j in zip(_E["dialogue"], JP["dialogue"]):
        if e["source"] == "mtl":
            # {WAIT} = next text box, {NL} = new line, {FE02}..{FE00} = red highlight
            pg = [p.replace("{FE02}", "{H}").replace("{FE00}", "{/H}").split("{NL}") for p in j["jp"].split("{WAIT}")]
            e["en"] = [l for k, p in enumerate(pg) for l in p + ([""] * (-len(p) % 3) if k < len(pg) - 1 else [])]
            e["source"] = "jp"
    for e, j in zip(_E["menu"], JP["menu"]):
        if e.get("source") == "mtl": e["en"], e["source"] = j["jp"], "jp"
    SRC.write_text(json.dumps(_E, ensure_ascii=False, indent=1), encoding="utf-8")
EN = json.load(open(SRC, encoding="utf-8"))
join = lambda lines: "\n".join(lines) if isinstance(lines, list) else lines
MENU = {e["key"]: e["en"] for e in EN["menu"]}
OPTION_KEYS = [e["key"] for e in EN["menu"] if e["key"].startswith("option_")]
DEBUG_KEYS = [e["key"] for e in EN["menu"] if e["key"].startswith("debug_")]
# arm9 system messages (popup boxes): key -> original string offsets in arm9.bin. The build stores
# the English in ITCM and repoints every literal that referenced these. {ITEM} = 0xFD00, the
# item/dress name the game inserts, {NUM} = 0xFC00 (number).
# sys_pattern_desc: DRESS MODE description of an uncrafted pattern (dress table entry 23, no pointer). Keys are listed in _import_script.json "menu" order.
SYSMSG = {"door_opened": [0x4BE34], "sys_no_money": [0x4B48C], "sys_buy": [0x4B4A0],
          "sys_shop_full": [0x4B4C8], "sys_read_error": [0x4B678, 0x4BFD8], "sys_discard": [0x4BA50, 0x4BEF8],
          "sys_make_dress": [0x4BA78, 0x4BAA8], "sys_no_materials": [0x4BA90], "sys_got_pattern": [0x4BAC0],
          "sys_dress_done": [0x4BADC], "sys_choose_pattern": [0x4BAF8], "sys_found_item": [0x4BB18],
          "sys_bag_full": [0x4BB68], "sys_which_floor": [0x4BE48], "sys_cant_change": [0x4BF0C],
          "sys_game_over": [0x48CE0], "sys_evil_aura": [0x48CF8],
          "sys_got_money": [0x4BA64], "sys_floor": [0x4B430], "sys_pattern_desc": [0x486B0]}
SYSMSG_LOC = {"door_opened": "sp003.sp"}   # shown in DIALOGUE after this file; others at the end
