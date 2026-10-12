import sys,struct,collections; sys.path.insert(0,'tools')
from pathlib import Path
from glyph_table import build
T=build()
c=collections.Counter(); ex={}
for p in Path('extracted/data/data').glob('*.sp'):
    d=p.read_bytes(); u=[struct.unpack_from('<H',d,i)[0] for i in range(0,len(d)-1,2)]
    for i in range(2,len(u)-2):
        x=u[i]
        if x in T or x in (0,0xFFFF): continue
        # surrounded by kana/kanji glyphs on both sides
        if 0<u[i-1]<0x247 and 0<u[i+1]<0x247 and 0<u[i-2]<0x247 and 0<u[i+2]<0x247:
            c[x]+=1; ex.setdefault(x,(p.name,i*2,''.join(T.get(v,'?') for v in u[i-4:i+5])))
sys.stdout.reconfigure(encoding='utf-8')
for k,v in c.most_common(25): print(hex(k),v,ex[k])
