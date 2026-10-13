"""_script_en.json / _script_jp.json loader. _script_en.json is the ONLY English text input of the build.
Multi-line fields are lists of exact in-game lines; {H}...{/H} = red keyword highlight."""
import json
from pathlib import Path
TR = Path(__file__).resolve().parents[1] / "tools-resources"
EN = json.load(open(TR / "_script_en.json", encoding="utf-8"))
JP = json.load(open(TR / "_script_jp.json", encoding="utf-8"))
join = lambda lines: "\n".join(lines) if isinstance(lines, list) else lines
MENU = {e["key"]: e["en"] for e in EN["menu"]}
OPTION_KEYS = [e["key"] for e in EN["menu"] if e["key"].startswith("option_")]
