"""Red keyword highlight (FE02 ... FE00): wrap the English term wherever the JP line highlights it."""
import json, re
from pathlib import Path
W = Path(__file__).resolve().parents[1]

TERMS = {  # JP highlighted term -> English regex (guide terms)
    "ゲノムロイド": r"genomroid",
    "ヴァルゥーダヌ": r"Varuudanu",
    "聖水": r"holy water",
    "聖書": r"holy book|bible",
    "聖剣": r"holy sword|sacred sword",
    "ボアダムン": r"bordermoons?",
    "ゴアダリス": r"gordalis",
    "アストゥーラ": r"Astulla",
    "アーガス": r"Argus",
    "トインカビア": r"Toinkabia",
    "エピネフル": r"Epinephle",
    "サーベイ": r"Survey",
    "ライテンス": r"Litense",
    "アクバル": r"akubaru",
    "テューヌ": r"tyuunu",
    "フォモル": r"fomoru",
    "オレウス": r"oreusu",
}
JPM = {(r["file"], r["idx"]): r["jp"] for r in json.load(open(W / "tools-resources/jp_master.json", encoding="utf-8"))}


def highlight(en, jp):
    for t in re.findall(r"\{FE02\}(.*?)\{FE00\}", jp):
        rx = TERMS.get(t)
        if not rx: continue
        m = re.compile(r"(?<!\{H\})\b(?:" + rx + r")\b", re.I).search(en)
        if not m: continue
        en = en[:m.start()] + "{H}" + m.group(0) + "{/H}" + en[m.end():]
    return en
