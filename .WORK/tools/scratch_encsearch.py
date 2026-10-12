import os, sys
strs = ["メッセージスピード", "バックライト", "アリスお嬢さま", "ヒステュール", "電撃を撃って", "アリスの部屋", "おはよう"]
encs = ["shift_jis", "utf-16-le", "utf-8", "euc-jp"]
files = []
for r, _, fs in os.walk("extracted"):
    for f in fs:
        files.append(os.path.join(r, f))
data = {p: open(p, "rb").read() for p in files}
hits = 0
for s in strs:
    for e in encs:
        b = s.encode(e)
        for p, d in data.items():
            i = d.find(b)
            if i >= 0:
                hits += 1
                print(s, e, p, hex(i))
print("hits:", hits)
