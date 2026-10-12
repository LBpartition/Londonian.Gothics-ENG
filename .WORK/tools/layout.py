"""Line-layout rules shared by the build and the script doc.
- phase10/layout_overrides.json: exact user layouts ("\n" = forced line break).
- auto_break(): start each new sentence on a new line when that adds no extra 3-line box."""
import json, math, re
from pathlib import Path
import textfit
W = Path(__file__).resolve().parents[1]
_p = W / "phase10" / "layout_overrides.json"
OV = json.loads(_p.read_text(encoding="utf-8")) if _p.exists() else {"intro": {}, "dress": {}, "item": {}, "dialogue": {}}
SENT = re.compile(r'(?<=[.!?])(?<!\bMr\.)(?<!\bMrs\.)(?<!\bDr\.)(?<!\bSt\.) (?=["\'(*]?[A-Z])')


def auto_break(text, box, m, per_page=3):
    pages = lambda t: math.ceil(len(textfit.wrap(t, box, m)) / per_page)
    base = pages(text)
    for mt in reversed(list(SENT.finditer(text))):
        head = text[:mt.start()].split("\n")[-1]
        if len(head.split()) <= 2:   # keep very short openers ("Huh?", "Understood.") inline
            continue
        cand = text[:mt.start()] + "\n" + text[mt.end():]
        if pages(cand) <= base:
            text = cand
    return text
