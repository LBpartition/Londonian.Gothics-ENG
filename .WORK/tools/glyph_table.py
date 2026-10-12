"""Build tools-resources/glyph_table.tsv (original-glyph rows; CUSTOM rows are hand-edited) from transcription of the font sheet (0x000-0x246).

Every row was read from the rendered sheets in phase2/. Special glyphs use {TAGS}.
"""
from pathlib import Path

ROWS = {
    0x000: ["{ROSE}"] + list("あいうえおかきくけこさしすせそ"),
    0x010: list("たちつてとなにぬねのはひふへほま"),
    0x020: list("みむめもやゆよらりるれろわをんぁ"),
    0x030: list("ぃぅぇぉゃゅょっがぎぐげござじず"),
    0x040: list("ぜぞだぢづでどばびぶべぼぱぴぷぺ"),
    0x050: list("ぽアイウエオカキクケコサシスセソ"),
    0x060: list("タチツテトナニヌネノハヒフヘホマ"),
    0x070: list("ミムメモヤユヨラリルレロワヲンァ"),
    0x080: list("ィゥェォャュョッガギグゲゴザジズ"),
    0x090: list("ゼゾダヂヅデドバビブベボパピプペ"),
    0x0A0: list("ポー、。！？（）「」※；：．＾£"),
    0x0B0: list("＂＃％＆☆○◎□￣＿＜＞↑→↓←"),
    0x0C0: list("0123456789") + ["{I0}", "{I1}", "{I2}", "{I3}", "{I4}", "{I5}"],
    0x0D0: ["{I6}", "{I7}", "{I8}", "{I9}"] + list("ABCDEFGHIJKL"),
    0x0E0: list("MNOPQRSTUVWXYZ") + ["…", "私"],
    0x0F0: list("止行博士朝早大変父化物穴現助危険"),
    0x100: list("丈夫作魔法確速持事聞失礼気急言入"),
    0x110: list("手本当嬢目覚迷宮倒驚死残今出心配"),
    0x120: list("待雰囲壊地下左降次右上廊曲部屋陣"),
    0x130: list("形光場所先通扉深関係中念力絶対近"),
    0x140: list("更奥進不味丸体居良状態破周多環境"),
    0x150: list("浄人一時的完全可能間経復活前説明"),
    0x160: list("以邪聖書水剣金生糸針色黒革細切美"),
    0x170: list("沢玉天羽測軽柄厚底靴品型紙客室庭"),
    0x180: list("寝斎実験故婦階段食堂料庫洗面敷二"),
    0x190: list("空拝電撃攻放強敵反射砲飛着回浮使"),
    0x1A0: list("移動壁越高歩小乗度返少遅長身同姿"),
    0x1B0: list("透昇帰来凍無代必要") + ["{TRI_R}"] + list("玄執理ヴ況役"),
    0x1C0: list("立思適任決応分自信押情報見安解広"),
    0x1D0: list("用開閉仕方音守頭普考声悪知弱準備"),
    0x1E0: list("休素直研究調戻収相友好話伝楽機難"),
    0x1F0: list("内容日記読月敗果娘願亡悔終命外取"),
    0x200: list("遊毒愛才胞重組込兵器苦十過去示呼"),
    0x210: list("限悟儀式界然我幸神徒彼裏表存在世"),
    0x220: list("効逃遠距離溶岩増定複数障害忘異成"),
    0x230: list("画捨選材足量整買商由字") + ["{TRI_L}"] + list("差源／店"),
    0x240: list("売判断乱妻傷肩"),
}
# Low-confidence transcriptions to re-check in context
UNSURE = {0x1AF: "姿?", 0x16E: "切?", 0x1B4: "凍?"}

def build():
    table = {}
    for base, chars in ROWS.items():
        assert len(chars) <= 16, hex(base)
        for i, c in enumerate(chars):
            table[base + i] = c
    assert len(table) == 0x247, len(table)
    return table

if __name__ == "__main__":
    # rewrite the original-glyph rows (0x000-0x246); keep the en column and all CUSTOM rows as edited
    t = build()
    out = Path(__file__).resolve().parents[1] / "tools-resources" / "glyph_table.tsv"
    old = [l.rstrip("\n").split("\t") for l in open(out, encoding="utf-8")][1:]
    en = {int(r[0], 16): r[2] for r in old}
    custom = ["\t".join(r) for r in old if int(r[0], 16) >= len(t)]
    rows = ["id\tchar\ten\ttop\tpixels\tnote"] + [f"0x{k:03X}\t{t[k]}\t{en.get(k, '')}\t\t\t{UNSURE.get(k, '')}" for k in sorted(t)]
    out.write_text("\n".join(rows + custom) + "\n", encoding="utf-8")
    print(f"{len(t)} original + {len(custom)} custom glyphs -> {out}")
