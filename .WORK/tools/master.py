"""_import_script.json / .script_jpn.json loader. _import_script.json is the ONLY English text input of the build.
Multi-line fields are lists of exact in-game lines; {H}...{/H} = red keyword highlight."""
import json
from pathlib import Path
TR = Path(__file__).resolve().parents[1] / "tools-resources"
EN = json.load(open(TR / "_import_script.json", encoding="utf-8"))
JP = json.load(open(TR / ".script_jpn.json", encoding="utf-8")) if (TR / ".script_jpn.json").exists() else None
join = lambda lines: "\n".join(lines) if isinstance(lines, list) else lines
MENU = {e["key"]: e["en"] for e in EN["menu"]}
OPTION_KEYS = [e["key"] for e in EN["menu"] if e["key"].startswith("option_")]
DEBUG_KEYS = [e["key"] for e in EN["menu"] if e["key"].startswith("debug_")]
